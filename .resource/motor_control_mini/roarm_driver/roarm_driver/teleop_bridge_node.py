"""
ROS2 node that subscribes to /cmd_vel (geometry_msgs/Twist)
and forwards commands to RoArm-M2 controller via HTTP.

Twist mapping:
  linear.x  -> X (forward/backward)
  angular.z -> Z (rotation)

Usage:
  ros2 run roarm_driver teleop_bridge
  ros2 run roarm_driver teleop_bridge --ros-args -p controller_ip:=192.168.0.44
"""

import json

import requests
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist


class TeleopBridgeNode(Node):
    def __init__(self):
        super().__init__("teleop_bridge")

        self.declare_parameter("controller_ip", "192.168.0.44")
        self.declare_parameter("cmd_t", 13)
        self.declare_parameter("timeout", 1.0)

        ip = self.get_parameter("controller_ip").value
        self.base_url = f"http://{ip}/js"
        self.cmd_t = self.get_parameter("cmd_t").value
        self.timeout = self.get_parameter("timeout").value

        self.sub = self.create_subscription(Twist, "cmd_vel", self.cmd_vel_cb, 10)
        self.get_logger().info(f"Teleop bridge started -> {self.base_url}")

    def cmd_vel_cb(self, msg: Twist):
        x = round(msg.linear.x, 4)
        z = round(msg.angular.z, 4)

        command = {"T": self.cmd_t, "X": x, "Z": z}
        try:
            resp = requests.get(
                self.base_url,
                params={"json": json.dumps(command)},
                timeout=self.timeout,
            )
            data = resp.json()
            self.get_logger().debug(f"Sent {command} -> {data}")
        except requests.RequestException as e:
            self.get_logger().warn(f"HTTP error: {e}")


def main(args=None):
    rclpy.init(args=args)
    node = TeleopBridgeNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
