# 存放与大模型交互的接口

import time
import re

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
        pass

    def generate_code(self, prompt:str)->str:
        print("planning……")
        # 询问LLM
        time.sleep(1)  # 模拟规划过程的时间
        
        # LLM返回，mock结果
        raw_text = "```python\nmove_to_obj_by_offset('Bottle', 0, 0)\npick_up_obj('Bottle')\nmove_to_obj_by_offset('Rubbish_Can', 0, 0)\nput_down_obj_by_offset('Rubbish_Can', 0, 0)\n```"

        return self._extract_python_code(raw_text)

    def _extract_python_code(self, text: str) -> str:
        # ai可能直接输出结果，也可能输出```python```代码块
        pattern = r"```python(.*?)```"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()
        return text.strip() # 如果没有代码块标记，直接返回原始文本