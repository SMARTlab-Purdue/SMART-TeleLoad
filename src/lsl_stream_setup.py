from pylsl import *

### For Lab-streaming Layer (LSL)
# For mouse left btn
info_teleload_mouse_btn = StreamInfo('teleload_mouse_btn', 'mouse_button', 1, IRREGULAR_RATE, cf_string, 'smart_teleload')
teleload_mouse_btn_outlet = StreamOutlet(info_teleload_mouse_btn)
teleload_mouse_btn_channels = info_teleload_mouse_btn.desc().append_child("channels")
teleload_mouse_btn_channels.append_child("channel")\
        .append_child_value("name", "button_state")\
        .append_child_value("unit", "pressed_released")\
        .append_child_value("type", "boolean")

info_teleload_mouse_pos = StreamInfo('teleload_mouse_pos', 'mouse_pose', 2, IRREGULAR_RATE, cf_int32, 'smart_teleload')
teleload_mouse_pos = StreamOutlet(info_teleload_mouse_pos)
teleload_mouse_pos_channels = info_teleload_mouse_pos.desc().append_child("channels")
teleload_mouse_pos_channels.append_child("channel")\
        .append_child_value("name", "posX")\
        .append_child_value("unit", "number")\
        .append_child_value("type", "int")
teleload_mouse_pos_channels.append_child("channel")\
        .append_child_value("name", "posY")\
        .append_child_value("unit", "number")\
        .append_child_value("type", "int")
        

# task accuracy
info_teleload_task_accuracy = StreamInfo('teleload_task_accuracy', 'mission_accuracy', 4, IRREGULAR_RATE, cf_float32, 'smart_teleload')
teleload_task_accuracy_outlet = StreamOutlet(info_teleload_task_accuracy)
teleload_task_accuracy_channels = info_teleload_task_accuracy.desc().append_child("channels")
teleload_task_accuracy_channels.append_child("channel")\
        .append_child_value("name", "success")\
        .append_child_value("unit", "success count")\
        .append_child_value("type", "float")
teleload_task_accuracy_channels.append_child("channel")\
        .append_child_value("name", "failure")\
        .append_child_value("unit", "failure count")\
        .append_child_value("type", "float")
teleload_task_accuracy_channels.append_child("channel")\
        .append_child_value("name", "success_rate")\
        .append_child_value("unit", "percent")\
        .append_child_value("type", "float")
teleload_task_accuracy_channels.append_child("channel")\
        .append_child_value("name", "total_scores")\
        .append_child_value("unit", "scores")\
        .append_child_value("type", "float")

# task exp status
info_teleload_exp_status = StreamInfo('teleload_exp_status', 'task_status', 1, IRREGULAR_RATE, cf_string, 'smart_teleload')
teleload_exp_status_outlet = StreamOutlet(info_teleload_exp_status)
teleload_exp_status_channels = info_teleload_exp_status.desc().append_child("channels") # [Start] [Setup] [Plus] [Countdown] [Main_Start] [SAM_Survey_Start] [NASA_Survey_Start] [End]
teleload_task_accuracy_channels.append_child("channel")\
        .append_child_value("name", "status")\
        .append_child_value("unit", "string")\
        .append_child_value("type", "string")


def lsl_outlet_mouse_pos(mouse_pos): # publish current mouse positions; [x, y]
    #print("image_ID, mouse_pos = ", image_ID, mouse_pos[0], mouse_pos[1])
    teleload_mouse_pos.push_sample([mouse_pos[0], mouse_pos[1]])

## Need to modify main gui codes
def lsl_outlet_mouse_btn(mouse_btn): # publish data when mouse button is pressed or released
    #print("image_ID, mouse_btn = ", image_ID, mouse_btn)
    # 0 means realeased, 1 means pressed
    teleload_mouse_btn_outlet.push_sample([mouse_btn])

def lsl_outlet_task_accuracy(task_accuracy_data): # publish [success click, failure click, success rate, total scores]
    teleload_mouse_btn_outlet.push_sample([task_accuracy_data[0], task_accuracy_data[1], task_accuracy_data[2], task_accuracy_data[3]])


def lsl_outlet_exp_status(exp_conditions): # publish [Start] [Setup] [Plus] [Countdown] [Main_Start] [SAM_Survey_Start] [NASA_Survey_Start] [Mission_summary] [End]
    teleload_exp_status_outlet.push_sample([exp_conditions])


# [Start] [Setup] [Plus] [Countdown] [Main_Start] [SAM_Survey_Start] [NASA_Survey_Start] [Mission_summary] [End]
