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

### 🐳 젠킨스 설치 및 실행 가이드 (Recommended Jenkins Setup)
젠킨스를 Docker 컨테이너로 실행할 경우, 파이프라인이 정상 작동하기 위해 **Docker Socket** 공유가 필요합니다. 아래 명령어를 참고하세요.

```bash
docker run -d -p 8280:8080 -p 50000:50000 --name jenkins \
  -v jenkins_home:/var/jenkins_home \
  -v /var/run/docker.sock:/var/run/docker.sock \
  jenkins/jenkins:lts
```
*(Windows PowerShell 사용 시 줄바꿈 문자 `\` 대신 `` ` ``를 사용하세요)*

**옵션 설명 (`-v`):**
* `-v jenkins_home:/var/jenkins_home`: 젠킨스의 데이터(설정, 빌드 로그 등)를 호스트 볼륨에 저장하여, 컨테이너가 삭제되어도 데이터가 유지되도록 합니다.
* `-v /var/run/docker.sock:/var/run/docker.sock`: **(필수)** 젠킨스 컨테이너 내부에서 **호스트의 Docker 데몬**을 직접 제어할 수 있도록 연결합니다. 이 설정이 있어야 젠킨스 파이프라인이 `docker build` 명령을 수행할 수 있습니다.

**⚠️ 권한 설정 (Permission)**
젠킨스 컨테이너가 호스트의 Docker 소켓에 접근할 수 있도록, 호스트 머신에서 아래 명령어로 권한을 허용해야 합니다 (Linux/Mac 환경).
```bash
sudo chmod 666 /var/run/docker.sock
```
        
## 📝 사용 방법 (How to Use)
1. **설정**: 이 리포지토리의 파일들을 **Mendix 프로젝트 폴더 내**에 복사하거나 클론합니다.
2. **MDA 준비**: Mendix Business Modeler에서 프로젝트를 빌드하여 배포 패키지(.mda)를 생성합니다.
3. **파일 배치**: 생성된 `.mda` 파일을 **`build-source`** 폴더 안에 넣어주세요.
    * Jenkins 파이프라인은 이 폴더에 있는 `.mda` 파일을 가져와서 도커 이미지를 빌드합니다.
    * *참고: `build-source` 폴더가 없다면 생성해 주세요.*

## 🔒 폐쇄망(Air-gapped) 환경 가이드

인터넷이 차단된 폐쇄망 환경에서 구축할 때의 가이드라인입니다.

### 외부 빌드 후 이미지 반입
인터넷이 가능한 외부 환경에서 빌드를 완료하고, 최종 이미지만 폐쇄망으로 반입하는 방식입니다. 가장 간단하고 권장되는 방법입니다.

1.  **외부망 작업**:
    *   소스 코드와 `.mda` 파일을 준비합니다.
    *   `docker build` 명령어로 Mendix App 이미지를 생성합니다.
    *   `docker save -o mendix-app.tar <image-name>` 명령어로 이미지를 파일로 저장합니다.
2.  **반입 및 배포**:
    *   `mendix-app.tar` 파일을 폐쇄망 서버로 복사합니다.
    *   `docker load -i mendix-app.tar` 명령어로 이미지를 로드합니다.
    *   `docker-compose up -d`로 컨테이너를 실행합니다.

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

### 🐳 Jenkins Setup Guide
When running Jenkins in a Docker container, you must share the **Docker Socket** for the pipeline to work. Use the following command:

```bash
docker run -d -p 8280:8080 -p 50000:50000 --name jenkins \
  -v jenkins_home:/var/jenkins_home \
  -v /var/run/docker.sock:/var/run/docker.sock \
  jenkins/jenkins:lts
```

**Option Explanation (`-v`):**
* `-v jenkins_home:/var/jenkins_home`: Persists Jenkins data (configs, build logs) to a host volume so data is not lost when the container is removed.
* `-v /var/run/docker.sock:/var/run/docker.sock`: **(Required)** Mounts the host's Docker socket into the connection. This allows Jenkins to run `docker build` commands using the host's Docker daemon.

**⚠️ Permission Setup**
To allow the Jenkins container to access the host's Docker socket, you may need to adjust permissions on the host machine (Linux/Mac):
```bash
sudo chmod 666 /var/run/docker.sock
```

## 📝 How to Use
1. **Setup**: Copy or clone the files from this repository **into your Mendix project folder**.
2. **Prepare MDA**: Build your project in Mendix Business Modeler to create a deployment package (.mda).
3. **Place File**: Put the generated `.mda` file inside the **`build-source`** folder.
    * The Jenkins pipeline will pick up the `.mda` file from this folder to build the Docker image.
    * *Note: Please create the `build-source` folder if it does not exist.*

## 🔒 Air-gapped Environment Guide

Guidelines for setting up within an air-gapped environment where internet access is restricted.

### Strategy 1: Build Outside, Deploy Inside (Recommended)
Build the image in an environment with internet access and transfer only the final image. This is the simplest and recommended method.

1.  **External tasks**:
    *   Prepare source code and `.mda` file.
    *   Build Mendix App image using `docker build`.
    *   Save image to file using `docker save -o mendix-app.tar <image-name>`.
2.  **Import and Deploy**:
    *   Copy `mendix-app.tar` to the air-gapped server.
    *   Load image using `docker load -i mendix-app.tar`.
    *   Run containers using `docker-compose up -d`.

### Strategy 2: Build Inside
When Jenkins needs to build source code directly inside the air-gapped environment.

1.  **Prerequisites (Download Externally)**:
    *   **Jenkins Image**: Prepare a custom Jenkins image with required plugins (Blue Ocean, Git, Docker Pipeline, etc.) pre-installed.
    *   **Mendix Buildpack Images**: Pre-build `mendix-rootfs:builder` and `mendix-rootfs:app` images externally and import them. (Use `rootfs-builder.dockerfile`, `rootfs-app.dockerfile`)
    *   **Binary Files**: Pre-download `Mendix Runtime (.tar.gz)` and `Java SDK` files and place them in an internal file server or cache directory.
2.  **Docker Build Config**:
    *   Update `Dockerfile` to reference internal resources (local cache or internal mirror) instead of external internet.
