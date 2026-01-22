# Mendix Jenkins Docker Pipeline

[English](#english-version) | [한국어](#korean-version)

<a name="korean-version"></a>
## 📖 프로젝트 개요
이 프로젝트는 **Mendix 애플리케이션**의 지속적 배포(Continuous Deployment, CD)를 자동화하기 위해 구성되었습니다.
Git 리포지토리에 코드가 푸시되면 Jenkins 파이프라인이 트리거되어, Mendix 애플리케이션을 Docker 이미지로 빌드하고 Docker Compose를 통해 배포 환경을 업데이트합니다.

## 🚀 주요 목표
* **자동화된 빌드 및 배포**: 수동 배포 과정을 제거하고 코드 변경 시 자동으로 배포가 이루어지도록 합니다.
* **Docker 컨테이너 활용**: Mendix 애플리케이션을 Docker 컨테이너로 패키징하여 일관된 실행 환경을 보장합니다.
* **Jenkins 파이프라인**: Jenkins를 오케스트레이터로 사용하여 전체 CI/CD 과정을 제어합니다.

## 🛠️ 워크플로우 (Workflow)
전체 배포 과정은 다음과 같은 순서로 진행됩니다:

1.  **Source Code Management**: 개발자가 Git 리포지토리에 코드를 푸시합니다.
2.  **Trigger**: Jenkins가 리포지토리의 변경 사항을 감지합니다 (Webhook 또는 Polling).
3.  **Build**: Jenkins 파이프라인이 Mendix Docker Buildpack을 사용하여 애플리케이션 이미지를 빌드합니다.
    * 빌드팩에 필요한 종속성은 `docker-buildpack` 디렉토리 안의 종속성을 참고하세요.
4.  **Deploy**: 빌드된 이미지를 기반으로 미리 정의된 `docker-compose` 구성을 실행하여 서비스를 배포/재시작합니다.

## 📦 구성 요소
* **Jenkins**: CI/CD 파이프라인 실행 및 관리
* **Mendix Docker Buildpack**: Mendix 모델(.mda)을 실행 가능한 Docker 이미지로 변환
* **Docker & Docker Compose**: 컨테이너 런타임 및 오케스트레이션

## 📋 사전 요구 사항 (Prerequisites)
이 파이프라인을 실행하기 위해 다음 환경이 구성되어 있어야 합니다:
* Jenkins 서버
* Docker 및 Docker Compose가 설치된 호스트
* Mendix 프로젝트 소스 코드

---

<a name="english-version"></a>
# Mendix Jenkins Docker Pipeline (English)

## 📖 Project Overview
This project is configured to automate **Continuous Deployment (CD)** for **Mendix applications**.
When code is pushed to the Git repository, a Jenkins pipeline is triggered to build the Mendix application into a Docker image and deploy it using Docker Compose.

## 🚀 Key Objectives
* **Automated Build and Deployment**: Eliminates manual deployment processes and ensures automatic deployment upon code changes.
* **Docker Container Usage**: Packages Mendix applications into Docker containers to ensure a consistent execution environment.
* **Jenkins Pipeline**: Uses Jenkins as an orchestrator to control the entire CI/CD process.

## 🛠️ Workflow
The entire deployment process proceeds in the following order:

1.  **Source Code Management**: Developers push code to the Git repository.
2.  **Trigger**: Jenkins detects changes in the repository (via Webhook or Polling).
3.  **Build**: The Jenkins pipeline builds the application image using the Mendix Docker Buildpack.
    * Please refer to the dependencies inside the `docker-buildpack` directory for buildpack requirements.
4.  **Deploy**: Based on the built image, predefined `docker-compose` configurations are executed to deploy/restart services.

## 📦 Components
* **Jenkins**: Manages and executes the CI/CD pipeline.
* **Mendix Docker Buildpack**: Converts Mendix models (.mda) into executable Docker images.
* **Docker & Docker Compose**: Container runtime and orchestration.

## 📋 Prerequisites
To run this pipeline, the following environment must be configured:
* Jenkins Server
* Host with Docker and Docker Compose installed
* Mendix Project Source Code
