# 存放与大模型交互的接口

import time
import re

from config import MAX_REPLAN_TIMES,MOVE_ERROR_THRESHOLD,PLACE_ERROR_THRESHOLD,CATCH_ERROR_THRESHOLD
from utils.utils import get_obj_xy,get_obj_size
from utils.utils import get_robot_pos,get_robot_orientation,get_robot_arm
from utils.utils import extract_code,call_LLM,call_VLM
from prompt.vlm_prompt import VLM_PROMPT
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

    def judge(self, task:str = None, action_id: int = None, task_desc: str = None, **kwargs):
        # 使用结构化动作(action_id + params)
        # 解析动作信息
        action_info = self._parse_atomic_task(task=task, action_id=action_id, task_desc=task_desc, params=kwargs)
        print(f"Judging task completion for task: {task_desc}")
        time.sleep(0.2)

        # 收集传感器信息
        observation = self._collect_observation()

        # 初步规则判断
        rule_result = self._rule_judge(action_info, observation)

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
        return self.replan(action_info, observation, vlm_result)

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
            "relation_ok": True,
        }
        print(f"Observation: {obs}")
        return obs

    def _rule_judge(self, action_info: dict, observation: dict) -> dict:
        action = action_info["action"]
        action_id = action_info["action_id"]

        if action_id == 1:
            passed = abs(action["target"][0] - observation["robot_x"] ) <= MOVE_ERROR_THRESHOLD and abs(action["target"][1] - observation["robot_y"]) <= MOVE_ERROR_THRESHOLD
            return {
                "pass": passed, 
                "failure_code": "localization_error" if not passed else ""
            } 
        elif action_id == 2:
            # move_to_obj_by_offset 获取obj xy，获取obj size， 机器人坐标要在目标中心加上半边长宽+offset+误差范围内才ok
            obj_x,obj_y = get_obj_xy(action_info["target"])
            obj_length,obj_width,obj_height = get_obj_size(action_info["target"])
            target_x = obj_x + action["offset"][0]
            target_y = obj_y + action["offset"][1]
            passed = abs(target_x - observation["robot_x"] ) <= MOVE_ERROR_THRESHOLD + 1/2*obj_length and abs(target_y - observation["robot_y"]) <= MOVE_ERROR_THRESHOLD + 1/2*obj_width
            return {
                "pass":passed,
                "failure_code": "localization_error" if not passed else "",
            }
        elif action_id == 3:
            # pick_up_xy
            holding = observation["holding"]
            placed = abs(action["target"][0] - observation["robot_x"] ) <= CATCH_ERROR_THRESHOLD and abs(action["target"][1] - observation["robot_y"]) <= CATCH_ERROR_THRESHOLD
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
            placed = abs(action["target"][0] - observation["robot_x"] ) <= PLACE_ERROR_THRESHOLD and abs(action["target"][1] - observation["robot_y"]) <= PLACE_ERROR_THRESHOLD
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
        action_id = action_info["action_id"]
        #

        # print(prompt)
        # return call_VLM(prompt)

    def extract_VLM_answer(self, raw_result:dict) -> dict:
        # 暂时留空，等待后面接入优化
        print("[VLM] model=mock")
        time.sleep(0.4)
        return {
            "pass": True,
            "reason": "mock vlm pass",
            "confidence": 0.9,
        }

    def replan(self, action_info: dict, observation: dict, vlm_result: dict):
        failure_reason = vlm_result["reason"]
        

        task = action_info.get("raw", self._action_info_to_text(action_info))
        print(f"Replanning task: {task}")
        task_key = f"{action_info.get('action_id', 0)}::{task}"
        retry_times = self.replan_retry_counter.get(task_key, 0)
        if retry_times >= self.max_replan_times:
            print(f"Replan aborted: retry limit reached ({self.max_replan_times})")
            return False

        self.replan_retry_counter[task_key] = retry_times + 1
        print(f"Local replan attempt {self.replan_retry_counter[task_key]}/{self.max_replan_times}")

        # 约束：仅做局部微调，不重写整段任务
        replan_code = self._build_replan_code(task, failure_reason)
        print("Replan code (exec):")
        print(replan_code)

        exec_env = {"task": task, "failure_code": failure_code, "time": time}
        try:
            exec(replan_code, {}, exec_env)
            return bool(exec_env.get("replan_success", False))
        except Exception as e:
            print(f"Replan exec error: {e}")
            return False
    
if __name__ == "__main__":
    instruction = "pick up the bottle from the desk first and then put it between the apple and banana"