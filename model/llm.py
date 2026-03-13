# 存放与大模型交互的接口

import time
import base64
import re
import json

from openai import OpenAI
import numpy as np

from config import VLM_API_KEY,VLM_API_BASE_URL,VLM_MODEL
from config import MAX_REPLAN_TIMES,MOVE_ERROR_THRESHOLD,PLACE_ERROR_THRESHOLD,CATCH_ERROR_THRESHOLD
from utils.utils import get_obj_xy,get_obj_size
from utils.utils import get_robot_pos,get_robot_orientation,get_robot_arm
from utils.utils import extract_code,call_LLM,encode_image
from prompt.vlm_prompt import VLM_SYSTEM_PROMPT
from prompt.adjust_prompt import ADJUST_PROMPT

class PlannerLLM:
    # 负责根据用户指令生成计划
    def __init__(self):
        pass

    def generate_code(self, prompt:str,rag_context:str)->str:
        print("planning……")
        # 询问LLM
        try:
            raw_text = call_LLM(prompt)
            print("finish planning")
            last_line = ""
            rag_lines = rag_context.strip().splitlines() if rag_context else []
            if rag_lines:
                last_line = rag_lines[-1]
                print(f"Last Line to Delete from answer: {last_line}")
            return extract_code(raw_text,last_line)
        except Exception as e:
            print(f"Planner LLM 调用失败：{e}")
            return ""

class JudgeLLM:
    # 负责判断任务是否完成，并决定是否要进行重规划
    def __init__(self):
        self.max_replan_times = MAX_REPLAN_TIMES
        self.replan_retry_counter = {}
        self.vlm_client = OpenAI(
            api_key=VLM_API_KEY,
            base_url=VLM_API_BASE_URL,
        )


    def judge(self, task:str = None, action_id: int = None, task_desc: str = None, **kwargs):
        # 使用结构化动作(action_id + params)
        # 解析动作信息
        action_info = self._parse_atomic_task(task=task, action_id=action_id, task_desc=task_desc, params=kwargs)
        print(f"Judging task completion for task: {task_desc}")
        time.sleep(0.2)

        # 收集传感器信息
        observation = self._collect_observation()

        print(action_info)
        # 初步规则判断
        rule_result = self._rule_judge(action_info, observation)
        print(rule_result)

        # VLM判断
        vlm_result = {"pass": True, "reason": "VLM skipped"}
        # 1，2失败判断; 3，4需要检测是否夹对 ; 5,6需要检测放的位置是否符合语义(instruction 如between关系)
        if not rule_result["pass"] or action_id in [3,4,5,6]:
            raw_result = self.judge_VLM(action_info,observation,rule_result)
            vlm_result = self.extract_VLM_answer(raw_result)

        # 均通过
        result = rule_result["pass"] and vlm_result["pass"]
        if result:
            print("Judge result: PASS")
            return True

        # 判断失败，需要呼唤LLM进行微调
        failure_reason = vlm_result["reason"]
        print(f"Judge result: FAIL ({failure_reason})")
        print("Task not completed. Initiating local replanning...")
        return self.replan(action_info,vlm_result)

    def _parse_atomic_task(self, task: str = None, action_id: int = None, task_desc: str = None, params: dict = None) -> dict:
        # 结构化解析
        if action_id is not None:
            info = self._parse_by_action_id(action_id, params or {})
            info["raw"] = task_desc
            return info
        else:
            raise ValueError("No action_id provided for structured task parsing")

    def _parse_by_action_id(self, action_id: int, params: dict) -> dict:
        if action_id == 1:
            return {
                "action": "move_to_xy",
                "action_id": action_id,
                "target": (float(params["x"]), float(params["y"])),
                "params": params,
            }

        if action_id == 2:
            return {
                "action": "move_to_obj_by_offset",
                "action_id": action_id,
                "target": params["target"],
                "offset": (float(params["dx"]), float(params["dy"])),
                "params": params,
            }

        if action_id == 3:
            return {
                "action": "pick_up_xy",
                "action_id": action_id,
                "target": (float(params["x"]), float(params["y"])),
                "params": params,
            }

        if action_id == 4:
            return {
                "action": "pick_up_obj",
                "action_id": action_id,
                "target": params["target"],
                "params": params,
            }

        if action_id == 5:
            return {
                "action": "put_down_xy",
                "action_id": action_id,
                "target": (float(params["x"]), float(params["y"])),
                "params": params,
            }

        if action_id == 6:
            return {
                "action": "put_down_obj_by_offset",
                "action_id": action_id,
                "target": params["target"],
                "offset": (float(params["dx"]), float(params["dy"])),
                "params": params,
            }

        return {
            "action": "unknown",
            "action_id": action_id,
            "params": params,
        }

    def _collect_observation(self) -> dict:
        # 传感器
        robot_x,robot_y = get_robot_pos()
        robot_orientation = get_robot_orientation()
        holding = get_robot_arm()
        obs = {
            "robot_x": robot_x,
            "robot_y": robot_y,
            "robot_orientation": robot_orientation,
            "holding": holding,
        }
        print(f"Observation: {obs}")
        return obs

    def _rule_judge(self, action_info: dict, observation: dict) -> dict:
        action_id = action_info["action_id"]

        if action_id == 1:
            passed = abs(action_info["target"][0] - observation["robot_x"] ) <= MOVE_ERROR_THRESHOLD and abs(action_info["target"][1] - observation["robot_y"]) <= MOVE_ERROR_THRESHOLD
            return {
                "pass": passed, 
                "failure_code": "localization_error" if not passed else ""
            } 
        elif action_id == 2:
            # move_to_obj_by_offset 获取obj xy，获取obj size， 机器人坐标要在目标中心加上半边长宽+offset+误差范围内才ok
            obj_x,obj_y = get_obj_xy(action_info["target"])
            obj_length,obj_width,obj_height = get_obj_size(action_info["target"])
            target_x = obj_x + action_info["offset"][0]
            target_y = obj_y + action_info["offset"][1]
            passed = abs(target_x - observation["robot_x"] ) <= MOVE_ERROR_THRESHOLD + 1/2*obj_length and abs(target_y - observation["robot_y"]) <= MOVE_ERROR_THRESHOLD + 1/2*obj_width
            return {
                "pass":passed,
                "failure_code": "localization_error" if not passed else "",
            }
        elif action_id == 3:
            # pick_up_xy
            holding = observation["holding"]
            placed = abs(action_info["target"][0] - observation["robot_x"] ) <= CATCH_ERROR_THRESHOLD and abs(action_info["target"][1] - observation["robot_y"]) <= CATCH_ERROR_THRESHOLD
            failure_code = ""
            if not placed:
                failure_code = "localization_error"
            elif not holding:
                failure_code = "grasp_failure"    
            return {
                "pass": passed and placed,
                "failure_code": failure_code,
            }
        elif action_id == 4:
            # pick_up_obj
            # holding 并且小车和obj原来的位置在误差范围内
            holding = observation["holding"]
            obj_x,obj_y = get_obj_xy(action_info["target"])
            placed = abs(obj_x - observation["robot_x"] ) <= CATCH_ERROR_THRESHOLD and abs(obj_y - observation["robot_y"]) <= CATCH_ERROR_THRESHOLD
            failure_code = ""
            if not placed:
                failure_code = "localization_error"
            elif not holding:
                failure_code = "grasp_failure"
            return {
                "pass": holding and placed,
                "failure_code": failure_code,
            }
        elif action_id == 5:
            # put_down_xy 机器人不在目标位置，或者还拿着东西都算失败
            holding = observation["holding"]
            placed = abs(action_info["target"][0] - observation["robot_x"] ) <= PLACE_ERROR_THRESHOLD and abs(action_info["target"][1] - observation["robot_y"]) <= PLACE_ERROR_THRESHOLD
            failure_code = ""
            if not placed:
                failure_code = "localization_error"
            elif holding:
                failure_code = "placement_error"
            return {
                "pass": not holding and placed,
                "failure_code": failure_code,
            }
        elif action_id == 6:
            # put_down_obj_by_offset 机器人不在目标位置，或者还拿着东西都算失败
            holding = observation["holding"]
            obj_x,obj_y = get_obj_xy(action_info["target"])
            target_x = obj_x + action_info["offset"][0]
            target_y = obj_y + action_info["offset"][1]
            placed = abs(target_x - observation["robot_x"] ) <= CATCH_ERROR_THRESHOLD and abs(target_y - observation["robot_y"]) <= CATCH_ERROR_THRESHOLD
            failure_code = ""
            if not placed:
                failure_code = "localization_error"
            elif holding:
                failure_code = "placement_error"
            return {
                "pass": not holding and placed,
                "failure_code": failure_code,
            }

        # 未知动作
        print("UNKNOWN ACTION!")
        return {"pass": True, "failure_code": ""}

    def judge_VLM(self, action_info: dict, observation: dict, rule_result: dict) -> dict:
        # 构建VLM的prompt，调用VLM进行判断
        # 获取全局用户指令
        from runtime_context import CTX
        global_instruction = CTX.get("instruction")
        if not global_instruction:
            print("can not gain the user instruction")
            time.sleep(10)
        current_action = action_info["raw"]
        user_text = f"""
        User Input:
        Global Instruction: "{global_instruction}"
        Current Action: {current_action}
        Observation: {observation}
        Rule Check Result: {rule_result}
        """
        image_path = "image/image.png" 
        try:
            base64_image = encode_image(image_path)
        except Exception as e:
            print(f"[Warning] Failed to read image: {e}. Proceeding without visual (Hallucination risk high).")
            base64_image = ""

        # 拼装多模态 Message
        messages =[
            {"role": "system", "content": VLM_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_text},
                ]
            }
        ]
        
        # 如果图片读取成功，加入图片体
        if base64_image:
            messages[1]["content"].append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
            })
        print("send messages to VLM to judge……")
        try:
            response = self.vlm_client.chat.completions.create(
                model=VLM_MODEL,
                messages=messages,
                temperature=0.1, # 保持低温度以输出稳定 JSON
                top_p=0.9
            )
            raw_text = response.choices[0].message.content
            return raw_text
        except Exception as e:
            print(f"[JudgeLLM] VLM API Call Failed: {e}")
            return '{"pass": false, "error_type": "vlm_api_error", "reason": "API call failed", "suggested_correction": "Retry previous action."}'

    def extract_VLM_answer(self,raw_result:dict) -> dict:
        print("\n[JudgeLLM] --- Raw VLM Output ---")
        print(raw_result)
        print("---------------------------------\n")
        try:
            # 使用正则提取 JSON 代码块中的内容
            json_pattern = re.search(r'\{.*\}', raw_result, re.DOTALL)
            if json_pattern:
                json_str = json_pattern.group(0)
                return json.loads(json_str)
            else:
                # 尝试直接解析
                return json.loads(raw_result)
        except json.JSONDecodeError as e:
            print(f"[JudgeLLM] Failed to parse VLM JSON: {e}")
            # 严重解析错误时的兜底保护
            return {
                "pass": False, 
                "error_type": "json_parse_error", 
                "reason": f"Failed to parse VLM output. Raw text: {raw_result[:50]}...",
                "suggested_correction": "Re-evaluate the action."
            }
 
    def replan(self,action_info,vlm_result):
        print("开始微调")
        action_desc = action_info.get("raw", "unknown action")
        from runtime_context import CTX
        global_instruction = CTX.get("instruction")
        # 记录重规划次数，防止死循环
        if action_desc not in self.replan_retry_counter:
            self.replan_retry_counter[action_desc] = 0
            
        if self.replan_retry_counter[action_desc] >= self.max_replan_times:
            print(f"[AdjustLLM] Max replan times ({self.max_replan_times}) reached for action: {action_desc}. Task Failed.")
            return False

        self.replan_retry_counter[action_desc] += 1
        print(f"\n[AdjustLLM] Initiating Replanning... (Attempt {self.replan_retry_counter[action_desc]}/{self.max_replan_times})")

        # 将 VLM 的核心输出压缩为单行字符串
        import json
        vlm_feedback_str = json.dumps({
            "error_type": vlm_result.get("error_type", "unknown"),
            "suggested_correction": vlm_result.get("suggested_correction", "Retry the action.")
        }, ensure_ascii=False)

        # 按照纯 CAP 风格拼接最终的 Prompt
        from prompt.adjust_prompt import ADJUST_PROMPT
        final_prompt = ADJUST_PROMPT + "\n"
        final_prompt += f"# Global Instruction: \"{global_instruction}\"\n"
        final_prompt += f"# Failed Action: {action_desc}\n"
        final_prompt += f"# VLM Feedback: {vlm_feedback_str}\n"
        final_prompt += "?"

        print(f"[AdjustLLM] Calling Task LLM to generate recovery code...")
        
        # 调用基础的 call_LLM
        from utils.utils import call_LLM, extract_code, load_L2_memory
        raw_text = call_LLM(final_prompt)
        
        # 提取真正的代码
        adjust_code = extract_code(raw_text, "?")
        print("========== AdjustLLM 生成的微调/恢复代码 ==========")
        print(adjust_code)
        print("===================================================")
        
        if not adjust_code.strip():
            print("[AdjustLLM] 生成的代码为空，无法微调。")
            return False
            
        # 动态执行这段代码
        try:
            # 引入全局变量和依赖
            objects = load_L2_memory()
            local_env = {
                "objects": objects,
                "instruction": global_instruction,
            }
            exec_globals = globals().copy()
            exec_globals.update(local_env)
            
            # 使用 exec 执行新生成的原语
            # 注意：新执行的原语里面又会调用 robot_api 的方法，从而再次触发 judge_llm.judge()
            # 这里有递归，未来可以考虑是否采取微调不重执行来拒绝重调用
            # exec(adjust_code, exec_globals)
            
            print(f"[AdjustLLM] 微调动作执行完毕。")
            return True
            
        except Exception as e:
            print(f"[AdjustLLM] 微调代码执行时发生异常: {e}")
            return False
    
if __name__ == "__main__":
    # instruction = "pick up the bottle from the desk first and then put it between the apple and banana"
    instruction = "put the coke can on the desk"
    from runtime_context import CTX
    CTX["instruction"] = instruction
    CTX["step_idx"] = 0
    from action.robot_api import put_down_obj_by_offset
    put_down_obj_by_offset("desk",0,0)


