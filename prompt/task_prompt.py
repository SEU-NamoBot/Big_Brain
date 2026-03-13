
BASE_PROMPT = """
import numpy as np
from action.robot_api import move_to_xy,move_to_obj_by_offset,pick_up_xy,pick_up_obj,put_down_xy, put_down_obj_by_offset
from utils.utils import parse_obj_name
from utils.utils import get_obj_xy,get_obj_size,load_L2_memory

objects = load_L2_memory()
# move to coordinates (100, 200) and pick up the item at coordinates (125, 220) 
move_to_xy(100, 200)
pick_up_xy(125, 220)

#put down item at 10cm south of the Table
table_obj = parse_obj_name('Table',objects)
put_down_obj_by_offset(table_obj,0,-10)

# move to chair with a cup on it
chair_obj = parse_obj_name('chair with a cup on it',objects)
move_to_obj_by_offset(chair_obj,0,0)

# pick up "Cup1"
cup_obj = parse_obj_name('Cup1',objects)
pick_up_obj(cup_obj)
# Move to the table and position it 50cm south and 50cm west of the center
table_obj = parse_obj_name('table',objects)
move_to_obj_by_offset(table_obj, -50, 50)

# pick up the red fruit from the table  and throw it into the leftmost trash can
table_obj = parse_obj_name('Table',objects)
apple_obj = parse_obj_name('red fruit')
trash_obj = parse_obj_name('leftmost trash can')
move_to_obj_by_offset(table_obj, 0, 0)
pick_up_obj(apple_obj)
move_to_obj_by_offset(trash_obj, 0, 0)
put_down_obj_by_offset(trash_obj, 0, 0)

# put the cup next to the blue box
cup_obj = parse_obj_name('cup',objects)
box_obj = parse_obj_name('Blue Box')
move_to_obj_by_offset(cup_obj, 0, 0)
pick_up_obj(cup_obj)
move_to_obj_by_offset(box_obj,0,0)
box_length,box_width,box_height = get_obj_size(box_obj)
put_down_obj_by_offset(box_obj, box_length/2+5, box_width/2+5)

# move around the office chair in a rectangular path of 3 meters by 2 meters
chair_obj = parse_obj_name('the office chair',objects)
chair_x,chair_y = get_obj_xy(chair_obj)
move_to_xy(chair_x+150, chair_y+100)
move_to_xy(chair_x+150, chair_y-100)
move_to_xy(chair_x-150, chair_y-100)
move_to_xy(chair_x-150, chair_y+100)
move_to_xy(chair_x+150, chair_y+100)

# move to the table which there are two bottles on it, then move to the counter, repeat 3 times
table_obj = parse_obj_name('table which there are two bottles on it')
counter_obj = parse_obj_name('Counter')
for _ in range(3):
    move_to_obj_by_offset(table_obj, 0, 0)
    move_to_obj_by_offset(counter_obj, 0, 0)
"""

OLD_PROMPT = '''
import numpy as np
from action.robot_api import move_to_xy, move_to_obj_by_offset, pick_up_xy, pick_up_obj, put_down_xy, put_down_obj_by_offset
from utils.utils import get_obj_xy, get_obj_size

# move to coordinates (100, 200) and pick up the item at coordinates (125, 220) 
move_to_xy(100, 200)
pick_up_xy(125, 220)

# put down item at 10cm south of the Table
put_down_obj_by_offset('Table', 0, -10)

# move to "Chair"
move_to_obj_by_offset('Chair', 0, 0)

# pick up "Cup1"
pick_up_obj('Cup1')

# put down item at coordinates (5, 10)
put_down_xy(5, 10)

# move to "Table"
move_to_obj_by_offset('Table', 1, 1)

# pick up the red apple from the table and throw it into the trash can
move_to_obj_by_offset('Table', 0, 0)
pick_up_obj('Red_Apple')
move_to_obj_by_offset('Trash_Can', 0, 0)
put_down_obj_by_offset('Trash_Can', 0, 0)

# put the cup next to the blue box
move_to_obj_by_offset('Cup', 0, 0)
pick_up_obj('Cup')
move_to_obj_by_offset('Blue_Box', 0, 0)
box_length,box_width,box_height = get_obj_size('Blue_Box')
put_down_obj_by_offset('Blue_Box', box_length/2+5, box_width/2+5)

# move around the office chair in a rectangular path of 3 meters by 2 meters
chair_x,chair_y = get_obj_xy("chair")
move_to_xy(chair_x+150, chair_y+100)
move_to_xy(chair_x+150, chair_y-100)
move_to_xy(chair_x-150, chair_y-100)
move_to_xy(chair_x-150, chair_y+100)
move_to_xy(chair_x+150, chair_y+100)

# move to the table, then move to the counter, repeat 3 times
for _ in range(3):
    move_to_obj_by_offset('Table', 0, 0)
    move_to_obj_by_offset('Counter', 0, 0)

'''