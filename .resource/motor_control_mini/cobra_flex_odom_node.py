#!/usr/bin/env python3
"""
Cobra Flex Odometry Node
========================
HTTP GET으로 모터 컨트롤러에서 인코더 값을 읽어
/odometry/wheels 토픽(nav_msgs/Odometry)으로 발행한다.

통신 형식:
  요청: GET http://{controller_ip}/js?json={"T":130}
  응답: {"T":1001,"M1":0,"M2":0,"M3":0,"M4":0,"odl":<left>,"odr":<right>,"v":<val>}

실행 방법:
  source /opt/ros/humble/setup.bash
  python3 cobra_flex_odom_node.py

파라미터 (ros2 run 또는 --ros-args 로 override 가능):
  controller_ip    (str)   : 모터 컨트롤러 IP  [기본: 192.168.0.44]
  wheel_separation (float) : 좌우 바퀴 중심 간격 m  [기본: 0.153]
  ticks_to_meter   (float) : 1 tick → m 변환 계수  [기본: 0.001 = 1mm]
  publish_rate     (float) : 발행 주기 Hz  [기본: 30.0]
  odom_frame_id    (str)   : 오도메트리 프레임  [기본: odom]
  base_frame_id    (str)   : 로봇 기준 프레임  [기본: base_link]
  publish_tf       (bool)  : odom→base_link TF 발행 여부  [기본: true]

⚠️  ticks_to_meter 교정 필요:
  - 로봇을 정확히 1m 직진 후 odl/odr 델타 값 확인
  - ticks_to_meter = 1.0 / 델타_값
  - 예: 1m 직진 시 delta_odl=1000 → ticks_to_meter = 0.001
"""

import math
import json

import requests
import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Quaternion, TransformStamped
from tf2_ros import TransformBroadcaster


def yaw_to_quaternion(yaw: float) -> Quaternion:
    """Z축 기준 yaw(rad) → Quaternion 변환"""
    q = Quaternion()
    q.x = 0.0
    q.y = 0.0
    q.z = math.sin(yaw / 2.0)
    q.w = math.cos(yaw / 2.0)
    return q


class CobraFlexOdomNode(Node):

    def __init__(self):
        super().__init__('cobra_flex_odom')

        # ── 파라미터 선언 ──────────────────────────────────────────
        self.declare_parameter('controller_ip',    '192.168.0.44')
        self.declare_parameter('wheel_separation',  0.153)   # m, 좌우 바퀴 중심 간격
        self.declare_parameter('ticks_to_meter',    0.001)   # ⚠️ 교정 필요
        self.declare_parameter('publish_rate',     30.0)     # Hz
        self.declare_parameter('odom_frame_id',   'odom')
        self.declare_parameter('base_frame_id',   'base_link')
        self.declare_parameter('publish_tf',        True)

        # ── 파라미터 읽기 ──────────────────────────────────────────
        ip               = self.get_parameter('controller_ip').value
        self.wheel_sep   = self.get_parameter('wheel_separation').value
        self.tick2m      = self.get_parameter('ticks_to_meter').value
        rate_hz          = self.get_parameter('publish_rate').value
        self.odom_frame  = self.get_parameter('odom_frame_id').value
        self.base_frame  = self.get_parameter('base_frame_id').value
        self.do_tf       = self.get_parameter('publish_tf').value

        # HTTP 세션 (연결 재사용으로 오버헤드 감소)
        self.session  = requests.Session()
        self.base_url = f'http://{ip}/js'
        # 30Hz 주기(33ms) 내에 완료되도록 타임아웃 설정
        self.http_timeout = min(0.025, 0.8 / rate_hz)

        # ── 오도메트리 상태 ────────────────────────────────────────
        self.x      = 0.0
        self.y      = 0.0
        self.theta  = 0.0
        self.prev_odl = None  # 이전 프레임 인코더 값 (None = 미초기화)
        self.prev_odr = None

        # ── 발행자 / TF ────────────────────────────────────────────
        self.odom_pub = self.create_publisher(Odometry, '/odometry/wheels', 10)
        self.tf_broadcaster = TransformBroadcaster(self) if self.do_tf else None

        # ── 타이머 ────────────────────────────────────────────────
        self.dt = 1.0 / rate_hz
        self.timer = self.create_timer(self.dt, self._timer_cb)

        self.get_logger().info(
            f'cobra_flex_odom 시작\n'
            f'  controller  : {ip}\n'
            f'  wheel_sep   : {self.wheel_sep} m\n'
            f'  ticks_to_m  : {self.tick2m}  (⚠️ 교정 필요)\n'
            f'  rate        : {rate_hz} Hz\n'
            f'  publish_tf  : {self.do_tf}'
        )

    # ── HTTP 요청 ──────────────────────────────────────────────────

    def _fetch(self) -> dict | None:
        """{"T":130} 전송 후 인코더 응답 반환. 실패 시 None."""
        try:
            resp = self.session.get(
                self.base_url,
                params={'json': json.dumps({'T': 130})},
                timeout=self.http_timeout,
            )
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.Timeout:
            self.get_logger().warn(
                'HTTP 타임아웃 — 프레임 스킵', throttle_duration_sec=2.0)
        except requests.exceptions.ConnectionError:
            self.get_logger().error(
                f'컨트롤러({self.base_url}) 연결 실패', throttle_duration_sec=5.0)
        except Exception as e:
            self.get_logger().warn(f'HTTP 오류: {e}', throttle_duration_sec=2.0)
        return None

    # ── 타이머 콜백 ────────────────────────────────────────────────

    def _timer_cb(self):
        data = self._fetch()
        if data is None:
            return

        odl = data.get('odl')
        odr = data.get('odr')
        if odl is None or odr is None:
            self.get_logger().warn(
                f'odl/odr 필드 누락 — 응답: {data}', throttle_duration_sec=5.0)
            return

        # 첫 수신: 기준값 설정 후 종료 (델타 없음)
        if self.prev_odl is None:
            self.prev_odl = odl
            self.prev_odr = odr
            self.get_logger().info(f'초기 인코더값  odl={odl}, odr={odr}')
            return

        # ── 인코더 델타 → 이동 거리 ───────────────────────────────
        dl = (odl - self.prev_odl) * self.tick2m  # 왼쪽 이동 거리 m
        dr = (odr - self.prev_odr) * self.tick2m  # 오른쪽 이동 거리 m
        self.prev_odl = odl
        self.prev_odr = odr

        # ── 차동 구동 운동학 ───────────────────────────────────────
        d_center = (dl + dr) / 2.0
        d_theta  = (dr - dl) / self.wheel_sep

        # 중간 각도 기준으로 위치 업데이트 (정확도 향상)
        mid_theta = self.theta + d_theta / 2.0
        self.x     += d_center * math.cos(mid_theta)
        self.y     += d_center * math.sin(mid_theta)
        self.theta += d_theta

        # theta 정규화 [-π, π]
        self.theta = math.atan2(math.sin(self.theta), math.cos(self.theta))

        # ── 속도 계산 (dt 기준) ────────────────────────────────────
        vx = d_center / self.dt
        wz = d_theta  / self.dt

        # ── 메시지 발행 ────────────────────────────────────────────
        now = self.get_clock().now().to_msg()
        q   = yaw_to_quaternion(self.theta)

        odom = Odometry()
        odom.header.stamp    = now
        odom.header.frame_id = self.odom_frame
        odom.child_frame_id  = self.base_frame

        odom.pose.pose.position.x    = self.x
        odom.pose.pose.position.y    = self.y
        odom.pose.pose.position.z    = 0.0
        odom.pose.pose.orientation   = q

        odom.twist.twist.linear.x    = vx
        odom.twist.twist.angular.z   = wz

        # 공분산 — 대각 행렬, 보정 전 큰 값 사용
        # [x, y, z, roll, pitch, yaw] 순서
        odom.pose.covariance[0]  = 0.1   # x
        odom.pose.covariance[7]  = 0.1   # y
        odom.pose.covariance[35] = 0.2   # yaw
        odom.twist.covariance[0]  = 0.1  # vx
        odom.twist.covariance[35] = 0.2  # wz

        self.odom_pub.publish(odom)

        # ── TF 발행 (odom → base_link) ────────────────────────────
        if self.tf_broadcaster is not None:
            tf = TransformStamped()
            tf.header.stamp            = now
            tf.header.frame_id         = self.odom_frame
            tf.child_frame_id          = self.base_frame
            tf.transform.translation.x = self.x
            tf.transform.translation.y = self.y
            tf.transform.translation.z = 0.0
            tf.transform.rotation      = q
            self.tf_broadcaster.sendTransform(tf)


def main(args=None):
    rclpy.init(args=args)
    node = CobraFlexOdomNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
