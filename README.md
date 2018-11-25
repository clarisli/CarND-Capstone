# Programming a Real Self-Driving Car

![alt text][image1]

The goal of this project is to to implement core functionality of a autonomous vehicle system, including traffic light detection, control, and waypoint following. The steps are:

1. Waypoint Updater Node (Partial): Complete a partial waypoint updater which subscribes to `/base_waypoints` and `/current_pose` and publishes to `/final_waypoints`.
2. DBW Node: Once waypoint updater is publishing `/final_waypoints`, the waypoint_follower node will start publishing messages to the `/twist_cmd` topic. After completing this step, the car should drive in the simulator, ignoring the traffic lights.
3. Traffic Light Detection: This can be split into 2 parts:
	* Detection: Detect the traffic light and its color from the `/image_color`. The topic `/vehicle/traffic_lights` contains the exact location and status of all traffic lights in simulator, use it to test the output.
	* Waypoint publishing: Once correctly identified the traffic light and determined its position, convert it to a waypoint index and publish it.
4. Waypoint Updater (Full): Use `/traffic_waypoint` to change the waypoint target velocities before publishing to `/final_waypoints`. Your car should now stop at red traffic lights and move when they are green.
5. Traffic Light Classification: Train a deep learning classifier to classify the entire image as containing either a red light, yellow light, green light, or no light.


[//]: # (Image References)

[image1]: ./imgs/udacity_car.png
[image2]: ./imgs/ros_graph.png
[image3]: ./imgs/tl-detector-ros-graph.png
[image4]: ./imgs/waypoint-updater-ros-graph.png
[image5]: ./imgs/dbw-node-ros-graph.png
[image6]: ./imgs/left0003.jpg
[image7]: ./imgs/left0011.jpg
[image8]: ./imgs/left0027.jpg
[image9]: ./imgs/left0681.jpg
[image10]: ./imgs/left0701.jpg
[image11]: ./imgs/left0561.jpg
[image12]: ./imgs/sim_light_classifier.png
[image13]: ./imgs/real_light_classifier.png

### Team

| Name | Email |
|------|-------| 
| Claris Li (Lead) | li.claris(at)gmail.com |
| Sijun Xiao | hbxsj1990(at)163.com |
| Joao Marques | jpmarques19(at)gmail.com |
| Chunfeng Yang | margaret_ycf(at)yahoo.com |
| Shawn Tan | yuxiaota(at)gmail.com |

### System Architecture

The following is a system architecture diagram showing the ROS nodes and topics used in the project.

![alt text][image2]

### Code Structure

Find the ROS packages for this project under the `/ros/src/` directory.

#### `/ros/src/tl_detector/`

This package contains two nodes:

1. `tl_detector.py`: traffic light detection node
2. `light_classification_model/tl_classfier.py`: traffic light classification node

The purpose is to publish locations to publish locations to stop for red traffic lights.

![alt text][image3]

#### `/ros/src/waypoint_updater/`

This package contains the waypoint updater node: `waypoint_updater.py`. The purpose of this node is to update the target velocity property of each waypoint based on traffic light and obstacle detection data. 

![alt text][image4]

#### `/ros/src/twist_controller/`

This package contains the drive-by-wire (dbw) node that resiponsible for control the vehicle. Files worth noting:

1. `dbw_node.py`: the dbw node
2. `twist_controller.py`
3. `pid.py`
3. `lowpass.py`

![alt text][image5]

#### `/ros/src/styx/`
A package that contains a server for communicating with the simulator, and a bridge to translate and publish simulator messages to ROS topics.

#### `/ros/src/styx_msgs/`
A package which includes definitions of the custom ROS message types used in the project.

#### `/ros/src/waypoint_loader/`
A package which loads the static waypoint data and publishes to `/base_waypoints`.

#### `/ros/src/waypoint_follower/`
A package containing code from [Autoware](https://github.com/CPFL/Autoware) which subscribes to `/final_waypoints` and publishes target vehicle linear and angular velocities in the form of twist commands to the `/twist_cmd` topic.

### Traffic Light Detection and Classification

We trained the traffic light detector with [Tensorflow Object Detection API](https://github.com/tensorflow/models/tree/master/research/object_detection). 

#### Create the Dataset

The dataset consists of images taken from the simulator and ROS bag files from the real site:

Images from the simulator:

![alt text][image6] ![alt text][image7] ![alt text][image8]

Images from the ROS bag:

![alt text][image9] ![alt text][image10] ![alt text][image11]

We could have mannually annotated the images using tools like [LabelImg](https://github.com/tzutalin/labelImg). Considering it's a time consuming task, we decided to use the annotated dataset shared by [Anthony Sarkis](https://github.com/swirlingsand) instead. The dataset can be downloaded [here](https://drive.google.com/file/d/0B-Eiyn-CUQtxdUZWMkFfQzdObUE/view?usp=sharing).

Tensorflow Object Detection API reads data using the TFRecords format - we wrote our custom script to convert the annotation YAML files to TFRecords.

#### Train the Model

For training, we did the following:

* Configured the object detection pipeline in a config file. Tensorflow provides many sample config files [here](https://github.com/tensorflow/models/tree/master/research/object_detection/samples/configs). We configed our customed pipelines based on `ssd_mobilenet_v1_coco.config`. We adjusted `num_classes` to four and set the values for `PATH_TO_BE_CONFIGURED` in the sample file. The `image_resizer`'s size is set to around `300x300`px according to the suggestion from this paper: [Speed/accuracy trade-offs for modern convolutional object detectors](https://arxiv.org/pdf/1611.10012.pdf). 

* Created custom label map that works with our TFRecords. Samples of label map can be found [here](https://github.com/tensorflow/models/tree/master/research/object_detection/data). Here's our label map with four classes:

```
item {
  id: 1
  name: 'Red'
}

item {
  id: 2
  name: 'Yellow'
}

item {
  id: 3
  name: 'Green'
}

item {
  id: 4
  name: 'off'
}
```

* Used pre-trained model checkpoint. Tensorflow provides several pre-trained checkpoint [here](https://github.com/tensorflow/models/blob/master/research/object_detection/g3doc/detection_model_zoo.md).
 
We then trained the model on Google Cloud. 

#### Export the Model

We exported the trained model to a Tensorflow graph proto file and used it for traffic light inference in this project:

* `/data/real_frozen_inference_graph.pb`
* `/data/sim_frozen_inference_graph.pb`

We downloaded the trained checkpoint from Google Cloud and used [the script provided by Tensorflow](https://github.com/tensorflow/models/blob/master/research/object_detection/g3doc/exporting_models.md) to export the model.

Note that we trained two separate models for the simulator and site.

#### Detection Examples

![alt text][image12]

![alt text][image13]

We chose SSD with MobileNet because it provides the best accuracy tradeoff within the fastest detectors. SSD is fast but performs worst with small objects, which is not a concern in our case of traffic light detection. The car only needs to react when it comes to a reasonable distance to a traffic light. Comparisons between different object detectors can be found [here](https://medium.com/@jonathan_hui/object-detection-speed-and-accuracy-comparison-faster-r-cnn-r-fcn-ssd-and-yolo-5425656ae359).


### Project Setup

Please use **one** of the two installation options, either native **or** docker installation.

#### Native Installation

* Be sure that your workstation is running Ubuntu 16.04 Xenial Xerus or Ubuntu 14.04 Trusty Tahir. [Ubuntu downloads can be found here](https://www.ubuntu.com/download/desktop).
* If using a Virtual Machine to install Ubuntu, use the following configuration as minimum:
  * 2 CPU
  * 2 GB system memory
  * 25 GB of free hard drive space

  The Udacity provided virtual machine has ROS and Dataspeed DBW already installed, so you can skip the next two steps if you are using this.

* Follow these instructions to install ROS
  * [ROS Kinetic](http://wiki.ros.org/kinetic/Installation/Ubuntu) if you have Ubuntu 16.04.
  * [ROS Indigo](http://wiki.ros.org/indigo/Installation/Ubuntu) if you have Ubuntu 14.04.
* [Dataspeed DBW](https://bitbucket.org/DataspeedInc/dbw_mkz_ros)
  * Use this option to install the SDK on a workstation that already has ROS installed: [One Line SDK Install (binary)](https://bitbucket.org/DataspeedInc/dbw_mkz_ros/src/81e63fcc335d7b64139d7482017d6a97b405e250/ROS_SETUP.md?fileviewer=file-view-default)
* Download the [Udacity Simulator](https://github.com/udacity/CarND-Capstone/releases).

#### Docker Installation
[Install Docker](https://docs.docker.com/engine/installation/)

Build the docker container
```bash
docker build . -t capstone
```

Run the docker file
```bash
docker run -p 4567:4567 -v $PWD:/capstone -v /tmp/log:/root/.ros/ --rm -it capstone
```

#### Port Forwarding
To set up port forwarding, please refer to the [instructions from term 2](https://classroom.udacity.com/nanodegrees/nd013/parts/40f38239-66b6-46ec-ae68-03afd8a601c8/modules/0949fca6-b379-42af-a919-ee50aa304e6a/lessons/f758c44c-5e40-4e01-93b5-1a82aa4e044f/concepts/16cf4a78-4fc7-49e1-8621-3450ca938b77)

#### Usage

1. Clone the project repository
```bash
git clone https://github.com/udacity/CarND-Capstone.git
```

2. Install python dependencies
```bash
cd CarND-Capstone
pip install -r requirements.txt
```
3. Make and run styx
```bash
cd ros
catkin_make
source devel/setup.sh
roslaunch launch/styx.launch
```
4. Run the simulator

#### Real world testing
1. Download [training bag](https://s3-us-west-1.amazonaws.com/udacity-selfdrivingcar/traffic_light_bag_file.zip) that was recorded on the Udacity self-driving car.
2. Unzip the file
```bash
unzip traffic_light_bag_file.zip
```
3. Play the bag file
```bash
rosbag play -l traffic_light_bag_file/traffic_light_training.bag
```
4. Launch your project in site mode
```bash
cd CarND-Capstone/ros
roslaunch launch/site.launch
```
5. Confirm that traffic light detection works on real life images

### Future Works

* Experiement with Faster R-CNN and reduce the number of proposal to 50. 
* Add support to obstacle detection.
