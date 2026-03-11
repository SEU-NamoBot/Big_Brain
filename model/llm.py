# 存放与大模型交互的接口

import time
import re

from openai import OpenAI
from big_brain.config import TASK_LLM_API_KEY, TASK_LLM_BASE_URL, TASK_LLM_MODEL
from big_brain.config import JUDGE_LLM_API_KEY, JUDGE_LLM_BASE_URL, JUDGE_LLM_MODEL
from big_brain.config import VLM_API_KEY, VLM_API_BASE_URL, VLM_MODEL

class JudgeLLM:
    # 负责判断任务是否完成，并决定是否要进行重规划
    def __init__(self):
        pass

    def judge(self, task:str):
        # 根据任务·位置信息与当前图片判断是否完成任务，如果没有完成，则调用replanning
        print(f"Judging task completion for task: {task}")
        time.sleep(1)  # 模拟判断过程的时间
        result = True
        if not result:
            print("Task not completed. Initiating replanning...")
            self.replan(task)

    
    def replan(self, task:str):
        print(f"Replanning task: {task}")
        # 导入子任务，先执行该部分。重规划过多直接判fail
        time.sleep(1)
        return True

class PlannerLLM:
    # 负责根据用户指令生成计划
    def __init__(self):
        self.client = OpenAI(
            api_key=TASK_LLM_API_KEY,
            base_url=TASK_LLM_BASE_URL,
        )
        self.model_name = TASK_LLM_MODEL

    def generate_code(self, prompt:str)->str:
        print("planning……")
        # raw_text = "```python\nmove_to_obj_by_offset('Bottle', 0, 0)\npick_up_obj('Bottle')\nmove_to_obj_by_offset('Rubbish_Can', 0, 0)\nput_down_obj_by_offset('Rubbish_Can', 0, 0)\n```"
        # return self._extract_python_code(raw_text)
        # 询问LLM
        try:
            # 开始调用 API
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0
            )
            raw_text = response.choices[0].message.content
            print("finish planning")
            return self._extract_python_code(raw_text)
        except Exception as e:
            print(f"Planner LLM 调用失败：{e}")
            return ""

    def _extract_python_code(self, text: str) -> str:
        # ai可能直接输出结果，也可能输出```python```代码块
        pattern = r"```python(.*?)```"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()
        return text.strip() # 如果没有代码块标记，直接返回原始文本