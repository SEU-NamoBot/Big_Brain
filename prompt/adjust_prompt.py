# 视觉模型的prompt，用于判断任务是否成功以及如何微调

ADJUST_PROMPT = """

"""

import numpy as np


# pick up object apple
# 失败
# YOLO检测苹果位置
# 利用深度图和机器人本身计算苹果坐标2->3（未来可以写一个转换的函数直接提供调用）
# 重新夹起来

# move to
# 失败（比如读取机器人真实位置）
# 判断失败原因
# 修正move to 位置