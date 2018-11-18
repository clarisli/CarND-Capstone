from styx_msgs.msg import TrafficLight
import tensorflow as tf
import numpy as np
import os
import rospy
import yaml
import cv2


IMAGE_PATH = os.path.dirname(os.path.realpath(__file__)) + '/../../../../test_images/simulator/'
MAX_IMAGE_WIDTH = 300
MAX_IMAGE_HEIGHT = 300

class TLClassifier(object):
    def __init__(self):
        #TODO load classifier
        self.detection_graph = None
        self.classes = {1: TrafficLight.RED,
                        2: TrafficLight.YELLOW,
                        3: TrafficLight.GREEN,
                        4: TrafficLight.UNKNOWN}
        self.image_counter = 0
        self.detection_graph = tf.Graph()
        model_path = self.get_model_path()
        self.load_model(model_path, self.detection_graph)

    def get_model_path(self):
        config_string = rospy.get_param("/traffic_light_config")
        config = yaml.load(config_string)
        return os.path.dirname(os.path.realpath(__file__)) + config['detection_model']

    def load_model(self, model_path, graph):
        with graph.as_default():
            od_graph_def = tf.GraphDef()
            with tf.gfile.GFile(model_path, 'rb') as fid:
                serialized_graph = fid.read()
                od_graph_def.ParseFromString(serialized_graph)
                tf.import_graph_def(od_graph_def, name='')

    def get_classification(self, image):
        """Determines the color of the traffic light in the image

        Args:
            image (cv::Mat): image containing the traffic light

        Returns:
            int: ID of traffic light color (specified in styx_msgs/TrafficLight)

        """
        #TODO implement light color prediction
        image = self.process_image(image)
        light_class, probability = self.predict(image)

        rospy.logdebug("class: %d, probability: %f", light_class, probability)

        return light_class

    def process_image(self, image):
        image = cv2.resize(image, (MAX_IMAGE_WIDTH, MAX_IMAGE_HEIGHT))
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        return image

    def predict(self, image, min_score_thresh=0.5):

        boxes, scores, classes = self.run_inference(image, self.detection_graph)

        for i, box in enumerate(boxes):
            if scores[i] > min_score_thresh:
                light_class = self.classes[classes[i]]
                rospy.logdebug("Traffic light detected: %d, %d" , classes[i], light_class)
                return light_class, scores[i]

        return None, None

    def run_inference(self, image, graph):
        with graph.as_default():
            config = tf.ConfigProto()
            config.graph_options.optimizer_options.global_jit_level = tf.OptimizerOptions.ON_1
            with tf.Session(graph=self.detection_graph, config=config) as sess:

                image_tensor = tf.get_default_graph().get_tensor_by_name('image_tensor:0')
                detection_boxes = tf.get_default_graph().get_tensor_by_name('detection_boxes:0')
                detection_scores = tf.get_default_graph().get_tensor_by_name('detection_scores:0')
                detection_classes = tf.get_default_graph().get_tensor_by_name('detection_classes:0')

                (boxes, scores, classes) = sess.run(
                    [detection_boxes, detection_scores, detection_classes],
                    feed_dict={image_tensor: np.expand_dims(image, axis=0)})

                scores = np.squeeze(scores)
                classes = np.squeeze(classes)
                boxes = np.squeeze(boxes)

        return boxes, scores, classes



