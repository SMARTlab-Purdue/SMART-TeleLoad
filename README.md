# SMART-TeleLoad

![Alt text](doc/smart_teleload_git.png){: width="80%"}

## Overview
Teleoperation system has witnessed remarkable advancements in recent years, driven by advanced computing technology that outperforms human operators in terms of speed and accuracy on repetitive tasks. Teleoperation systems are characterized by complex and dynamic interplay between human operators and their remote environments. However, there is an urgent need to develop a novel and practical stimulus tool capable of generating affective loads for teleoperation systems. To address this gap, this repository introduces a pragmatic stimulus tool designed to bridge the gap in existing stimuli tools and enable to generating the targeted affective load in the latest teleoperation systems and applications. The proposed tool comprises open-source-based graphic user interface (GUI) programs capable of modulating various control variables relating to the stimulus as needed for diverse research and practical applications and supports a lab-streaming layer (LSL) to easily and effectively connect with other systems (e.g., physiological sensors, and other GUI programs regardless of operating systems). Through an extensive user study involving 30 participants, we validated the performance of the proposed stimulus tool by analyzing multiple subjective surveys with aspects of the cognitive and emotional loads.

## Repository Files

This repository is composed of two main folders: 

* `doc`: paper and figures for this git
* `src`: main stimulus GUI programs and resources as below folder tree:

![Alt text](doc/smart_teleload_tree.png){: width="80%"}

- `src/darknet_files`: including the essential cfg file and split weights zip files necessary for object detection algorithms.
- `src/pyqt_ui_files`: including six UI design files used in the SMART-TeleLoad program
- `src/resource`: having three folders including supplementary files, such as images, effect sounds, and pre-recorded video files.
- `src/subjective_results`: saving directory for the human subject's answers and mission scores from the subjective questionnaire

- `src/control_room_gui_node.py`:
- `src/lsl_outlet_reader.py`: an example code to read the LSL stream data, which is an optional code for user to check the LSL outlet stream data. 
- `src/lsl_stream_setup.py`: defining the LSL out streams which is connected to 



## Instruction tutorial
Before starting this program, your machine should have below python libaries to run the main GUI program:
* pylsl
* panda
* numpy
* 

After installing the libaries, please 

1. `cd src` #to go to the `src` folder
2. `python control_room_gui_node.py` #run main program


## LSL outlets

### XXX

### XXX

### XXX

### XXX


## Output Files
### task performance and restuls


## Acknowledgement
This material is based upon work supported by the National Science Foundation under Grant No. IIS-1846221. Any opinions, findings, and conclusions or recommendations expressed in this material are those of the author(s) and do not necessarily reflect the views of the National Science Foundation.


## Citation
Please use the following citation:

Jo, W., Go, C., & Min, B. C. (2023). ''SMART-TeleLoad: A New Graphic User Interface to Generate Affective Loads for Teleoperation''. _Journal_, vol(no), x-x.


@article{spt_task_2023,
    title={SMART-TeleLoad: A New Graphic User Interface to Generate Affective Loads for Teleoperation},
    author={Wonse Jo and Go-eum Cha and Byung-Cheol Min},
    journal={TBD},
    volume={},
    number={},
    pages={},
    year={2023},
    publisher={},
    doi={}
}



