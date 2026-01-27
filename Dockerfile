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
    chmod +x /usr/local/bin/docker-compose

# 5. 권한 설정
# Docker 그룹이 없으면 생성하고, jenkins 사용자를 docker 그룹에 추가
RUN groupadd -f docker && usermod -aG docker jenkins

# jenkins 사용자가 sudo를 암호 없이 사용할 수 있도록 설정 (선택 사항, 디버깅 용이)
RUN echo "jenkins ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers

# 다시 젠킨스 사용자로 전환
USER jenkins

# 6. 플러그인 설치 (폐쇄망 지원을 위해 이미지에 포함)
COPY --chown=jenkins:jenkins plugins.txt /usr/share/jenkins/ref/plugins.txt
# 7. 권한 문제 해결을 위한 sudo 래퍼 설정 (root 사용자 전환 대신 깔끔한 방식)
# jenkins 사용자가 sudo를 통해 docker를 실행하도록 래퍼 스크립트 생성
# 기존 바이너리를 -real로 변경하고, 원본 위치에 래퍼 배치
RUN mv /usr/bin/docker /usr/bin/docker-real \
    && mv /usr/local/bin/docker-compose /usr/local/bin/docker-compose-real \
    && echo '#!/bin/bash' > /usr/bin/docker \
    && echo 'sudo /usr/bin/docker-real "$@"' >> /usr/bin/docker \
    && chmod +x /usr/bin/docker \
    && echo '#!/bin/bash' > /usr/local/bin/docker-compose \
    && echo 'sudo /usr/local/bin/docker-compose-real "$@"' >> /usr/local/bin/docker-compose \
    && chmod +x /usr/local/bin/docker-compose

# 8. 마지막 실행 권한 (jenkins 사용자로 실행하되 sudo 사용 가능)
USER jenkins