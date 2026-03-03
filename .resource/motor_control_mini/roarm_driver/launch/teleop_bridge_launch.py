import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    config = os.path.join(
        get_package_share_directory("roarm_driver"), "config", "roarm.yaml"
    )

    return LaunchDescription(
        [
            Node(
                package="roarm_driver",
                executable="teleop_bridge",
                name="teleop_bridge",
                parameters=[config],
                output="screen",
            ),
        ]
    )
