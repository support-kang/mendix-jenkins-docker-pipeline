FROM jenkins/jenkins:lts

USER root

# 1. 필수 기본 패키지 설치
RUN apt-get update && apt-get install -y \
    lsb-release \
    curl \
    gnupg \
    sudo \
    python3 \
    python3-requests

# 2. Docker 공식 GPG 키 추가 및 리포지토리 설정
RUN mkdir -p /etc/apt/keyrings && \
    curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg && \
    echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian \
    $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

# 3. Docker CLI 및 Docker Compose 플러그인 설치
RUN apt-get update && apt-get install -y \
    docker-ce-cli \
    docker-compose-plugin

# 4. Standalone Docker Compose (v1 호환용 바이너리) 설치
# 최신 버전 URL 사용 (linux 소문자 주의)
RUN curl -SL "https://github.com/docker/compose/releases/download/v2.29.1/docker-compose-linux-$(uname -m)" -o /usr/local/bin/docker-compose && \
    chmod +x /usr/local/bin/docker-compose && \
    # 로컬 테스트 시 git의 권한 문제 해결, docker socket을 쓰는경우에만 사용.
    git config --system --add safe.directory '*' 

# 5. 권한 설정
# Docker 그룹이 없으면 생성하고, jenkins 사용자를 docker 그룹에 추가
RUN groupadd -f docker && usermod -aG docker jenkins

# jenkins 사용자가 sudo를 암호 없이 사용할 수 있도록 설정 (선택 사항, 디버깅 용이)
RUN echo "jenkins ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers

# 6. 플러그인 설치 (폐쇄망 지원을 위해 이미지에 포함)
COPY --chown=jenkins:jenkins plugins.txt /usr/share/jenkins/ref/plugins.txt
RUN jenkins-plugin-cli -f /usr/share/jenkins/ref/plugins.txt