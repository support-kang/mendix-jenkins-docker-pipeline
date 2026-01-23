# Mendix Jenkins Docker Pipeline

[English](#english-version) | [한국어](#korean-version)

<a name="korean-version"></a>
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
2.  **MDA 파일 준비**: 
    *   Mendix Modeler에서 배포 패키지(.mda)를 생성합니다.
    *   생성된 파일을 프로젝트 내 **`build-source` 폴더**에 복사합니다. (폴더가 없다면 생성)
3.  **파이프라인 실행**:
    *   젠킨스에서 'New Item' -> 'Pipeline'을 생성합니다.
    *   'Pipeline script from SCM'을 선택하고 Git 리포지토리를 연결합니다.
    *   'Build Now'를 클릭하여 배포를 시작합니다.

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

인터넷이 없는 환경에서는 외부에서 빌드된 이미지를 반입하여 배포하는 것을 권장합니다.

### 추천 전략: 외부 빌드 후 이미지 반입 (Build Outside)
1.  **외부망**: 소스를 빌드하여 `mendix-app` 이미지를 생성 후 파일로 저장 (`docker save`).
2.  **내부망**: 이미지 파일을 로드하고 `docker-compose up`으로 실행.
(상세 내용은 이전 가이드 참조)

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
2.  **Prepare MDA**: 
    *   Build `.mda` package in Mendix Modeler.
    *   Place it in the **`build-source` folder**.
3.  **Run Pipeline**:
    *   Create a new Pipeline job in Jenkins.
    *   Connect your Git repository.
    *   Click 'Build Now'.

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

## 🔒 Air-gapped Environment Guide
For environments without internet, it is recommended to build images externally and transfer them.

### Strategy: Build Outside, Deploy Inside
1.  **External**: Build `mendix-app` image and save to file (`docker save`).
2.  **Internal**: Load image (`docker load`) and run with `docker-compose`.
