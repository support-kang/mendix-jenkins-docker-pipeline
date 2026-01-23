FROM jenkins/jenkins:lts

# 루트 권한으로 전환 (설치를 위해)
USER root

# 필요한 패키지 설치 및 Docker Compose 다운로드
# (최신 버전이 필요하면 v2.29.1 부분을 최신 버전으로 변경하세요)
RUN apt-get update && apt-get install -y curl \
    && curl -L "https://github.com/docker/compose/releases/download/v2.29.1/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose \
    && chmod +x /usr/local/bin/docker-compose

# 다시 젠킨스 사용자로 전환
USER jenkins