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

        stage('Prepare Build Context') {
            steps {
                script {
                    echo 'Copying MDA file from source directory to docker-buildpack context...'
                    // 권한 문제 방지를 위해 기존 파일이 있다면 삭제
                    sh 'rm -f docker-buildpack/app.mda'
                    sh 'cp build-source/*.mda docker-buildpack/app.mda'
                }
            }
        }

        stage('Build Mendix App') {
            steps {
                script {
                    echo "Building Final Application Image: ${APP_IMAGE}"
                    
                    dir('docker-buildpack') {
                        sh """
                        docker build \
                        --build-arg BUILDER_ROOTFS_IMAGE=mendix-rootfs:builder \
                        --build-arg ROOTFS_IMAGE=mendix-rootfs:app \
                        --build-arg BUILD_PATH=app.mda \
                        -t ${APP_IMAGE} .
                        """
                    }
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
                    // 간단한 Health Check (메인 페이지 호출)
                    sh """
                    for i in {1..30}; do
                        if curl -s -f http://localhost:8080 > /dev/null; then
                            echo "Application is UP!"
                            exit 0
                        fi
                        echo "Waiting for app... (\$i/30)"
                        sleep 10
                    done
                    echo "Application failed to start."
                    echo "=== Container Logs ==="
                    docker compose -f docker-buildpack/tests/docker-compose-postgres.yml logs mendixapp
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
                echo 'Cleaning up...'
                // 테스트 종료 후 컨테이너 정리
                sh 'docker compose -f docker-buildpack/tests/docker-compose-postgres.yml down'
                
                // 오래된/사용하지 않는 이미지 정리 (선택 사항)
                // sh 'docker image prune -f' 
            }
        }
        success {
            echo 'Pipeline completed successfully!'
        }
        failure {
            echo 'Pipeline failed!'
        }
    }
}