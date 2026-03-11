# 存放与大模型交互的接口

import time

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