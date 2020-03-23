#!/usr/bin/env python

#  Raymond Kirk (Tunstill) Copyright (c) 2020
#  Email: ray.tunstill@gmail.com
import pickle

import cv2
import geometry_msgs
import ros_numpy
import rospy
from geometry_msgs.msg import Pose
from sensor_msgs.msg import Image, CameraInfo
from std_msgs.msg import String
import tf2_ros
from rasberry_perception.detection.compat import input


def __main():
    import pathlib
    pico_root = (pathlib.Path(__file__).parent / "pico_2019_10_11").resolve()

    if not pico_root.is_dir():
        raise ValueError("Request the download of sequence 0 from Raymond "
                         "http://lcas.lincoln.ac.uk/owncloud/index.php/s/PYEccW0yWvZaSz4/download")

    files = sorted(list(str(s) for s in pico_root.glob("*.pkl")))

    fps = 10
    seconds_limit = 10
    repeat_frames = 1
    warmup_frames = 1
    actual_seconds = (seconds_limit * repeat_frames) + ((warmup_frames - 1) / fps)
    frame_limit = int(fps * seconds_limit)
    assert frame_limit > 0
    print("Truncating files array (n={}) to {} seconds (n={}) for {} fps".format(len(files), actual_seconds, frame_limit,
                                                                                 fps))
    files = files[:frame_limit]

    ram_files = []
    print("Loading files into RAM")
    from tqdm import tqdm

    for file in tqdm(files):
        with open(file, "r") as fh:
            data = pickle.load(fh)
        ram_files.append(data)
        # if len(ram_files) > 5:
        #     break

    rospy.init_node("sequence_0_publisher", anonymous=True)
    hz = rospy.Rate(fps)

    republish_namespace = "sequence_0/"
    image_pub = rospy.Publisher(republish_namespace + "colour/image_raw", Image, queue_size=1)
    image_info_pub = rospy.Publisher(republish_namespace + "colour/camera_info", CameraInfo, queue_size=1)
    depth_pub = rospy.Publisher(republish_namespace + "depth/image_raw", Image, queue_size=1)
    depth_map_pub = rospy.Publisher(republish_namespace + "depth/cmap_raw", Image, queue_size=1)
    depth_info_pub = rospy.Publisher(republish_namespace + "depth/camera_info", CameraInfo, queue_size=1)
    robot_position = rospy.Publisher(republish_namespace + "robot/pose", Pose, queue_size=1)
    sequence_starts = rospy.Publisher(republish_namespace + "info", String, queue_size=1)
    current_node = rospy.Publisher(republish_namespace + "current_node", String, queue_size=1)

    # Static pico frame publisher
    broadcaster = tf2_ros.StaticTransformBroadcaster()
    static_transformStamped = geometry_msgs.msg.TransformStamped()
    static_transformStamped.header.stamp = rospy.Time.now()
    static_transformStamped.header.frame_id = "map"
    static_transformStamped.child_frame_id = "pico_zense_frame"
    static_transformStamped.transform.rotation.w = 1.0
    broadcaster.sendTransform(static_transformStamped)
    static_transformStamped.header.frame_id = "pico_zense_frame"
    static_transformStamped.child_frame_id = "pico_zense_colour_frame"
    broadcaster.sendTransform(static_transformStamped)

    from timeit import default_timer as timer
    iteration = 0

    # On iter 0 write the video to file for further validation
    out = None

    while not rospy.is_shutdown():
        print("Running iteration {}".format(iteration))
        sequence_starts.publish(String("Sequence 0, iteration {} starting".format(iteration)))
        input("\nStart? [enter]: ")
        start = timer()

        for frame_idx, data in enumerate(ram_files):
            if rospy.is_shutdown():
                break

            if frame_idx >= frame_limit:
                print("Reached frame limit {}>={} for time limit of {} seconds".format(frame_idx, frame_limit,
                                                                                       seconds_limit))
                break

            if iteration == 0 and out is None:
                out = cv2.VideoWriter(str(pico_root.parent / "sequence_0to{}_out{}s.avi".format(frame_limit,
                                                                                                seconds_limit)),
                                      cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'), 10,
                                      (data["rgb"]["image"].width, data["rgb"]["image"].height))
            if iteration == 0:
                out.write(ros_numpy.numpify(data["rgb"]["image"]))

            for _ in range(warmup_frames if frame_idx == 0 else repeat_frames):
                now = rospy.Time.now()
                data["rgb"]["image"].header.stamp = now
                data["aligned_depth_to_rgb"]["image"].header.stamp = now
                data["aligned_depth_to_rgb"]["intrinsics"].header.stamp = now
                data["aligned_depth_to_rgb"]["colourmap"].header.stamp = now
                data["rgb"]["intrinsics"].header.stamp = now

                image_pub.publish(data["rgb"]["image"])
                image_info_pub.publish(data["rgb"]["intrinsics"])
                depth_pub.publish(data["aligned_depth_to_rgb"]["image"])
                depth_info_pub.publish(data["aligned_depth_to_rgb"]["intrinsics"])
                depth_map_pub.publish(data["aligned_depth_to_rgb"]["colourmap"])
                robot_position.publish(data["localisation"]["robot_pose"])
                if data["localisation"]["current_node"] is not None:
                    current_node.publish(data["localisation"]["current_node"])

                hz.sleep()
        print("Iteration {} took {} seconds".format(iteration, timer() - start))
        iteration += 1

    # print(files)


if __name__ == "__main__":
    try:
        __main()
    except KeyboardInterrupt:
        pass