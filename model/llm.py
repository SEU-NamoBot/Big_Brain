# 存放与大模型交互的接口

import time
import re

from openai import OpenAI
from config import TASK_LLM_API_KEY, TASK_LLM_BASE_URL, TASK_LLM_MODEL
from config import JUDGE_LLM_API_KEY, JUDGE_LLM_BASE_URL, JUDGE_LLM_MODEL
from config import VLM_API_KEY, VLM_API_BASE_URL, VLM_MODEL
from config import MAX_REPLAN_TIMES
from utils.utils import extract_code,call_LLM

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

    def generate_code(self, prompt:str,rag_context:str)->str:
        print("planning……")
        # 询问LLM
        try:
            raw_text = call_LLM(prompt)
            print("finish planning")
            print(f"Last Line to Delete from answer: {rag_context.strip().splitlines()[-1]}")
            return extract_code(raw_text,rag_context.strip().splitlines()[-1])
        except Exception as e:
            print(f"Planner LLM 调用失败：{e}")
            return ""

