# Mendix Jenkins Docker Pipeline

[English](#english-version) | [한국어](#korean-version)

<a name="korean-version"></a>

<img width="3158" height="1234" alt="Image" src="https://github.com/user-attachments/assets/763c1b6c-2f22-447b-a400-50cf6dd4eb9c" />

## 📖 프로젝트 개요
이 프로젝트는 **Mendix 애플리케이션**의 지속적 배포(CD)를 자동화하기 위한 Jenkins 파이프라인과 Docker 구성을 제공합니다.
Git 리포지토리에 코드가 푸시되면 Jenkins가 트리거되어 Mendix 앱을 빌드하고, Docker Compose를 통해 배포합니다.

---

## 🚀 젠킨스 환경 구축 가이드 (Jenkins Environment Setup)
이 파이프라인은 젠킨스 에이전트 내부에서 `docker` 및 `docker compose` 명령어를 사용합니다.
따라서 젠킨스 환경에 **Docker CLI**와 **Docker Compose Plugin**이 반드시 설치되어 있어야 합니다.

### 1단계: 젠킨스 이미지 준비
공식 `jenkins/jenkins` 이미지에는 도커 도구가 포함되어 있지 않습니다. 아래 두 가지 방법 중 하나를 선택하세요.

#### 🅰️ 방법 A: 커스텀 이미지 만들기 (권장)
이 리포지토리에 포함된 `Dockerfile`을 사용하여 도커 도구(`docker`, `docker compose`)와 권한 설정이 완료된 이미지를 빌드합니다.

```bash
# 리포지토리 루트(Dockerfile이 있는 위치)에서 실행
docker build -t my-jenkins-docker .
```

#### 🅱️ 방법 B: 실행 중인 컨테이너에 설치하기
이미 젠킨스가 실행 중이라면, 컨테이너에 접속하여 직접 설치할 수 있습니다.
```bash
# 1. 젠킨스 컨테이너에 root 권한으로 접속
docker exec -u 0 -it <container_name> bash

# 2. Docker CLI 및 Compose 설치 (위의 Dockerfile 내용과 동일하게 진행)
apt-get update && apt-get install -y lsb-release curl
curl -fsSLo /usr/share/keyrings/docker-archive-keyring.asc https://download.docker.com/linux/debian/gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.asc] \
https://download.docker.com/linux/debian $(lsb_release -cs) stable" > /etc/apt/sources.list.d/docker.list
apt-get update && apt-get install -y docker-ce-cli docker-compose-plugin

# 3. 설치 확인
docker --version
docker compose version
```

### 2단계: 젠킨스 컨테이너 실행
준비된 이미지(`my-jenkins-docker`)를 실행할 때, **호스트의 도커 소켓**을 공유해야 젠킨스가 호스트의 도커를 제어할 수 있습니다.

```bash
# Bash에서 실행
docker run -d -p 8082:8080 -p 50000:50000 --name jenkins \
  -v jenkins_home:/var/jenkins_home \
  -v /var/run/docker.sock:/var/run/docker.sock \
  --group-add $(stat -c '%g' /var/run/docker.sock) \
  my-jenkins-docker
```

```powershell
# PowerShell에서 실행 (Windows Docker Desktop의 경우 group-add 옵션 제외)
docker run -d -p 8082:8080 -p 50000:50000 --name jenkins `
  -v jenkins_home:/var/jenkins_home `
  -v /var/run/docker.sock:/var/run/docker.sock `
  my-jenkins-docker
```

*   `-v /var/run/docker.sock:/var/run/docker.sock`: 호스트의 도커 엔진을 공유합니다.
*   `--group-add $(stat -c '%g' /var/run/docker.sock)`: **(보안 권장)** 컨테이너에 호스트의 도커 그룹 권한을 부여하여 `sudo`나 `chmod 666` 없이도 도커를 사용할 수 있게 합니다.

---

## 📝 사용 방법 (How to Use)

1.  **프로젝트 설정**: 이 리포지토리의 파일들을 Mendix 프로젝트 루트에 복사합니다.
2.  **빌드 소스 준비 (Build Source)**: `build-source` 폴더에 다음 **2가지 구조 중 하나**를 준비합니다. `.mda` 파일이 필수는 아닙니다.
    
    *   **옵션 A: 프로젝트 소스 코드 (추천)**
        *   Mendix 프로젝트 폴더 전체를 넣습니다.
        *   **주의**: `.mpr` 파일이 `build-source` 폴더 바로 아래에 위치해야 합니다.
        ```
        build-source/
        ├── MyProject.mpr   <-- 필수
        ├── javasource/
        ├── resources/
        └── theme/
        ```

    *   **옵션 B: 배포 파일 (.mda)**
        *   이미 빌드된 배포 파일(.mda) 하나만 넣습니다.
        ```
        build-source/
        └── MyProject.mda
        ```
3.  **파이프라인 실행**:
    *   젠킨스에서 'New Item' -> 'Pipeline'을 생성합니다.
    *   'Pipeline script from SCM'을 선택하고 Git 리포지토리를 연결합니다.
    *   **Script Path 설정**:
        *   **Docker Compose 배포**: `Jenkinsfile` (기본값)
        *   **Kubernetes 배포**: `Jenkinsfile.k8s`
    *   'Build Now'를 클릭하여 배포를 시작합니다. (빌드 시 `mendix-app:latest` 태그가 함께 생성됩니다.)

---

## � 환경 변수 및 Mendix 상수 설정 (Environment Variables Configuration)

Docker 배포 시 Mendix 모듈의 **Constant(상수)** 값을 변경하거나 시스템 환경 변수를 설정할 수 있습니다.
보안상 중요한 값(API Key, Password 등)은 Git에 올리지 않고 별도로 관리해야 합니다.

### 1. Mendix 상수 (Constant) 오버라이드
Mendix의 상수는 `MXRUNTIME_` 접두사를 사용하여 환경 변수로 덮어쓸 수 있습니다.
*   **규칙**: `MXRUNTIME_` + `모듈명_상수명` (특수문자 `.`은 `_`로 치환)
*   **예시**: 모듈명 `MyModule`, 상수명 `MyConstant` -> `MXRUNTIME_MyModule_MyConstant`

### 2. `.env` 파일을 이용한 설정 (권장)
`docker-compose.yml` 파일에 직접 값을 입력하는 대신, `.env` 파일을 사용하여 관리하는 것을 권장합니다.

1.  **`.env` 파일 생성**: 프로젝트 루트에 생성하고 `.gitignore`에 추가합니다.
    ```properties
    DB_PASSWORD=MySecurePassword123!
    SMTP_HOST=smtp.gmail.com
    MY_API_KEY=12345
    ```

2.  **`docker-compose.yml` 에서 참조**:
    ```yaml
    services:
      mendixapp:
        image: mendix-app:latest
        environment:
          - ADMIN_PASSWORD=${DB_PASSWORD}
          - MXRUNTIME_MyEmailModule_SMTPServerAddress=${SMTP_HOST}
          - MXRUNTIME_MyModule_MySecretKey=${MY_API_KEY}
    ```

### 3. 컨테이너 내부 쉘에서 확인
실행 중인 컨테이너에 환경 변수가 잘 적용되었는지 확인하는 방법입니다.

```bash
# 1. 컨테이너 접속 (Bash)
docker exec -it <container_name> /bin/bash

# 2. 환경 변수 확인
env | grep MXRUNTIME_
```

---

## ☸️ 쿠버네티스(Kubernetes) 로컬 테스트 가이드 (Local Testing)

`k8s/` 브랜치 또는 폴더에 포함된 매니페스트를 사용하여 로컬 환경(Minikube, Docker Desktop K8s)에서 테스트할 수 있습니다.

### 1. 사전 준비
*   **Kubernetes 활성화**: Docker Desktop 설정에서 Kubernetes를 Enable 하거나, Minikube를 설치합니다.
*   **kubectl 설치**: Kubernetes 클러스터를 제어하기 위한 CLI 도구입니다.

### 2. 이미지 빌드 (로컬)
로컬 K8s는 로컬 도커 이미지를 바로 사용할 수 있습니다 (imagePullPolicy: IfNotPresent).
먼저 이미지를 빌드해 둡니다.

```bash
# Dockerfile이 있는 루트 경로에서 실행
docker build -t mendix-app:latest .
```

### 3. 매니페스트 배포
`k8s/` 폴더의 YAML 파일들을 클러스터에 적용합니다.

```bash
# 네임스페이스 생성 (선택)
kubectl create namespace mendix

# 매니페스트 적용 (-n mendix 옵션은 네임스페이스 사용 시)
kubectl apply -f k8s/postgres.yaml
kubectl apply -f k8s/mendix-app.yaml
```

### 4. 확인 및 접속
```bash
# 파드 상태 확인
kubectl get pods

# 서비스(접속 주소) 확인
kubectl get svc
```
*   **Docker Desktop**: `localhost:8080`으로 접속 가능.
*   **Minikube**: `minikube service mendix-app` 명령어로 URL 확인.

---

## 💾 대용량 MDA 파일 처리 가이드 (Large File Handling)
Mendix 빌드 아티팩트(`.mda`) 용량이 커서 Git에 올리기 어려운 경우, 다음 방법들을 사용하세요.

### 1. Git LFS (Large File Storage) 사용 (추천)
Git의 대용량 파일 확장 기능을 사용하여 `.mda` 파일을 버전 관리합니다.
1.  로컬 및 젠킨스 서버에 **Git LFS**를 설치합니다.
2.  프로젝트에서 LFS 추적 설정: `git lfs track "*.mda"`
3.  평소처럼 커밋 및 푸시하면 자동으로 LFS에 저장됩니다.

### 2. 외부 저장소 다운로드 (S3, Nexus 등)
파일을 별도 파일 서버나 클라우드 스토리지에 올리고, 빌드 시점에 다운로드합니다.
*   **Jenkinsfile 수정 예시**:
    ```groovy
    script {
        // MDA 파일이 없으면 다운로드
        if (!fileExists('docker-buildpack/app.mda')) {
            sh 'curl -o docker-buildpack/app.mda "https://my-storage.com/app-v1.mda"'
        }
    }
    ```

### 3. 수동 복사 (폐쇄망 등)
젠킨스 에이전트의 워크스페이스(`build-source` 폴더)에 직접 파일을 복사해둡니다.

---

## 🔒 폐쇄망(Air-gapped) 환경 가이드

인터넷이 없는 환경에서는 두 가지 전략을 사용할 수 있습니다.

### 전략 1: 외부 빌드 후 이미지 반입 (Build Outside) - 추천
1.  **외부망**: 소스를 빌드하여 `mendix-app` 이미지를 생성 후 파일로 저장 (`docker save`).
2.  **내부망**: 이미지 파일을 로드하고 `docker-compose up`으로 실행.

### 전략 2: 내부 빌드 (Build Inside) - 의존성 오프라인 준비
폐쇄망 내부에서 빌드해야 한다면, 필요한 의존성을 미리 다운로드해야 합니다.

1.  **의존성 다운로드 (외부망)**
    스크립트를 실행하여 Buildpack과 Mendix Runtime을 캐시 폴더에 다운로드합니다.
    ```bash
    # .mpr 파일에서 버전을 자동 감지하여 다운로드
    python3 scripts/download_offline_deps.py --source build-source
    ```

2.  **파일 이동**
    `docker-buildpack/build-cache` 폴더를 폐쇄망 환경의 프로젝트 경로로 그대로 복사합니다.

3.  **빌드**
    Dockerfile이 `build-cache` 폴더를 감지하면 자동으로 로컬 파일을 사용하여 빌드합니다.

---
---

<a name="english-version"></a>
# Mendix Jenkins Docker Pipeline (English)

## 📖 Overview
This project provides a Jenkins pipeline and Docker configuration to automate the **Continuous Deployment (CD)** of **Mendix applications**.

---

## 🚀 Jenkins Environment Setup Guide
This pipeline uses `docker` and `docker compose` commands inside the Jenkins agent.
Therefore, **Docker CLI** and **Docker Compose Plugin** must be installed in the Jenkins environment.

### Step 1: Prepare Jenkins Image
The official `jenkins/jenkins` image does not include Docker tools. Choose one of the following methods.

#### 🅰️ Method A: Build Custom Image (Recommended)
Use the `Dockerfile` included in this repository to build an image with Docker tools (`docker`, `docker compose`) and permissions pre-configured.

```bash
# Run in the repository root (where Dockerfile is located)
docker build -t my-jenkins-docker .
```

#### 🅱️ Method B: Install in Running Container
If Jenkins is already running, access the container and install the tools manually.
```bash
# 1. Access Jenkins container as root
docker exec -u 0 -it <container_name> bash

# 2. Run installation commands (same as Dockerfile above)
# ... (apt-get install docker-ce-cli docker-compose-plugin) ...
```

### Step 2: Run Jenkins Container
When running the image, you must share the **Host Docker Socket**.

```bash
docker run -d -p 8080:8080 -p 50000:50000 --name jenkins \
  -v jenkins_home:/var/jenkins_home \
  -v /var/run/docker.sock:/var/run/docker.sock \
  --group-add $(stat -c '%g' /var/run/docker.sock) \
  my-jenkins-docker
```

*   `-v /var/run/docker.sock:/var/run/docker.sock`: Shares the host's Docker engine.
*   `--group-add ...`: **(Security Best Practice)** Grants the container permissions to access the host's Docker socket without using insecure `chmod 666`.

---

## 📝 How to Use

1.  **Setup**: Copy files from this repository to your Mendix project root.
2.  **Prepare Build Source**: Place one of the **3 supported structures** in the **`build-source` folder**:
    
    *   **Option A: Project Source (Recommended)**
        *   The entire Mendix project folder.
        *   **Note**: The `.mpr` file must be directly inside `build-source`.
        ```
        build-source/
        ├── MyProject.mpr   <-- Required
        ├── javasource/
        ├── resources/
        └── theme/
        ```

    *   **Option B: Package File (.mpk)**
        *   A single Mendix export package (.mpk).
        ```
        build-source/
        └── MyProject.mpk
        ```

    *   **Option C: Diploma File (.mda)**
        *   A pre-built deployment archive (.mda).
        ```
        build-source/
        └── MyProject.mda
        ```
3.  **Run Pipeline**:
    *   Create a new Pipeline job in Jenkins.
    *   Connect your Git repository.
    *   **Set Script Path**:
        *   **Docker Compose Deployment**: `Jenkinsfile` (Default)
        *   **Kubernetes Deployment**: `Jenkinsfile.k8s`
    *   Click 'Build Now'. (The image will be strictly tagged as `mendix-app:latest`.)

---

## 🔧 Configuration of Environment Variables & Mendix Constants

You can override **Mendix Constants** and configure system environment variables for Docker deployments.
Sensitive values (API Keys, Passwords, etc.) should be managed separately and not committed to Git.

### 1. Overriding Mendix Constants
You can override Mendix constants using environment variables with the `MXRUNTIME_` prefix.
*   **Rule**: `MXRUNTIME_` + `ModuleName_ConstantName` (replace `.` with `_`)
*   **Example**: Module `MyModule`, Constant `MyConstant` -> `MXRUNTIME_MyModule_MyConstant`

### 2. Using `.env` Files (Recommended)
Instead of hardcoding values in `docker-compose.yml`, use a `.env` file.

1.  **Create `.env` file**: Create it in the project root and add it to `.gitignore`.
    ```properties
    DB_PASSWORD=MySecurePassword123!
    SMTP_HOST=smtp.gmail.com
    MY_API_KEY=12345
    ```

2.  **Reference in `docker-compose.yml`**:
    ```yaml
    services:
      mendixapp:
        image: mendix-app:latest
        environment:
          - ADMIN_PASSWORD=${DB_PASSWORD}
          - MXRUNTIME_MyEmailModule_SMTPServerAddress=${SMTP_HOST}
          - MXRUNTIME_MyModule_MySecretKey=${MY_API_KEY}
    ```

### 3. Verifying in Container Shell
To check if environment variables are correctly applied inside the running container:

```bash
# 1. Access Container (Bash)
docker exec -it <container_name> /bin/bash

# 2. Check Environment Variables
env | grep MXRUNTIME_
```

---

## ☸️ Kubernetes Local Testing Guide

You can test the deployment locally using Minikube or Docker Desktop Kubernetes with the manifests in the `k8s/` folder.

### 1. Prerequisites
*   **Enable Kubernetes**: Enable Kubernetes in Docker Desktop settings or install Minikube.
*   **Install kubectl**: CLI tool for controlling the Kubernetes cluster.

### 2. Build Image (Local)
Local K8s can use local Docker images (imagePullPolicy: IfNotPresent).
Build the image first.

```bash
# Run in the root directory
docker build -t mendix-app:latest .
```

### 3. Deploy Manifests
Apply the YAML files in the `k8s/` folder to your cluster.

```bash
# Create Namespace (Optional)
kubectl create namespace mendix

# Apply Manifests
kubectl apply -f k8s/postgres.yaml
kubectl apply -f k8s/mendix-app.yaml
```

### 4. Verify & Access
```bash
# Check Pod Status
kubectl get pods

# Check Services
kubectl get svc
```
*   **Docker Desktop**: Access via `localhost:8080`.
*   **Minikube**: Run `minikube service mendix-app` to get the URL.

---

## 💾 Handling Large MDA Files
If your `.mda` file is too large for Git, use one of the following methods:

### 1. Git LFS (Large File Storage) (Recommended)
Use Git LFS to version control large `.mda` files.
1.  Install **Git LFS** on both local machine and Jenkins server.
2.  Track mda files: `git lfs track "*.mda"`
3.  Commit and push as usual.

### 2. Download from External Storage (S3, Nexus, etc.)
Upload the file to an external file server and download it during the build.
*   **Jenkinsfile Example**:
    ```groovy
    script {
        sh 'curl -o docker-buildpack/app.mda "https://my-storage.com/app-v1.mda"'
    }
    ```

### 3. Manual Copy
Manually copy the file to the `build-source` folder in the Jenkins workspace.

---


## 🔒 Air-gapped Environment Setup

In air-gapped environments, you cannot download dependencies during the build.

### 1. Download Dependencies (Online)
Run the script to download Buildpack and Runtime to `docker-buildpack/build-cache`.

```bash
# Auto-detect version from .mpr and download
python3 scripts/download_offline_deps.py --source build-source
```

### 2. Transfer Files
Copy the `docker-buildpack/build-cache` directory to the same location in your offline environment.

### 3. Build
The Dockerfile detects the `build-cache` folder and uses local files automatically.

