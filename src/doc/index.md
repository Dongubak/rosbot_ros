# ROSbot ROS2 코드베이스 문서

> Cobra Flex 로봇 적용을 위한 rosbot_ros 분석 문서

---

## 📋 문서 목록

### 개요 및 구조
- [[01_프로젝트_개요]] — 이 프로젝트가 무엇인지, 어떤 로봇을 지원하는지
- [[02_패키지_구조]] — 9개 패키지 각각의 역할과 관계
- [[03_시스템_아키텍처]] — 노드·토픽·TF 전체 흐름도

### 핵심 구성요소
- [[04_하드웨어_인터페이스]] — MCU↔ROS2 통신 (Micro-ROS, ros2_control)
- [[05_센서_통합]] — LiDAR, 카메라, IMU, 거리 센서
- [[06_컨트롤러]] — 구동 컨트롤러, IMU 브로드캐스터, 조이스틱
- [[07_로컬라이제이션]] — EKF 센서 융합 (odometry + IMU)
- [[08_런치_시스템]] — 실제 로봇/시뮬레이션 시작 구조

### 적용 가이드
- [[09_사용_여부_정리]] — Cobra Flex에서 쓰는 것 vs 쓰지 않는 것
- [[10_Cobra_Flex_적용_가이드]] — 수정이 필요한 파일과 방법

### 참고
- [[용어집]] — ROS2, ros2_control, EKF 등 전문 용어 정리

---

## 🤖 우리 로봇 스펙

| 항목 | 내용 |
|------|------|
| 로봇 플랫폼 | Cobra Flex |
| 구동 방식 | 차동 구동 (Differential Drive) |
| LiDAR | RPLidar A2M1 |
| 카메라 | Gemini336 (Orbbec) |
| 매니퓰레이터 | **미사용** |
| 옴니휠 | **미사용** |

---

## 🗂️ 레포지토리 구조 한눈에 보기

```
rosbot_ros/
├── rosbot/                    # 메타패키지 (전체 묶음)
├── rosbot_bringup/            # 실제 로봇 시작 (launch)
├── rosbot_controller/         # ros2_control 컨트롤러 설정
├── rosbot_description/        # URDF/xacro 로봇 모델
├── rosbot_gazebo/             # Gazebo 시뮬레이션
├── rosbot_hardware_interfaces/# C++ 하드웨어 인터페이스
├── rosbot_joy/                # 조이스틱 조종
├── rosbot_localization/       # EKF 위치 추정
└── rosbot_utils/              # 유틸리티 (펌웨어, 필터)
```
