pipeline {
    agent any
    
    environment {
        // Đã cập nhật khớp với main.tf (FastAPI thường dùng 8000)
        APP_PORT = "80" 
        EC2_IP = "54.169.9.106" 
        DOCKER_REPO = "username/demo-yte"
        DOCKERHUB_CRED = "dockerhub-credentials-id"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Static Analysis (Semgrep)') {
         steps {
        // Thêm -u $(id -u) để tránh lỗi permission khi tạo file log
            sh 'docker run --rm -v $(pwd):/src returntocorp/semgrep semgrep scan --config=auto --error'
    }
}

        stage('SCA Scan (Trivy FS)') {
            steps {
                // Quét thư viện mã nguồn, dừng nếu thấy lỗi High/Critical
                sh "docker run --rm -v \$(pwd):/app aquasec/trivy fs --severity HIGH,CRITICAL --exit-code 1 /app"
            }
        }

        stage('Build & Image Scan') {
            steps {
                script {
                    def appImage = docker.build("${DOCKER_REPO}:latest")
                    
                    // SECURITY GATE: Quét Image vừa build. Lỗi nặng là dừng pipeline tại đây!
                    sh "docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy image --severity HIGH,CRITICAL --exit-code 1 ${DOCKER_REPO}:latest"
                }
            }
        }

        stage('Push to Docker Hub') {
            steps {
                script {
                    docker.withRegistry('', "${DOCKERHUB_CRED}") {
                        docker.image("${DOCKER_REPO}:latest").push()
                        docker.image("${DOCKER_REPO}:latest").push("${env.BUILD_NUMBER}")
                    }
                }
            }
        }

        stage('Deploy to AWS EC2') {
            steps {
                sshagent(['AWS_SSH_KEY']) {
                    sh """
                    ssh -o StrictHostKeyChecking=no ec2-user@${env.EC2_IP} "
                        docker pull ${env.DOCKER_REPO}:latest
                        docker stop healthcare-app || true
                        docker rm healthcare-app || true
                        # Chạy với Non-root (nếu Dockerfile đã config) và port 8000
                        docker run -d \
                            -p ${env.APP_PORT}:${env.APP_PORT} \
                            --name healthcare-app \
                            --restart unless-stopped \
                            ${env.DOCKER_REPO}:latest
                    "
                    """
                }
            }
        }
    }
    
    post {
        success {
            echo "✅ Deployment Successful! App is live at http://${env.EC2_IP}:${env.APP_PORT}"
        }
        failure {
            echo "❌ Pipeline Failed. Please check Security Scan logs!"
        }
        always {
            cleanWs()
        }
    }
}
