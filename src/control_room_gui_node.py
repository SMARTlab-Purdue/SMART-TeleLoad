### OpenCV Libs
from re import I
import cv2
from cv_bridge import CvBridge, CvBridgeError

### Python Libs
import sys, os, time, random,  math
from threading import Thread
import numpy as np
import pandas as pd  
import glob
from playsound import playsound

### For lsl.
from pylsl import StreamInfo, StreamOutlet, StreamInlet, local_clock, resolve_stream, resolve_byprop, cf_float32, cf_double64, cf_string, cf_int32, IRREGULAR_RATE


### PyQt Libs
from PyQt5 import QtGui, uic
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QThread, QTimer, QEvent, QPropertyAnimation, QPoint, QRect, QUrl
from PyQt5.QtGui import QPixmap, QCursor, QPainter, QBrush, QPen, QImage
from PyQt5.QtWidgets import *

### 
from lsl_stream_setup import *


#############################
## Global Variables
#############################
one_seconds_timer = 1000 # 1 second
START_number = 1 #10 #10 #For test it was 10

WIN_WIDTH = 512 
WIN_HEIGHT = 256 

Mouse_Click_Limit = 0.2 #unit: seconds


### For DNN based Object Detection algorithm
traget_cfg = 'darknet_files/yolov3-custom.cfg'
traget_weights = 'darknet_files/yolov3-custom_final.weights'

net = cv2.dnn.readNet(traget_weights, traget_cfg)
net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)

model = cv2.dnn_DetectionModel(net)
model.setInputParams(size=(WIN_HEIGHT, WIN_HEIGHT), scale=1/255, swapRB=True)
activate_model_img = np.zeros((WIN_HEIGHT,WIN_HEIGHT,3), dtype=np.uint8)
model.detect(activate_model_img, 0.8, 0.9)

CONFIDENCE_THRESHOLD = 0.2
NMS_THRESHOLD = 0.4
COLORS = [(0, 255, 255), (255, 255, 0), (0, 255, 0), (255, 0, 0)]

class_names = ["actual", "fake"]

### For sound playing
correct_sound = 'resources/sounds/smw_coin_20ms.wav'
incorrect_sound = 'resources/sounds/smw_yoshi_spit_20ms.wav'





def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class CCTV_GUI_Window(QMainWindow):
    def __init__(self):
        super(CCTV_GUI_Window, self).__init__()

        #self.showFullScreen()  # for activating fullscreen windows

        self.screen = QDesktopWidget().screenGeometry()
        self.screen_width = self.screen.width()
        self.screen_height = self.screen.height()
        self.screen_center_position = [self.screen.width()/2, self.screen.height()/2]
        
        lsl_outlet_exp_status("Setup")
        uic.loadUi('pyqt_ui_files/PyQT_CCTV_Setting.ui', self)
        self.prep_start_btn.clicked.connect(self.prep_start_btn_on_click)

        #====================================================#
        #||                Global Variables                ||#
        #====================================================#
        self.cctv_GUI_control_state = 0

        self.cctv_GUI_control_time = 0 
        self.cctv_GUI_control_time_rest = 0 
   
        self.final_success_click = 0
        self.final_failure_click = 0

        self.obtained_scores = 0

        self.end_time_cctv_1 = 0
        self.end_time_cctv_2 = 0
        self.end_time_cctv_3 = 0
        self.end_time_cctv_4 = 0
       
        self.previous_mouse_position = [0,0]
        self.current_mouse_position = [0,0]
        self.current_click_with_mouse_position = [0,0,0]

        self.default_pixmap = QPixmap('resources/SMART-LAB_Purdue.jpg')
        self.default_pixmap = self.default_pixmap.scaled(int(WIN_WIDTH*0.6), int(WIN_HEIGHT*0.6), Qt.KeepAspectRatio, Qt.SmoothTransformation)

        self.QMsg_Box_submit_btn = QMessageBox()
        self.QMsg_Box_submit_btn.setWindowTitle("Missing Confirms")
        self.QMsg_Box_submit_btn.setIcon(QMessageBox.Critical)

        self.pos = QCursor.pos()


        #====================================================#
        #||                PyQT5 Setup Part                ||#
        #====================================================#  
        
        ### For timers
        # set Timer for prep imags display
        self.qTimer_prep_counting = QTimer()
        self.qTimer_prep_counting.setInterval(one_seconds_timer) # 1000 ms = 1 s, 0 = as soon as 
        self.qTimer_prep_counting.timeout.connect(self.prep_count_display)
    
        # set Timer for main experiment display
        self.qTimer_main_exp_counting = QTimer()
        self.qTimer_main_exp_counting.setInterval(one_seconds_timer) # 1000 ms = 1 s, 0 = as soon as 
        self.qTimer_main_exp_counting.timeout.connect(self.main_exp_count_display)

        ### Activate Timer
        # set Timer for CAM display and rosspin
        self.qTimer_cctv_gui_show = QTimer()
        self.qTimer_cctv_gui_show.setInterval(30) #ms/ 0 = as soon as <- need to check video frame 30Hz
        self.qTimer_cctv_gui_show.timeout.connect(self.cctv_gui_update)


    #################################################################
    # Update obtained scores
    #################################################################
    def cctv_GUI_overall_scores_callback(self):
        self.Score_obtained_label_5.setText('<html><head/><body><p align="center"><span style=" font-size:18pt; font-weight:600;">' + str(self.obtained_scores) + '</span></p></body></html>')
        # Stream task accuracy
        success_rate= round(self.final_success_click/(self.final_failure_click + self.final_success_click), 2)
        lsl_task_accuracy_data = [self.final_success_click, self.final_failure_click, success_rate, self.obtained_scores]
        lsl_outlet_task_accuracy(lsl_task_accuracy_data)


        
    #################################################################
    # Mouse Event Callbacks                                         #
    ################################################################# 
    def answer_check(self, classes, scores, boxes):
        if not len(classes):
            answer_result = False          
        else:
            for (classid, score, box) in zip(classes, scores, boxes):
                color = COLORS[int(classid) % len(COLORS)]
                label = "%s : %f" % (class_names[classid[0]], score)
                if class_names[classid[0]] == "fake": ## answer correct
                    answer_result = True #it was False
                else:
                    #print("mistake:: wrong objects")
                    #print("Mistake Click")
                    answer_result = False  
        return  answer_result

    def CCTV_mouse_event_1(self, event):
        start = time.time()
        self.current_click_with_mouse_position = [1, self.current_mouse_position[0], self.current_mouse_position[1]]
        diff_time = start - self.end_time_cctv_1

        if diff_time >= Mouse_Click_Limit and self.remaining_time >= 0:
            classes, scores, boxes = model.detect(self.frame_1, 0.8, 0.9)
            self.object_type_in_cctv_1 = self.answer_check(classes, scores, boxes)

            if self.object_type_in_cctv_1:
                playsound(correct_sound)
                self.final_success_click += 1
                self.obtained_scores += 1 
            else:
                playsound(incorrect_sound)
                self.final_failure_click += 1
                self.obtained_scores -= 1       

            self.cctv_GUI_overall_scores_callback()

        self.end_time_cctv_1 = time.time()
    
    def CCTV_mouse_event_2(self, event):
        start = time.time()
        self.current_click_with_mouse_position = [1, self.current_mouse_position[0], self.current_mouse_position[1] ]
        diff_time = start - self.end_time_cctv_2

        if diff_time >= Mouse_Click_Limit and self.remaining_time >= 0:
            classes, scores, boxes = model.detect(self.frame_2, 0.8, 0.9)
            self.object_type_in_cctv_2 = self.answer_check(classes, scores, boxes)

            if self.object_type_in_cctv_2:
                playsound(correct_sound)
                self.final_success_click += 1
                self.obtained_scores += 1 
            else:
                playsound(incorrect_sound)
                self.final_failure_click += 1
                self.obtained_scores -= 1       

            self.cctv_GUI_overall_scores_callback()

        self.end_time_cctv_2 = time.time()
    
    def CCTV_mouse_event_3(self, event):
        start = time.time()
        self.current_click_with_mouse_position = [1, self.current_mouse_position[0], self.current_mouse_position[1] ]
        diff_time = start - self.end_time_cctv_3

        if diff_time >= Mouse_Click_Limit and self.remaining_time >= 0:
            classes, scores, boxes = model.detect(self.frame_3, 0.8, 0.9)
            self.object_type_in_cctv_3 = self.answer_check(classes, scores, boxes)

            if self.object_type_in_cctv_3:
                playsound(correct_sound)
                self.final_success_click += 1
                self.obtained_scores += 1 
            else:
                playsound(incorrect_sound)
                self.final_failure_click += 1
                self.obtained_scores -= 1       
            
            self.cctv_GUI_overall_scores_callback()

        self.end_time_cctv_3 = time.time()
    
    def CCTV_mouse_event_4(self, event):
        start = time.time()
        self.current_click_with_mouse_position = [1, self.current_mouse_position[0], self.current_mouse_position[1] ]
        diff_time = start - self.end_time_cctv_4

        if diff_time >= Mouse_Click_Limit and self.remaining_time >= 0:
            classes, scores, boxes = model.detect(self.frame_4, 0.8, 0.9)
            self.object_type_in_cctv_4 = self.answer_check(classes, scores, boxes)

            if self.object_type_in_cctv_4:
                playsound(correct_sound)
                self.final_success_click += 1
                self.obtained_scores += 1 
            else:
                playsound(incorrect_sound)
                self.final_failure_click += 1
                self.obtained_scores -= 1       

            self.cctv_GUI_overall_scores_callback()

        self.end_time_cctv_4 = time.time()
    

    #################################################################
    # PyQT Windows                                                  #
    #################################################################   
    def prep_start_btn_on_click(self):
        #Setting global variables
        self.participant_name = self.prep_part_name_textEdit.toPlainText()

        self.exp_num_cam = int(self.prep_num_cam_var.value())
        self.exp_obj_speed = int(self.prep_obj_speed_var.value())

        self.exp_prep_time = int(self.prep_prep_time_textEdit.toPlainText()) # seconds
        self.exp_main_time = int(self.prep_exp_time_textEdit.toPlainText()) # seconds

  
        target_video_imdir = 'resources/object_shape/smartmbot_videos/speed_'+ str(self.exp_obj_speed) +'/'
        ext = ['mp4'] 
        
        self.target_video = []
        [self.target_video.extend(glob.glob(target_video_imdir + '*.' + e)) for e in ext]
        print(self.target_video)
        random.shuffle(self.target_video)

        self.GUI_setting_prep_session()
        
    def GUI_setting_prep_session(self):
        self.cctv_GUI_control_state = 1
        lsl_outlet_exp_status("Start")
        uic.loadUi('pyqt_ui_files/PyQT_CCTV_GUI.ui', self)
        
        self.CCTV_image_label_1.setPixmap(self.default_pixmap)
        self.CCTV_image_label_1.setAlignment(Qt.AlignCenter)

        self.CCTV_image_label_2.setPixmap(self.default_pixmap)
        self.CCTV_image_label_2.setAlignment(Qt.AlignCenter)

        self.CCTV_image_label_3.setPixmap(self.default_pixmap)
        self.CCTV_image_label_3.setAlignment(Qt.AlignCenter)

        self.CCTV_image_label_4.setPixmap(self.default_pixmap)
        self.CCTV_image_label_4.setAlignment(Qt.AlignCenter)

        self.CCTV_image_label_1.mousePressEvent = self.CCTV_mouse_event_1
        self.CCTV_image_label_2.mousePressEvent = self.CCTV_mouse_event_2
        self.CCTV_image_label_3.mousePressEvent = self.CCTV_mouse_event_3
        self.CCTV_image_label_4.mousePressEvent = self.CCTV_mouse_event_4

        self.i = START_number 

        self.remaining_time = self.exp_main_time
        self.current_scores = 0

        (self.previous_cursor_x, self.previous_cursor_y) = (None,None)
        self.end_time = 0

        self.remaining_count_label_5.setText('<html><head/><body><p align="center"><span style=" font-size:18pt; font-weight:600;">' + str(self.remaining_time) + '</span></p></body></html>')

        lsl_outlet_exp_status("Plus")
        self.qTimer_prep_counting.start() # set Timer for prep imags display

    def confirm_score_btn_click(self):
        self.qTimer_cctv_gui_show.stop()                        
        self.close()

    def sam_submit_bt_on_click(self):
        Valence_check = self.Valence_checkBox.isChecked()
        Arousal_check = self.Arousal_checkBox.isChecked()

        if Valence_check+Arousal_check == 2:
            #Read slider values
            self.results_sam_valence = self.Valence_Slider.value()
            self.results_sam_arousal = self.Arousal_Slider.value()

            # Go to the NASA-TLX Questionary   
            lsl_outlet_exp_status("NASA_Survey_Start")
            uic.loadUi('pyqt_ui_files/PyQT_subQ_NASA_GUI.ui', self)
            self.submit_nasa_button.clicked.connect(self.nasa_tlx_submit_bt_on_click)

        else:
            ## Warning Box
            self.QMsg_Box_submit_btn.setText("Please make sure to check all Confirms boxes;")
            self.QMsg_Box_submit_btn.exec()


    def nasa_tlx_submit_bt_on_click(self):
        mental_check = self.mental_checkBox.isChecked()
        physical_check = self.physical_checkBox.isChecked()
        temporal_check = self.temporal_checkBox.isChecked()
        performance_check = self.performance_checkBox.isChecked()
        effort_check = self.effort_checkBox.isChecked()
        frustration_check = self.frustration_checkBox.isChecked()
        
        check_confrim = mental_check + physical_check + temporal_check + performance_check + effort_check + frustration_check
     
        if check_confrim == 6:
            self.results_nasa_mental = self.mental_Slider.value()
            self.results_nasa_physical = self.physical_Slider.value()
            self.results_nasa_temporal = self.temporal_Slider.value()
            self.results_nasa_performance = self.performance_Slider.value()
            self.results_nasa_effort = self.effort_Slider.value() 
            self.results_nasa_frustration = self.frustration_Slider.value() 

            # End the GUI program
            lsl_outlet_exp_status("Mission_summary")
            uic.loadUi('pyqt_ui_files/PyQT_CCTV_Score_GUI.ui', self)
            self.PyQT_CCTV_Score_GUI_Session()

        else:
            ## Warning Box
            self.QMsg_Box_submit_btn.setText("Please make sure to check all Confirms boxes;")
            self.QMsg_Box_submit_btn.exec()

    def main_exp_count_display(self):
        if self.remaining_time < 0:
            self.qTimer_cctv_gui_show.stop()
            self.qTimer_prep_counting.stop()
            
            if self.exp_num_cam > 0:
                self.cap_cam_1.release()
            if self.exp_num_cam > 1:
                self.cap_cam_2.release()
            if self.exp_num_cam > 2:
                self.cap_cam_3.release()
            if self.exp_num_cam == 3:
                self.cap_cam_4.release()
            
            lsl_outlet_exp_status("SAM_Survey_Start")
            uic.loadUi('pyqt_ui_files/PyQT_subQ_SAM_GUI.ui', self)
            self.submit_sam_btn.clicked.connect(self.sam_submit_bt_on_click)
            self.qTimer_main_exp_counting.stop()
        else:
            self.remaining_count_label_5.setText('<html><head/><body><p align="center"><span style=" font-size:18pt; font-weight:600;">' + str(self.remaining_time) + '</span></p></body></html>')

        self.remaining_time -= 1

    def prep_count_display(self):
        #print(self.i)
        if self.exp_prep_time > 0:
            self.exp_prep_time -= 1

        else:
            if self.i > 0:
                self.qTimer_prep_counting.setInterval(one_seconds_timer)
                self.prep_img_show_label.setText('<html><head/><body><p align="center"><span style=" color:#ffffff;">'+str(self.i)+'</span></p></body></html>')
                lsl_outlet_exp_status("Countdown")

            elif self.i == 0:
                self.prep_img_show_label.setText('<html><head/><body><p align="center"><span style=" color:#ffffff;">Start</span></p></body></html>')
                lsl_outlet_exp_status("Main_Start")

            else:            
                self.prep_img_show_label.close()

                self.qTimer_main_exp_counting.start() # set Timer for prep imags display

                self.qTimer_cctv_gui_show.start()

                if self.exp_num_cam > 0:
                    self.cap_cam_1 = cv2.VideoCapture(self.target_video[0])
                if self.exp_num_cam > 1:
                    self.cap_cam_2 = cv2.VideoCapture(self.target_video[1])
                if self.exp_num_cam > 2:
                    self.cap_cam_3 = cv2.VideoCapture(self.target_video[2])
                if self.exp_num_cam > 3:
                    self.cap_cam_4 = cv2.VideoCapture(self.target_video[3])

                self.qTimer_prep_counting.stop()

            self.i -= 1

    def PyQT_CCTV_Score_GUI_Session(self):
        
        # data = [Valence, Arousal]
        sam_results = [ self.results_sam_valence,
                        self.results_sam_arousal ]

        # ISA data::: -2 = Underutilised, -1 = Relaxed, 0 = Comfortable, 1 = High, 2 = Excessive
        # data = [Mental Demand, Physical Demand, Temporal Demand, Performance, Effort, Frustration] 
        nasa_results = [self.results_nasa_mental, 
                        self.results_nasa_physical, 
                        self.results_nasa_temporal, 
                        self.results_nasa_performance, 
                        self.results_nasa_effort, 
                        self.results_nasa_frustration ]
        

        mission_results = [int(self.obtained_scores)]
        click_results = [self.final_success_click, self.final_failure_click, self.final_success_click/(self.final_success_click+self.final_failure_click)]
        

        print("Subject Number=", self.participant_name)
        print("Camera_Number=", self.exp_num_cam)
        print("SAM_results=", sam_results)
        print("NASA-TLX_results=", nasa_results)
        print("Mission_scores =", mission_results)
        print("Clicks_results =", click_results)


        #mission_results = 333
        self.sccuess_score_label_1.setText('<html><head/><body><p><span style=" color:#0500ff;">' + str(click_results[0]) + '</span></p></body></html>')
        self.failure_score_label_1.setText('<html><head/><body><p><span style=" color:#ef2929;">' + str(click_results[1]) + '</span></p></body></html>')
        self.total_score_label_1.setText('<html><head/><body><p><span style=" color:#000000;">' + str(mission_results[0]) + '</span></p></body></html>')
        self.total_rate_label_1.setText('<html><head/><body><p><span style=" color:#000000;">' + str(round(click_results[0]/(click_results[0]+click_results[1]),4)) + '</span></p></body></html>')


        # Save results as CSV files
        df0 = pd.DataFrame({'P_Name':[self.participant_name]})
        df1 = pd.DataFrame({'Camera_Number':[self.exp_num_cam]})
        df2 = pd.DataFrame({'Object_Speed':[self.exp_obj_speed]})


        df3 = pd.DataFrame({'SAM_Result':sam_results})
        df4 = pd.DataFrame({'NASA_Result':nasa_results})
        df5 = pd.DataFrame({'Mission_Scores':mission_results})
        df6 = pd.DataFrame({'Click_Result': click_results})

        result=pd.concat([df0, df1, df2, df3, df4, df5, df6], axis=1, names=[])

        cvs_file_name = self.participant_name + "_cam_" + str(self.exp_num_cam) +"_speed_" + str(self.exp_obj_speed)+".csv"
        result.to_csv("subjective_results/"+cvs_file_name)

        lsl_outlet_mouse_pos("End")

        print("A session Done")

        self.confirm_score_btn.setEnabled(True)
        self.confirm_score_btn.clicked.connect(self.confirm_score_btn_click)

            
    def cctv_gui_update(self):
        ## reading mouse positions
        self.current_mouse_position = [self.pos.x(), self.pos.y()]       
        ## Publish mouse positions (x, y) 
        lsl_outlet_mouse_pos(self.current_mouse_position)

        if self.exp_num_cam > 0:
            self.ret_1, self.frame_1 = self.cap_cam_1.read()
            image_1 = QImage(self.frame_1, self.frame_1.shape[1], self.frame_1.shape[0], 
                            self.frame_1.strides[0], QImage.Format_RGB888)
            self.CCTV_image_label_1.setPixmap(QPixmap.fromImage(image_1))
            self.CCTV_image_label_1.setAlignment(Qt.AlignCenter)
        if self.exp_num_cam > 1:
            self.ret_2, self.frame_2 = self.cap_cam_2.read()
            image_2 = QImage(self.frame_2, self.frame_2.shape[1], self.frame_2.shape[0], 
                            self.frame_2.strides[0], QImage.Format_RGB888)
            self.CCTV_image_label_2.setPixmap(QPixmap.fromImage(image_2))
            self.CCTV_image_label_2.setAlignment(Qt.AlignCenter)
        if self.exp_num_cam > 2:
            self.ret_3, self.frame_3 = self.cap_cam_3.read()
            image_3 = QImage(self.frame_3, self.frame_3.shape[1], self.frame_3.shape[0], 
                            self.frame_3.strides[0], QImage.Format_RGB888)
            self.CCTV_image_label_3.setPixmap(QPixmap.fromImage(image_3))
            self.CCTV_image_label_3.setAlignment(Qt.AlignCenter)
        if self.exp_num_cam > 3:
            self.ret_4, self.frame_4 = self.cap_cam_4.read()
            image_4 = QImage(self.frame_4, self.frame_4.shape[1], self.frame_4.shape[0], 
                            self.frame_4.strides[0], QImage.Format_RGB888)
            self.CCTV_image_label_4.setPixmap(QPixmap.fromImage(image_4))
            self.CCTV_image_label_4.setAlignment(Qt.AlignCenter)
       

def main(args=None):
    app = QApplication(sys.argv)
    win = CCTV_GUI_Window()
    win.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()