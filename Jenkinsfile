pipeline {
    agent any

    environment {
        // 1. 버전 관리 (빌드 번호 사용)
        // 기본값은 mendix-app:build-X 형식이 됨
        APP_IMAGE = "mendix-app:build-${env.BUILD_NUMBER}"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        // 2. 빌드 속도 최적화 (Conditional Build)
        // 이미지가 존재하면 빌드를 건너뜀
        stage('Build Base Images') {
            steps {
                script {
                    dir('docker-buildpack') {
                        // mendix-rootfs:app 이미지 확인
                        if (sh(script: "docker images -q mendix-rootfs:app", returnStdout: true).trim().isEmpty()) {
                            echo 'Building RootFS App Image...'
                            sh 'docker build -t mendix-rootfs:app -f rootfs-app.dockerfile .'
                        } else {
                            echo 'RootFS App Image already exists. Skipping build.'
                        }

                        // mendix-rootfs:builder 이미지 확인
                        if (sh(script: "docker images -q mendix-rootfs:builder", returnStdout: true).trim().isEmpty()) {
                            echo 'Building RootFS Builder Image...'
                            sh 'docker build -t mendix-rootfs:builder -f rootfs-builder.dockerfile .'
                        } else {
                            echo 'RootFS Builder Image already exists. Skipping build.'
                        }
                    }
                }
            }
        }

        stage('Prepare & Build Logic') {
            steps {
                script {
                    echo 'Determining build strategy...'
                    
                    // 기본 빌드 인자 설정
                    def buildArgs = "--build-arg BUILDER_ROOTFS_IMAGE=mendix-rootfs:builder --build-arg ROOTFS_IMAGE=mendix-rootfs:app"
                    def buildContext = "docker-buildpack"

                    // 1. MDA 파일 존재 여부 확인
                    if (sh(script: "ls build-source/*.mda > /dev/null 2>&1", returnStatus: true) == 0) {
                        echo "Strategy: MDA File Found. Using existing MDA."
                        
                        // 기존 MDA 정리 및 복사
                        sh 'rm -f docker-buildpack/app.mda'
                        sh 'cp build-source/*.mda docker-buildpack/app.mda'
                        
                        // MDA 경로를 빌드 인자로 추가
                        buildArgs += " --build-arg BUILD_PATH=app.mda"
                        
                    } else {
                        echo "Strategy: No MDA Found. Attempting to build from source using build.py..."
                        
                        // 소스 빌드 결과 저장할 디렉토리 정리
                        sh 'rm -rf docker-buildpack/build-context'
                        
                        // build.py 실행 (소스 -> MDA/Project 변환)
                        // build.py가 내부 'scripts' 폴더를 참조하므로 실행 위치를 docker-buildpack으로 변경해야 함
                        dir('docker-buildpack') {
                            sh """
                            python3 build.py \
                                --source ../build-source \
                                --destination build-context \
                                build-mda-dir
                            """
                        }
                        
                        // 빌드 컨텍스트 변경
                        buildContext = "docker-buildpack/build-context"
                    }

                    echo "Building Final Application Image: ${APP_IMAGE}"
                    echo "Context: ${buildContext}"
                    echo "Args: ${buildArgs}"

                    // 최종 Docker Build 수행
                    sh "docker build ${buildArgs} -t ${APP_IMAGE} ${buildContext}"
                }
            }
        }

        stage('Deploy to Test') {
            steps {
                script {
                    echo 'Deploying application stack...'
                    // docker compose (v2) 사용 (README 가이드에 따라 환경 구성 필요)
                    sh 'docker compose -f docker-buildpack/tests/docker-compose-postgres.yml up -d'
                    
                    echo 'Waiting for application to start...'
                    sleep 30
                }
            }
        }

        // 3. 통합 테스트 (Verification)
        stage('Verification') {
            steps {
                script {
                    echo 'Verifying application health...'
                    // Docker Native Healthcheck 상태 확인
                    sh """
                    # 컨테이너 ID 조회 (종료된 컨테이너 포함)
                    CONTAINER_ID=\$(docker compose -f docker-buildpack/tests/docker-compose-postgres.yml ps -a -q mendixapp)
                    
                    if [ -z "\$CONTAINER_ID" ]; then
                        echo "Error: Application container not found!"
                        exit 1
                    fi

                    echo "Monitoring container health for \$CONTAINER_ID..."
                    
                    # 컨테이너 시작 대기 (최대 30초)
                    echo "Waiting for container to start..."
                    for i in {1..10}; do
                         STATUS=\$(docker inspect --format='{{.State.Status}}' \$CONTAINER_ID)
                         if [ "\$STATUS" = "running" ]; then
                             break
                         fi
                         if [ "\$STATUS" = "exited" ] || [ "\$STATUS" = "dead" ]; then
                             echo "Container exited early with status: \$STATUS"
                             echo "=== Container Logs ==="
                             docker logs \$CONTAINER_ID
                             exit 1
                         fi
                         sleep 3
                    done

                    # 최대 5분 대기 (5초 * 60회)
                    for i in {1..60}; do
                        HEALTH=\$(docker inspect --format='{{.State.Health.Status}}' \$CONTAINER_ID)
                        STATUS=\$(docker inspect --format='{{.State.Status}}' \$CONTAINER_ID)
                        
                        echo "Status: \$STATUS, Health: \$HEALTH (\$i/60)"
                        
                        if [ "\$STATUS" = "exited" ] || [ "\$STATUS" = "dead" ]; then
                             echo "Container crashed!"
                             echo "=== Container Logs ==="
                             docker logs \$CONTAINER_ID
                             exit 1
                        fi

                        if [ "\$HEALTH" = "healthy" ]; then
                            echo "Application is UP and HEALTHY!"
                            exit 0
                        fi
                        
                        if [ "\$HEALTH" = "unhealthy" ]; then
                            echo "Application verification FAILED (Unhealthy)."
                            echo "=== Container Logs ==="
                            docker logs \$CONTAINER_ID
                            exit 1
                        fi
                        
                        sleep 5
                    done
                    
                    echo "Application verification TIMED OUT."
                    echo "=== Container Logs ==="
                    docker logs \$CONTAINER_ID
                    exit 1
                    """
                }
            }
        }
    }

    // 4. 디스크 정리 (Cleanup)
    post {
        always {
            script {
                echo 'Pipeline execution finished.'
                // 오래된/사용하지 않는 이미지 정리 (선택 사항)
                sh 'docker image prune -f' 
            }
        }
        success {
            echo 'Pipeline completed successfully! Test environment is preserved.'
        }
        failure {
            script {
                echo 'Pipeline failed! Cleaning up...'
                sh 'docker compose -f docker-buildpack/tests/docker-compose-postgres.yml down -v'
            }
        }
        aborted {
            script {
                echo 'Pipeline aborted! Cleaning up...'
                sh 'docker compose -f docker-buildpack/tests/docker-compose-postgres.yml down -v'
            }
        }
    }
}