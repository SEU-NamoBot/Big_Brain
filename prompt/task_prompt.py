
BASE_PROMPT = '''
import numpy as np
from big_brain.action.robot_api import move_to_xy, move_to_obj_by_offset, pick_up_xy, pick_up_obj, put_down_xy, put_down_obj_by_offset
from big_brain.utils.position_utils import get_obj_xy, get_obj_size

# move to coordinates (100, 200) and pick up the item at coordinates (125, 220) 
move_to_xy(100, 200)
pick_up_xy(125, 220)

# put down item at the center of the Table
put_down_obj_by_offset('Table', 0, 0)

# move to "Chair"
move_to_obj_by_offset('Chair', 0, 0)

# pick up "Cup1"
pick_up_obj('Cup1')

# put down item at coordinates (5, 10)
put_down_xy(5, 10)

# move to "Table" and put down item at 1cm north and 1cm east of the table center
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