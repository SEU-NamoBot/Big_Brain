# 辅助判断位置的工具函数

def get_obj_xy(obejct:str):
    # 获取物体的坐标
    return (1.0, 2.0)

def get_obj_size(object:str):
    # 获取物体的长宽高
    # -1表示未知
    return (0.5, 0.5, 0.5)

def parse_obj_name(text:str):
    # 从文本中解析出物体名称
    return text.strip()

def parse_obj_position(text:str):
    # 从文本中解析出物体位置
    return (1.0, 2.0)