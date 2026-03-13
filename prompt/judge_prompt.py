# 视觉模型的prompt，用于判断任务是否成功以及如何微调

feedback_prompt = """

"""

import numpy as np


# pick up object apple
# 失败
# YOLO检测苹果位置
# 计算苹果坐标2->3
# 重新夹起来

# move to
# 失败
# 判断失败原因
# 修正move to 位置