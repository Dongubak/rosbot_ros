# 10. Cobra Flex 적용 가이드

> [!NOTE] 이 문서의 목적
> rosbot_ros 코드를 Cobra Flex 로봇에 적용하기 위해
> 수정해야 할 파일과 방법을 단계별로 정리한다.

---

## 수정 우선순위 요약

| 우선순위 | 파일/항목 | 이유 |
|---------|----------|------|
| 🔴 필수 | 컨트롤러 파라미터 (바퀴 치수) | 오도메트리 정확도 |
| 🔴 필수 | 로봇 본체 URDF | Cobra Flex 형태 반영 |
| 🔴 필수 | LiDAR URDF + 드라이버 launch | RPLidar A2M1 연결 |
| 🔴 필수 | 레이저 필터 영역 | 자기 인식 오류 방지 |
| 🔴 필수 | MCU 통신 설정 | 하드웨어 인터페이스 |
| 🟡 중요 | 카메라 URDF + 드라이버 launch | Gemini336 연결 |
| 🟡 중요 | EKF 파라미터 | 로컬라이제이션 품질 |
| 🟢 선택 | 조이스틱 매핑 | 조작 편의성 |

---

## 전체 진행 체크리스트

> [!TIP]
> 각 단계의 상세 체크리스트는 해당 섹션에서 확인한다.
> 아래는 전체 진행 상황을 빠르게 파악하기 위한 요약이다.

- [x] **1단계** — 컨트롤러 파라미터 수정 (바퀴 치수 입력)
- [x] **2단계** — 로봇 본체 URDF 작성 (Cobra Flex 형태)
- [ ] **3단계** — LiDAR 통합 (RPLidar A2M1)
- [ ] **4단계** — 레이저 필터 영역 수정
- [ ] **5단계** — 카메라 통합 (Gemini336)
- [ ] **6단계** — MCU 통신 설정
- [ ] **7단계** — EKF 파라미터 확인
- [ ] **8단계** — 조이스틱 매핑 확인
- [ ] **최종 검증** — 전체 시스템 동작 확인

---

## 1단계: 컨트롤러 파라미터 수정

**파일**: `rosbot_controller/config/rosbot/controllers.yaml`

Cobra Flex의 실제 바퀴 치수를 측정하여 입력한다.

```yaml
diff_drive_controller:
  ros__parameters:
    # ⬇️ 아래 두 값을 Cobra Flex 실측값으로 변경
    wheel_separation: 0.186      # ← Cobra Flex 좌우 바퀴 중심 간격 (m)으로 변경
    wheel_radius: 0.0425         # ← Cobra Flex 바퀴 반지름 (m)으로 변경

    # 초기에는 1.0으로 시작, 캘리브레이션 후 조정
    wheel_separation_multiplier: 1.0   # ← 1.0으로 초기화
    left_wheel_radius_multiplier: 1.0  # ← 1.0으로 초기화
    right_wheel_radius_multiplier: 1.0 # ← 1.0으로 초기화
```

### 바퀴 치수 측정 방법

```
wheel_separation = 왼쪽 바퀴 중심 ~ 오른쪽 바퀴 중심 거리 (m)
wheel_radius     = 바퀴 반지름 (지름의 절반) (m)
```

> [!TIP] 측정 팁
> 자를 사용하여 바퀴 접지 중심점 간 거리를 측정한다.
> 타이어 팽창 상태에서 측정 (실제 주행 조건과 동일하게).

### ☑️ 1단계 체크리스트

- [x] 줄자로 **좌우 바퀴 중심 간격** 실측 → 값: `___ m`
- [x] 줄자로 **바퀴 지름** 실측 → 반지름 값: `___ m`
- [x] `controllers.yaml`의 `wheel_separation` 값 수정
- [x] `controllers.yaml`의 `wheel_radius` 값 수정
- [x] 보정 승수 3개 (`wheel_separation_multiplier`, `left/right_wheel_radius_multiplier`) 모두 `1.0`으로 초기화
- [ ] 직진 캘리브레이션: 로봇을 정확히 **1m 직진** 후 `/odometry/wheels`의 x 값이 `~1.0`인지 확인
- [ ] 회전 캘리브레이션: 로봇을 정확히 **360° 회전** 후 `/odometry/wheels`의 yaw가 `~6.28 rad`인지 확인
- [ ] 오차 있으면 승수값 조정 후 재확인

---

## 2단계: 로봇 본체 URDF 작성

> [!NOTE] 현재 상태
> `.cobra_flex/robot_core.xacro`를 기반으로 아래 파일들이 이미 작성되어 있다.
> 바퀴 이름 변환, ros2_control 추가, IMU 링크 추가 등이 적용된 상태.
> **파일 내 `⚠️ TODO` 주석을 찾아 실측값으로 채우는 것이 주요 작업이다.**

### 생성된 파일 구조

```
rosbot_description/urdf/cobra_flex/
├── cobra_flex.urdf.xacro    ← 최상위 (xacro 인자, include만)
├── body.urdf.xacro          ← 본체·바퀴·센서 링크/조인트  ← TODO 있음
├── ros2_control.urdf.xacro  ← ros2_control + Gazebo 플러그인  ← TODO 있음
├── wheel.urdf.xacro         ← (비어있음, 향후 확장용)
└── components.urdf.xacro    ← (비어있음, 향후 확장용)
```

### 원본 → 변환된 주요 변경 사항

| 항목 | 원본 (`.cobra_flex/`) | 변환 후 (`cobra_flex/`) |
|------|----------------------|------------------------|
| 바퀴 이름 | `left_front_wheel_joint` | `fl_wheel_joint` (rosbot_ros 규약) |
| 바퀴 부모 링크 | `chassis` | `base_link` (직접 연결) |
| LiDAR 링크 이름 | `laser_frame` | `lidar_link` |
| ros2_control | ❌ 없음 | ✅ 추가됨 |
| IMU 링크 | ❌ 없음 | ✅ 추가됨 (위치 TODO) |
| 카메라 광학 프레임 | ❌ 없음 | ✅ `camera_optical_link` 추가 |
| Gazebo 플러그인 | 구식 `libgazebo_ros_diff_drive` | ros2_control 연동 방식 |
| 하드웨어/시뮬 분기 | ❌ 없음 | ✅ `use_sim` 조건부 분기 |

### wheel_separation 계산 결과

원본 치수(`robot_core.xacro`)에서 base_link 기준 바퀴 y 위치 계산:
```
wheel_y_offset = chassis_y/2 + base_link_to_wheel_y + wheel_width/2
               = 0.053     + 0.0235              + 0.010        = 0.0865 m

wheel_separation = 2 × wheel_y_offset = 0.173 m
```

> [!IMPORTANT] controllers.yaml 동기화 필요
> `controllers.yaml`의 `wheel_separation: 0.186` (ROSbot 기본값)을
> **`0.173`으로 수정**해야 한다. (실측 캘리브레이션 후 최종 확인)

### ☑️ 2단계 체크리스트

#### 파일 존재 확인
- [x] `rosbot_description/urdf/cobra_flex/cobra_flex.urdf.xacro` 생성됨
- [x] `rosbot_description/urdf/cobra_flex/body.urdf.xacro` 생성됨
- [x] `rosbot_description/urdf/cobra_flex/ros2_control.urdf.xacro` 생성됨

#### body.urdf.xacro — TODO 항목 처리 (파일에서 `⚠️ TODO` 검색)
- [x] **IMU 장착 위치** 실측 후 `imu_x`, `imu_y`, `imu_z` property 수정
  - 측정 기준: base_link 원점 (4바퀴 접지 중심, 바닥 위 `wheel_radius=0.03725m` 높이)
  - 현재 임시값 `0 0 0` → 실측값으로 변경 필요
- [x] **IMU 장착 방향** 확인: IMU x축 = 로봇 전방, z축 = 상방인지 확인
  - 방향이 다르면 `imu_rpy` property 수정 (예: 뒤집혔으면 `"0 ${pi} 0"`)
- [x] **LiDAR 장착 위치** 실측 확인 (현재값: `x=0.039688`, `z=0.1468`)
  - 원본 robot_core.xacro에서 계산된 값 — 실측 후 차이 있으면 수정
- [x] **카메라 장착 위치** 실측 확인 (현재값: `x=0.128658`, `z=0.0726962`)
- [x] **섀시 질량** 수정: 현재 `0.8 kg` → 저울로 실측 (배터리 포함 여부 확인)
- [x] **바퀴 질량** 수정: 현재 `0.1 kg` → 바퀴 1개 무게 측정
- [x] **카메라 질량** 수정: 현재 `0.05 kg` → Gemini336 데이터시트 확인

#### ros2_control.urdf.xacro — TODO 항목 처리
- [x] **Gazebo 버전** 확인: Classic / Ignition(Fortress/Garden) 중 어느 것?
  - Classic 사용 시: 현재 코드 그대로 사용 가능
  - Ignition 사용 시: `gazebo_ros2_control/GazeboSystem` → `gz_ros2_control/GazeboSimSystem`
- [ ] **하드웨어 플러그인** 결정: ROSbot 인터페이스 재사용 vs Cobra Flex 전용 드라이버

#### controllers.yaml 동기화
- [x] `wheel_separation: 0.173` 으로 수정 (계산값, 실측 캘리브레이션 후 미세 조정)
- [x] `wheel_radius: 0.03725` 으로 수정 (= 0.0745 / 2)
- [ ] 보정 승수는 일단 `1.0` 유지 → 캘리브레이션 후 조정

#### 파싱 검증
- [ ] xacro 파싱 오류 없는지 확인
  ```bash
  ros2 run xacro xacro \
    $(ros2 pkg prefix rosbot_description)/share/rosbot_description/urdf/cobra_flex/cobra_flex.urdf.xacro
  ```
- [ ] 출력된 URDF에서 `fl_wheel_joint`, `fr_wheel_joint`, `rl_wheel_joint`, `rr_wheel_joint` 4개 존재 확인
- [ ] 출력된 URDF에서 `ros2_control` 블록이 존재하는지 확인

#### RViz 시각화 검증
- [ ] robot_state_publisher 실행하여 RViz에서 로봇 형태 확인
  ```bash
  # 워크스페이스 빌드 후
  colcon build --packages-select rosbot_description
  source install/setup.bash
  ros2 launch rosbot_description load_urdf.launch.py robot_model:=cobra_flex
  ```
  > ⚠️ `load_urdf.launch.py`에 `cobra_flex` 모델 지원 여부 확인 필요 (아래 참고)

- [ ] RViz에서 아래 TF 구조가 올바르게 표시되는지 확인
  ```
  base_footprint
  └── base_link
      ├── chassis
      ├── fl_wheel_link  (앞 왼쪽)
      ├── fr_wheel_link  (앞 오른쪽)
      ├── rl_wheel_link  (뒤 왼쪽)
      ├── rr_wheel_link  (뒤 오른쪽)
      ├── imu_link
      ├── lidar_link
      └── camera_link
          └── camera_optical_link
  ```
- [ ] `ros2 run tf2_tools view_frames` 로 frames.pdf 생성 후 구조 확인
- [ ] base_link → lidar_link 변환 수치 확인
  ```bash
  ros2 run tf2_ros tf2_echo base_link lidar_link
  # 기대값: translation: x=0.039688, z=0.1468
  ```

#### load_urdf.launch.py 수정 (필요 시)
`rosbot_description/launch/load_urdf.launch.py`가 `cobra_flex` 모델명을 지원하는지 확인:
```bash
# launch 파일에서 robot_model 처리 방식 확인
grep -n "robot_model\|urdf" \
  $(ros2 pkg prefix rosbot_description)/share/rosbot_description/launch/load_urdf.launch.py
```
`cobra_flex` 모델이 지원되지 않으면 launch 파일에 경로 분기를 추가해야 한다.

---

## 3단계: LiDAR 통합 (RPLidar A2M1)

### 방법 A: rplidar_ros 패키지 직접 사용 (권장)

`rosbot_bringup/launch/bringup.launch.py`에 LiDAR 실행 추가:

```python
# bringup.launch.py에 추가
IncludeLaunchDescription(
    PythonLaunchDescriptionSource([
        PathJoinSubstitution([
            FindPackageShare('rplidar_ros'),
            'launch', 'rplidar_a2m1_launch.py'
        ])
    ]),
    launch_arguments={
        'serial_port': '/dev/ttyUSB0',   # 실제 포트 확인 필요
        'frame_id': 'lidar_link',         # URDF에서 정의한 프레임 ID와 일치해야 함
        'topic_name': '/scan',
    }.items()
)
```

패키지 설치:
```bash
sudo apt install ros-humble-rplidar-ros
```

### 방법 B: 별도 launch 파일 생성

```python
# rosbot_bringup/launch/lidar.launch.py 새로 생성
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='rplidar_ros',
            executable='rplidar_node',
            name='rplidar_node',
            parameters=[{
                'serial_port': '/dev/ttyUSB0',
                'serial_baudrate': 115200,
                'frame_id': 'lidar_link',
                'angle_compensate': True,
                'scan_mode': 'Standard',
            }],
            remappings=[('scan', '/scan')]
        )
    ])
```

> [!IMPORTANT]
> `frame_id: 'lidar_link'`이 URDF에서 정의한 LiDAR 링크 이름과 반드시 일치해야 한다.

### ☑️ 3단계 체크리스트

#### 하드웨어 준비
- [ ] RPLidar A2M1을 USB로 PC에 연결
- [ ] `ls /dev/ttyUSB*` 또는 `ls /dev/ttyACM*`으로 **포트 이름 확인** → `___`
- [ ] `sudo chmod 666 /dev/ttyUSB0` (또는 해당 포트)로 권한 부여
- [ ] 영구 권한 설정: udev 규칙 추가 또는 사용자를 `dialout` 그룹에 추가
  ```bash
  sudo usermod -aG dialout $USER
  ```

#### 패키지 설치
- [ ] `ros-humble-rplidar-ros` 패키지 설치 확인
  ```bash
  ros2 pkg list | grep rplidar
  ```

#### Launch 파일 수정
- [ ] `bringup.launch.py`에 LiDAR launch include 추가 (방법 A 또는 B 선택)
- [ ] `serial_port` 파라미터를 실제 포트로 수정
- [ ] `frame_id`가 URDF의 `lidar_link`와 일치하는지 확인
- [ ] `topic_name`이 `/scan`으로 설정되어 있는지 확인

#### 동작 검증
- [ ] LiDAR 노드 단독 실행 후 `/scan` 토픽 수신 확인
  ```bash
  ros2 topic hz /scan
  # 기대값: ~10Hz
  ```
- [ ] 스캔 데이터 내용 확인 (range 값이 유효한 범위인지)
  ```bash
  ros2 topic echo /scan --once
  ```
- [ ] RViz에서 `LaserScan` 타입으로 `/scan` 시각화 — 주변 환경이 올바르게 보이는지 확인
- [ ] LiDAR 회전 방향이 올바른지 확인 (앞쪽이 RViz에서 앞쪽에 표시되어야 함)
  - 거꾸로라면 URDF의 lidar_joint에 `rpy="0 0 3.14159"` 추가

---

## 4단계: 레이저 필터 영역 수정

**파일**: `rosbot_utils/config/rosbot/laser_filter.yaml`

Cobra Flex의 실제 크기에 맞게 박스 영역 조정:

```yaml
laser_scan_filters:
  - name: LaserScanBoxFilter
    params:
      # ⬇️ Cobra Flex 크기에 맞게 수정 (단위: m, base_link 기준)
      max_x: 0.XX    # 로봇 앞쪽 끝까지 거리 + 여유 5cm (양수)
      min_x: -0.XX   # 로봇 뒤쪽 끝까지 거리 + 여유 5cm (음수)
      max_y: 0.XX    # 로봇 오른쪽 끝까지 거리 + 여유 5cm (양수)
      min_y: -0.XX   # 로봇 왼쪽 끝까지 거리 + 여유 5cm (음수)
      max_z: 0.XX    # LiDAR 장착 높이 + 여유 (양수)
      min_z: 0.0     # 바닥 기준
```

> [!TIP] 측정 방법
> base_link 기준으로 로봇의 앞/뒤/좌/우 끝점까지 거리를 측정한다.
> 여유(margin)를 5cm 정도 추가하여 로봇 본체가 확실히 필터링되도록 한다.
> 너무 크게 설정하면 가까운 실제 장애물이 무시될 수 있다.

### ☑️ 4단계 체크리스트

#### 치수 측정
- [ ] base_link에서 **앞쪽 끝**까지 거리 측정 → `___ m` (+ 여유 0.05m)
- [ ] base_link에서 **뒤쪽 끝**까지 거리 측정 → `___ m` (+ 여유 0.05m)
- [ ] base_link에서 **좌측 끝**까지 거리 측정 → `___ m` (+ 여유 0.05m)
- [ ] base_link에서 **우측 끝**까지 거리 측정 → `___ m` (+ 여유 0.05m)
- [ ] **LiDAR 장착 높이** (바닥 기준) 확인 → `___ m` (+ 여유 0.03m)

#### 파일 수정
- [ ] `laser_filter.yaml`의 `max_x` 수정
- [ ] `laser_filter.yaml`의 `min_x` 수정 (음수값)
- [ ] `laser_filter.yaml`의 `max_y` 수정
- [ ] `laser_filter.yaml`의 `min_y` 수정 (음수값)
- [ ] `laser_filter.yaml`의 `max_z` 수정

#### 동작 검증
- [ ] 레이저 필터 노드 실행 후 `/scan_filtered` 토픽 수신 확인
- [ ] RViz에서 `/scan`과 `/scan_filtered`를 **동시에** 시각화
- [ ] `/scan_filtered`에서 **로봇 본체 부분이 제거**되었는지 확인
- [ ] 로봇 외부의 실제 장애물(벽, 물체)은 `/scan_filtered`에 **여전히 보이는지** 확인
- [ ] 필터 영역이 너무 크거나 작으면 `laser_filter.yaml` 재조정

---

## 5단계: 카메라 통합 (Gemini336)

### Orbbec SDK 설치

```bash
# 방법 1: apt 패키지 (가용 시)
sudo apt install ros-humble-orbbec-camera

# 방법 2: 소스 빌드
cd ~/ros2_ws/src
git clone https://github.com/orbbec/OrbbecSDK_ROS2.git
cd ~/ros2_ws
rosdep install --from-paths src --ignore-src -r -y
colcon build --packages-select orbbec_camera
```

### Launch 파일에 카메라 추가

```python
# bringup.launch.py에 추가
IncludeLaunchDescription(
    PythonLaunchDescriptionSource([
        PathJoinSubstitution([
            FindPackageShare('orbbec_camera'),
            'launch', 'gemini_336_launch.py'
        ])
    ]),
    launch_arguments={
        'camera_name': 'camera',
        'depth_registration': 'true',
    }.items()
)
```

### ☑️ 5단계 체크리스트

#### 하드웨어 준비
- [ ] Gemini336 카메라를 USB 3.0 포트에 연결
- [ ] `lsusb`로 카메라가 인식되는지 확인
- [ ] USB 권한 설정 (udev 규칙 — Orbbec SDK README 참고)

#### 패키지 설치
- [ ] OrbbecSDK_ROS2 패키지 설치 (apt 또는 소스 빌드)
- [ ] `ros2 pkg list | grep orbbec`으로 패키지 인식 확인
- [ ] `gemini_336_launch.py` 파일 존재 여부 확인
  ```bash
  find $(ros2 pkg prefix orbbec_camera) -name "*336*"
  ```

#### Launch 파일 수정
- [ ] `bringup.launch.py`에 카메라 launch include 추가
- [ ] `camera_name`이 `camera`로 설정되어 있는지 확인
- [ ] URDF의 `camera_link` 프레임 ID와 카메라 드라이버 설정 일치 확인

#### 동작 검증
- [ ] 카메라 노드 단독 실행 후 토픽 목록 확인
  ```bash
  ros2 topic list | grep camera
  ```
- [ ] 컬러 이미지 수신 확인
  ```bash
  ros2 topic hz /camera/color/image_raw
  ```
- [ ] 뎁스 이미지 수신 확인
  ```bash
  ros2 topic hz /camera/depth/image_raw
  ```
- [ ] RViz에서 `Image` 타입으로 컬러 이미지 시각화 확인
- [ ] TF에서 `camera_link`가 `base_link`에 연결되어 있는지 확인

---

## 6단계: MCU 통신 설정

### Cobra Flex가 Micro-ROS를 사용하는 경우

**파일**: `rosbot_bringup/launch/microros.launch.py`

```python
# 시리얼 포트와 속도를 Cobra Flex에 맞게 수정
Node(
    package='micro_ros_agent',
    executable='micro_ros_agent',
    arguments=['serial', '--dev', '/dev/ttyUSB1', '-b', '115200']
    # 실제 포트와 baud rate로 변경
)
```

### Cobra Flex가 다른 통신 방식을 사용하는 경우

Micro-ROS 대신 직접 ROS2 토픽을 발행하는 드라이버가 있다면:

1. `microros.launch.py`를 사용하지 않는다
2. `rosbot_hardware_interfaces`를 새 하드웨어 인터페이스로 교체한다
3. `bringup.launch.py`에서 Micro-ROS 관련 부분을 제거하고 새 드라이버를 추가한다

> [!NOTE] 하드웨어 인터페이스가 예상하는 토픽 형식
> - `/_motors_cmd`: `std_msgs/Float32MultiArray` — `[rr, rl, fr, fl]` 순서
> - `/_motors_response`: `sensor_msgs/JointState` (4개 바퀴)
> - `~/imu`: `sensor_msgs/Imu`

### ☑️ 6단계 체크리스트

#### MCU 통신 방식 확인
- [ ] Cobra Flex MCU가 **Micro-ROS를 사용하는지** 확인
  - 사용: 아래 Micro-ROS 체크리스트 진행
  - 미사용: 별도 드라이버 방식 확인 필요

#### Micro-ROS 사용 시
- [ ] MCU와 연결되는 **시리얼 포트 확인** → `___`
  ```bash
  ls /dev/ttyUSB* /dev/ttyACM*
  ```
- [ ] MCU의 **Baud Rate 확인** → `___` bps
- [ ] `micro_ros_agent` 패키지 설치 확인
  ```bash
  ros2 pkg list | grep micro_ros
  ```
- [ ] `microros.launch.py`의 포트와 Baud Rate 수정
- [ ] Micro-ROS Agent 단독 실행 후 MCU 연결 확인
  ```bash
  ros2 run micro_ros_agent micro_ros_agent serial --dev /dev/ttyUSB1 -b 115200
  ```
- [ ] Agent 실행 후 `/_motors_response` 토픽이 나타나는지 확인
  ```bash
  ros2 topic list | grep motors
  ```
- [ ] `/_imu/data_raw` 또는 `~/imu` 토픽이 나타나는지 확인

#### 토픽 형식 검증
- [ ] `/_motors_response` 메시지 타입이 `sensor_msgs/JointState`인지 확인
  ```bash
  ros2 topic info /_motors_response
  ```
- [ ] `/_motors_response`에 4개 바퀴 이름이 포함되어 있는지 확인
  ```bash
  ros2 topic echo /_motors_response --once
  ```
- [ ] IMU 토픽 메시지 타입이 `sensor_msgs/Imu`인지 확인

#### 모터 명령 전송 테스트
- [ ] 컨트롤러 실행 후 `/_motors_cmd` 토픽이 발행되는지 확인
- [ ] 조이스틱으로 전진 명령 시 바퀴가 실제로 움직이는지 확인
- [ ] 정지 명령(cmd_vel = 0) 시 즉시 정지하는지 확인

---

## 7단계: EKF 파라미터 확인

**파일**: `rosbot_localization/config/ekf.yaml`

대부분 ROSbot과 동일하게 사용 가능하지만, IMU가 다른 경우 확인 필요:

```yaml
ekf_node:
  ros__parameters:
    frequency: 20.0
    two_d_mode: true

    # 토픽 이름이 실제 발행 토픽과 일치하는지 확인
    odom0: odometry/wheels   # diff_drive_controller 출력
    imu0: imu/data           # imu_sensor_broadcaster 출력
```

### ☑️ 7단계 체크리스트

#### 토픽 이름 확인
- [ ] `diff_drive_controller`가 `odometry/wheels`로 오도메트리를 발행하는지 확인
  ```bash
  ros2 topic list | grep odometry
  ```
- [ ] `imu_sensor_broadcaster`가 `imu/data`로 IMU 데이터를 발행하는지 확인
  ```bash
  ros2 topic hz /imu/data
  # 기대값: ~25Hz 이상
  ```
- [ ] `ekf.yaml`의 `odom0`와 `imu0` 토픽 이름이 실제 발행 토픽과 일치하는지 확인

#### IMU 공분산 확인
- [ ] 사용하는 IMU의 데이터시트에서 자세/각속도/선가속도 오차 스펙 확인
- [ ] ROSbot의 BNO055 기본값(orientation: 1.9e-3, angular_vel: 2.0e-3)을 그대로 쓸 수 없는 경우
  `controllers.yaml`의 `imu_sensor_broadcaster` 공분산 값 수정

#### EKF 동작 검증
- [ ] 전체 시스템 실행 후 `/odometry/filtered` 토픽 수신 확인
  ```bash
  ros2 topic hz /odometry/filtered
  # 기대값: 20Hz
  ```
- [ ] 로봇 정지 상태에서 `/odometry/filtered` x, y 값이 드리프트 없이 안정적인지 확인
- [ ] 직진 1m 후 `/odometry/filtered` x가 `/odometry/wheels` x와 유사한지 확인
- [ ] `ros2 run tf2_tools view_frames`에서 `odom → base_link` 연결이 존재하는지 확인

---

## 8단계: 조이스틱 매핑 확인

**파일**: `rosbot_joy/config/joy.yaml`

```yaml
joy_node:
  ros__parameters:
    device_id: 0
    deadzone: 0.1

teleop_twist_joy_node:
  ros__parameters:
    enable_button: 4       # LB 버튼 (누르고 있어야 이동 가능)
    enable_turbo_button: 5 # RB 버튼 (고속 모드)
    axis_linear:
      x: 1                 # 왼쪽 스틱 상하
    axis_angular:
      yaw: 3               # 오른쪽 스틱 좌우
    scale_linear:
      x: 0.7               # 최대 선속도 (m/s)
    scale_angular:
      yaw: 1.0             # 최대 각속도 (rad/s)
```

### ☑️ 8단계 체크리스트

#### 조이스틱 연결
- [ ] 조이스틱(게임패드)을 USB로 연결
- [ ] `/dev/input/js0` 또는 해당 장치가 인식되는지 확인
  ```bash
  ls /dev/input/js*
  ```
- [ ] `jstest /dev/input/js0`으로 버튼/축 번호 확인

#### 매핑 확인
- [ ] `enable_button` 번호가 실제 사용하는 컨트롤러의 **안전 버튼**에 매핑되어 있는지 확인
- [ ] 전진/후진 축 번호(`axis_linear.x`) 확인
- [ ] 좌/우 회전 축 번호(`axis_angular.yaw`) 확인
- [ ] 최대 선속도(`scale_linear.x`)가 Cobra Flex의 최대 속도를 초과하지 않는지 확인
- [ ] 필요 시 버튼/축 번호 수정

#### 동작 검증
- [ ] `enable_button`을 누른 상태에서 스틱을 움직이면 로봇이 이동하는지 확인
- [ ] `enable_button`을 떼면 로봇이 즉시 멈추는지 확인
- [ ] 전진/후진/좌회전/우회전 방향이 의도한 방향과 일치하는지 확인
  - 반대라면 `scale_linear.x`나 `scale_angular.yaw`를 음수로 변경

---

## 최종 검증

### ☑️ 최종 통합 검증 체크리스트

#### 시스템 시작
- [ ] `ros2 launch rosbot_bringup bringup.launch.py` 실행 시 오류 없이 시작하는지 확인
- [ ] 30초 내에 모든 컨트롤러가 `active` 상태가 되는지 확인
  ```bash
  ros2 control list_controllers
  ```

#### 토픽 확인
- [ ] `/scan` — LiDAR 데이터 수신 확인
- [ ] `/scan_filtered` — 필터링된 LiDAR 데이터 수신 확인
- [ ] `/imu/data` — IMU 데이터 수신 확인
- [ ] `/odometry/wheels` — 바퀴 오도메트리 수신 확인
- [ ] `/odometry/filtered` — EKF 오도메트리 수신 확인
- [ ] `/joint_states` — 관절 상태 수신 확인
- [ ] `/camera/color/image_raw` — 카메라 이미지 수신 확인

#### TF 트리 확인
- [ ] `ros2 run tf2_tools view_frames` 실행 후 frames.pdf 확인
- [ ] `map → odom → base_link` 체인 존재 여부 확인
- [ ] `base_link → lidar_link` 연결 확인
- [ ] `base_link → camera_link` 연결 확인
- [ ] `base_link → imu_link` 연결 확인
- [ ] `base_link → fl/fr/rl/rr_wheel_link` 4개 연결 확인

#### 주행 테스트
- [ ] 조이스틱으로 전진 1m — 오도메트리 x값 확인 (`~1.0`)
- [ ] 조이스틱으로 360° 회전 — 오도메트리 yaw값 확인 (`~6.28 rad`)
- [ ] 직진 중 LiDAR 스캔이 움직임에 따라 정상적으로 업데이트되는지 확인
- [ ] 장애물 앞에서 `/scan_filtered`에 장애물이 감지되는지 확인

#### RViz 종합 시각화
- [ ] RViz 실행 후 다음 항목 동시 시각화 확인:
  - [ ] 로봇 모델 (`RobotModel` 타입, topic: `/robot_description`)
  - [ ] LiDAR 스캔 (`LaserScan` 타입, topic: `/scan_filtered`)
  - [ ] 오도메트리 (`Odometry` 타입, topic: `/odometry/filtered`)
  - [ ] TF 트리 (`TF` 타입)
  - [ ] 카메라 이미지 (`Image` 타입, topic: `/camera/color/image_raw`)

---

## 전체 수정 파일 목록

| 파일 | 수정 내용 | 필수? |
|------|----------|-------|
| `rosbot_controller/config/rosbot/controllers.yaml` | 바퀴 치수 | 🔴 |
| `rosbot_description/urdf/cobra_flex/` (새 폴더) | Cobra Flex URDF | 🔴 |
| `rosbot_bringup/launch/bringup.launch.py` | LiDAR/카메라 launch 추가 | 🔴 |
| `rosbot_bringup/launch/microros.launch.py` | 포트/속도 변경 | 🔴 |
| `rosbot_utils/config/rosbot/laser_filter.yaml` | 풋프린트 영역 | 🔴 |
| `rosbot_localization/config/ekf.yaml` | IMU 파라미터 확인 | 🟡 |
| `rosbot_joy/config/joy.yaml` | 조이스틱 매핑 | 🟢 |

---

- [[09_사용_여부_정리]] — 무엇을 사용하는지 확인
- [[06_컨트롤러]] — 컨트롤러 파라미터 상세
- [[05_센서_통합]] — 센서 연결 방법
- [[용어집]] — 모르는 용어 확인
