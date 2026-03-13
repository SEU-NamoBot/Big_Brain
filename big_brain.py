# 大脑主流程
import json

import numpy as np

from action.robot_api import *
from model.rag import RAGManager
from model.llm import PlannerLLM
from prompt.task_prompt import BASE_PROMPT
from config import HISTORY_PATH
from utils.utils import get_obj_xy, get_obj_size, call_LLM, load_L2_memory,parse_obj_name

class BigBrain:
    def __init__(self):
        self.history_data = self._load_history(HISTORY_PATH)
        self.rag_manager = RAGManager(self.history_data)
        self.planner = PlannerLLM()

    def _load_history(self, path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _save_history(self, path):
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.history_data, f, ensure_ascii=False, indent=4)

    def run(self):
        # 大脑主流程
        # 输入任务
        # user_instruction = input("请输入任务指令: ")
        instruction = "pick up the bottle from the desk first and then put it between the apple and banana"
        # RAG调用
        rag_context = self.rag_manager.retrieve(instruction)
        
        # 组装prompt
        final_prompt = BASE_PROMPT + "\n"
        if rag_context:
            print("找到相似历史任务，作为参考：")
            print(rag_context)
            final_prompt += rag_context + "\n"        
        # 追加当前任务,使用？号引导LLM生成任务
        final_prompt += f"# {instruction}\n?"
        # print(final_prompt)
        print(f"{instruction}\n?")
        # LLM规划任务
        generated_code = self.planner.generate_code(final_prompt,rag_context)
        if generated_code.strip() == "":
            print("LLM未能生成有效的计划。")
            return False
        
        print("========== 生成的执行计划 ==========")
        print(generated_code)
        print("====================================")
        
        # 执行计划
        try:
            # exec 需要知道当前的全局和局部变量
            objects = load_L2_memory()
            # 把 objects 本身注入到全局作用域，方便在生成的代码中直接使用
            globals()["objects"] = objects
            globals()["instruction"] = instruction
            globals().update(objects)
            globals().update(instruction)
            exec(generated_code, globals())
            print("任务执行成功！")
            
            # 保存任务
            task_id = len(self.history_data) + 1
            new_record = {
                "id": task_id,
                "command": instruction,
                "task_queue": generated_code.splitlines()
            }
            self.history_data.append(new_record)
            # self._save_history(HISTORY_PATH)
            return True
        except Exception as e:
            print(f"执行过程中发生异常: {e}")
            return False


if __name__ == "__main__":
    brain = BigBrain()
    brain.run()