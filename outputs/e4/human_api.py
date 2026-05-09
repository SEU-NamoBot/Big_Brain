"""
## Navigation

- `N1` 导航到(100,200)
- `N2` 导航到垃圾桶旁边
- `N3` 绕垃圾桶做长50，宽50的方形运动
- `N4` 前往坐标绝对值之和最小的垃圾桶旁边，以50为半径绕行一圈，随后返回出发位置

## Manipulation

- `G1` 夹起红色方块
- `G2` 夹起位于地面的红色方块
- `G3` 把物体放到桌子上
- `G4` 把物体放到蓝色方块和黄色方块中间

## Composite

- `C1` 把沙发上的水杯放到椅子上
- `C2` 把红色方块从桌子上拿起，放到蓝色方块和黄色方块中间
- `C3` 把地上所有的垃圾丢到垃圾桶中
- `C4` 以长度为100的方形方式绕着桌子运动，当有红色方块出现时，夹起他，放到垃圾桶中
"""

import numpy as np
from action.robot_api import *
from utils.utils import *

objects = load_L2_memory()

# N1 导航到(100,200)
move_to_xy(100, 200)

# N2 导航到垃圾桶旁边
trash_can_obj = parse_obj_name('trash can',objects)
# return objects[trash_can]
move_to_obj_by_offset(trash_can_obj, 0, 0)

# N3 绕垃圾桶做长50，宽50的方形运动
trash_can_obj = parse_obj_name('trash can',objects)
trash_can_x, trash_can_y = get_obj_xy(trash_can_obj)
move_to_xy(trash_can_x + 25, trash_can_y + 25)
move_to_xy(trash_can_x + 25, trash_can_y - 25)
move_to_xy(trash_can_x - 25, trash_can_y - 25)
move_to_xy(trash_can_x - 25, trash_can_y + 25)
move_to_xy(trash_can_x + 25, trash_can_y + 25)


# N4 前往坐标绝对值之和最小的垃圾桶旁边，以50为半径绕行一圈，随后返回出发位置
original_x, original_y = get_robot_pos()
trash_can_obj = parse_obj_name('the trash can with the smallest sum of absolute coordinates',objects)

trash_can_x, trash_can_y = get_obj_xy(trash_can_obj)
# 将圆分为8个点进行绕行
for angle in np.linspace(0, 2 * np.pi, 8, endpoint=False):
    offset_x = 50 * np.cos(angle)
    offset_y = 50 * np.sin(angle)
    move_to_xy(trash_can_x + offset_x, trash_can_y + offset_y)
# 返回出发位置
move_to_xy(original_x, original_y)

# G1 夹起红色方块
red_block_obj = parse_obj_name('red block',objects)
pick_up_obj(red_block_obj)

# G2 夹起位于地面的红色方块
red_block_obj = parse_obj_name('red block on the ground',objects)
pick_up_obj(red_block_obj)

# G3 把物体放到桌子上
table_obj = parse_obj_name('table',objects)
put_down_obj_by_offset(table_obj, 0, 0)

# G4 把物体放到蓝色方块和黄色方块中间
blue_block_obj = parse_obj_name('blue block',objects)
yellow_block_obj = parse_obj_name('yellow block',objects)
blue_block_x, blue_block_y = get_obj_xy(blue_block_obj)
yellow_block_x, yellow_block_y = get_obj_xy(yellow_block_obj)
mid_x = (blue_block_x + yellow_block_x) / 2
mid_y = (blue_block_y + yellow_block_y) / 2
move_to_xy(mid_x, mid_y)
put_down_xy(mid_x, mid_y)

# C1 把沙发上的水杯放到椅子上
cup_obj = parse_obj_name('cup on the sofa',objects)
chair_obj = parse_obj_name('chair',objects)
move_to_obj_by_offset(cup_obj, 0, 0)
pick_up_obj(cup_obj)
move_to_obj_by_offset(chair_obj, 0, 0)
put_down_obj_by_offset(chair_obj, 0, 0)

# C2 把红色方块从桌子上拿起，放到蓝色方块和黄色方块中间
red_block_obj = parse_obj_name('red block on the table',objects)
blue_block_obj = parse_obj_name('blue block',objects)
yellow_block_obj = parse_obj_name('yellow block',objects)
move_to_obj_by_offset(red_block_obj, 0, 0)
pick_up_obj(red_block_obj)
blue_block_x, blue_block_y = get_obj_xy(blue_block_obj)
yellow_block_x, yellow_block_y = get_obj_xy(yellow_block_obj)
mid_x = (blue_block_x + yellow_block_x) / 2
mid_y = (blue_block_y + yellow_block_y) / 2
move_to_xy(mid_x, mid_y)
put_down_xy(mid_x, mid_y)

# C3 把地上所有的非家具丢到垃圾桶中
objects_on_ground = parse_obj_name('objects on the ground that are not furniture',objects)
trash_can_obj = parse_obj_name('trash can',objects)
for object in objects_on_ground:
    move_to_obj_by_offset(object, 0, 0)
    pick_up_obj(object)
    move_to_obj_by_offset(trash_can_obj, 0, 0)
    put_down_obj_by_offset(trash_can_obj, 0, 0)

# C4 以长度为100的方形方式绕着桌子运动，当有红色方块出现时，夹起他，放到垃圾桶中
table_obj = parse_obj_name('table',objects)
table_x, table_y = get_obj_xy(table_obj)
trash_can_obj = parse_obj_name('trash can',objects)
i = 0
while True:
    # 绕着桌子运动,一次只运动一条边
    if i % 4 == 0:
        move_to_xy(table_x + 50, table_y + 50)
    elif i % 4 == 1:
        move_to_xy(table_x + 50, table_y - 50)
    elif i % 4 == 2:
        move_to_xy(table_x - 50, table_y - 50)
    else:       
        move_to_xy(table_x - 50, table_y + 50)
    i += 1
    # 检测红色方块
    red_blocks = parse_obj_name('red block',objects)
    if red_blocks:
        for red_block in red_blocks:
            move_to_obj_by_offset(red_block, 0, 0)
            pick_up_obj(red_block)
            move_to_obj_by_offset(trash_can_obj, 0, 0)
            put_down_obj_by_offset(trash_can_obj, 0, 0)
