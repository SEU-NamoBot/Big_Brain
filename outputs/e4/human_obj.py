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
- `C3` 把地上所有的非家具丢到垃圾桶中
- `C4` 以长度为100的方形方式绕着桌子运动，当有红色方块出现时，夹起他，放到垃圾桶中
"""

import numpy as np
from action.robot_api import *
from utils.utils import *

objects = load_L2_memory()

# N1 导航到(100,200)
pass

# N2 导航到垃圾桶旁边
ret_val = objects['trash_can']

# N3 绕垃圾桶做长50，宽50的方形运动
ret_val = objects['trash_can']


# N4 前往坐标绝对值之和最小的垃圾桶旁边，以50为半径绕行一圈，随后返回出发位置
trash_cans = objects['trash_can']
min_sum = float('inf')
closest_trash_can = None
for trash_can in trash_cans:
    x, y = get_obj_xy(trash_can)
    coord_sum = abs(x) + abs(y)
    if coord_sum < min_sum:
        min_sum = coord_sum
        closest_trash_can = trash_can
ret_val = closest_trash_can

# G1 夹起红色方块
# redd block
ret_val = []
for obj_name in objects['block']:
    if get_obj_rgb(obj_name) == 'red':
        ret_val.append(obj_name)

# G2 夹起位于地面的红色方块
ret_val = []
for obj_name in objects['block']:
    if get_obj_rgb(obj_name) == 'red':
        z = get_obj_z(obj_name)
        if 0 < z < 10:
            ret_val.append(obj_name)

# G3 把物体放到桌子上
ret_val = objects['table']

# G4 把物体放到蓝色方块和黄色方块中间
# first parse: blue block
ret_val = []
for obj_name in objects['block']:
    if get_obj_rgb(obj_name) == 'blue':
        ret_val.append(obj_name)
# second parse: yellow block
ret_val = []
for obj_name in objects['block']:
    if get_obj_rgb(obj_name) == 'yellow':
        ret_val.append(obj_name)

# C1 把沙发上的水杯放到椅子上
# cup on the sofa
ret_val = []
for cup_name in objects['cup']:
    cup_x, cup_y = get_obj_xy(cup_name)
    cup_z = get_obj_z(cup_name)
    for sofa_name in objects['sofa']:
        sofa_x, sofa_y = get_obj_xy(sofa_name)
        sofa_size_x, sofa_size_y, sofa_size_z = get_obj_size(sofa_name)
        if sofa_x - sofa_size_x/2 < cup_x < sofa_x + sofa_size_x/2 and sofa_y - sofa_size_y/2 < cup_y < sofa_y + sofa_size_y/2 and cup_z > sofa_size_z:
            ret_val.append(cup_name)

# chair
ret_val = objects['chair']


# C2 把红色方块从桌子上拿起，放到蓝色方块和黄色方块中间
# red block
ret_val = []
for block_name in objects['block']:
    for table_name in objects['table']:
        table_x, table_y = get_obj_xy(table_name)
        table_size_x, table_size_y, table_size_z = get_obj_size(table_name)
        block_x, block_y = get_obj_xy(block_name)
        block_z = get_obj_z(block_name)
        if table_x - table_size_x/2 < block_x < table_x + table_size_x/2 and table_y - table_size_y/2 < block_y < table_y + table_size_y/2 and block_z > table_size_z:
            if get_obj_rgb(block_name) == 'red':
                ret_val.append(block_name) 

# blue block
ret_val = []
for block_name in objects['block']:
    if get_obj_rgb(block_name) == 'blue':
        ret_val.append(block_name)

# yellow block
ret_val = []
for block_name in objects['block']:
    if get_obj_rgb(block_name) == 'yellow':
        ret_val.append(block_name)

# C3 把地上所有的非家具丢到垃圾桶中
ret_val = []
for obj_name in objects['block'] + objects['cup'] + objects['bottle']:
    obj_x, obj_y = get_obj_xy(obj_name)
    obj_z = get_obj_z(obj_name)
    if obj_z < 10: # on the ground
        ret_val.append(obj_name)

ret_val = objects['trash_can']

# C4 以长度为100的方形方式绕着桌子运动，当有红色方块出现时，夹起他，放到垃圾桶中
ret_val = objects['table']  

ret_val = []
for block_name in objects['block']:
    block_x, block_y = get_obj_xy(block_name)
    if get_obj_rgb(block_name) == 'red':
        ret_val.append(block_name)
        
ret_val = objects['trash_can']