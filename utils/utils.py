# 辅助判断位置的工具函数
import re

import numpy as np
from openai import OpenAI

from prompt.position_prompt import POSITION_PROMPT
from prompt.object_prompt import OBJECT_PROMPT
from config import TASK_LLM_API_KEY, TASK_LLM_BASE_URL, TASK_LLM_MODEL

def get_obj_xy(obejct:str):
    # 获取物体的坐标
    return (1.0, 2.0)

def get_obj_size(object:str):
    # 获取物体的长宽高
    # -1表示未知
    return (0.5, 0.5, 0.5)

def get_obj_rgb(object:str)->str:
    # 获取物体的RGB颜色
    color = "red"
    print(f"{object}: {color}")
    return color

def get_robot_pos():
    # 获取机器人的坐标
    return (0.0, 0.0)   

def get_robot_orientation():
    # 获取机器人的朝向
    return 0.0

def get_robot_arm()->bool:
    # 获取机器臂状态，是否夹持着物品？
    return True

def parse_obj_name(text:str,objects:dict)->list:
    # 从文本中解析出物体名称
    # 构建prompt
    base_prompt = OBJECT_PROMPT
    # 构建objects的字符串表示
    objects_str = "objects = {\n"
    for category, obj_list in objects.items():
        objects_str += f'    "{category}": {obj_list},\n'
    objects_str += "}\n"
    # 补充问题
    final_prompt = base_prompt + "\n" + objects_str + f"# {text}\n?"
    # print(final_prompt)
    print(f"# {text}?")

    # 调用大模型
    raw_text = call_LLM(final_prompt)

    code = extract_code(raw_text,text)
    # print(code)
    # 将传入的 objects 注入到 exec 的命名空间中，
    # 让生成的代码可以使用 "objects" 并写出 ret_val
    local_env = {"objects": objects}
    exec(code, {}, local_env)
    # ret_val 是在 exec 的代码中定义的
    return local_env["ret_val"]

def call_LLM(prompt:str):
    client = OpenAI(
            api_key=TASK_LLM_API_KEY,
            base_url=TASK_LLM_BASE_URL,
        )
    model_name = TASK_LLM_MODEL
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            # system有些模型需要有些模型不需要，具体看temperature为0，top_p为None时具体的输出
            {"role": "system", "content": "you only need to use code to answer the ? part"},
            {"role": "user", "content": prompt}
        ],
        temperature=0.0,
        top_p = None,
    )
    raw_text = response.choices[0].message.content
    return raw_text

def extract_code(text: str, last_line: str) -> str:
    # ai可能直接输出结果，也可能输出```python```代码块
    print("原始输出检查")
    print("====================================")
    print(text)
    print("====================================")
    pattern = r"```python(.*?)```"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    if last_line:
        if last_line in text:
            text = text.split(last_line, 1)[-1] # 保留last_line之后的部分
    # 也有可能直接丢出了指令
    return text.strip() # 如果没有代码块标记，直接返回原始文本

def load_L2_memory()->dict:
    # 用来读取l2层,暂时硬编码，未来完善为读取
    objects = {
        "desk": ['desk'],
        "chair": ['chair'],
        "bottle" : ['bottle1', 'bottle2', 'bottle3'],
        "fruits" : ['apple', 'banana', 'lemon']
    }
    return objects

def call_VLM(prompt:str):
    # 调用视觉模型进行判断
    print("Calling VLM for verification...")

def parse_obj_position(text:str):
    # 从文本中解析出物体位置
    client = OpenAI(
            api_key=TASK_LLM_API_KEY,
            base_url=TASK_LLM_BASE_URL,
        )
    return (1.0, 2.0)

if __name__ == "__main__":
    objects = {
        "desk": ["desk1", "desk2"],
        "chair" : ["chair1"],
        "bottle" : ['bottle1','bottle2'],
        "fruits" : ['apple', 'banana']
    }
    print(parse_obj_name("red desk",objects))
    # code = parse_obj_name("the bottle that is closest to the chair",objects)
    # print(parse_obj_name("the bottle that is between the fruits",objects))