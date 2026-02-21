pipeline {
    agent any
    
    environment {
        APP_PORT = "80" 
        EC2_IP = "54.169.9.106" 
        DOCKER_REPO = "vantaiz/demo-yte"
        DOCKERHUB_CRED = "dockerhub-credentials-id" // Đảm bảo ID này khớp trong Jenkins Credentials
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Static Analysis (Semgrep)') {
         steps {
            sh '''
            pip install semgrep
               semgrep scan --config auto || true
               '''
    }
}

        stage('SCA Scan (Trivy FS)') {
            steps {
                // Quét file hệ thống (source code)
                sh "docker run --rm -v \$(pwd):/app aquasec/trivy fs --severity HIGH,CRITICAL --exit-code 0 /app"
            }
        }

        stage('Build & Image Scan') {
            steps {
                script {
                    // Build image
                    def appImage = docker.build("${DOCKER_REPO}:latest")
                    
                    // SECURITY GATE: Quét Image. 
                    // Nếu bạn muốn pipeline DỪNG khi có lỗi bảo mật, hãy để --exit-code 1
                    // Nếu muốn chạy tiếp bất chấp rủi ro, sửa thành --exit-code 0
                    sh "docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy image --severity HIGH,CRITICAL --exit-code 0 ${DOCKER_REPO}:latest"
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
                // Đảm bảo bạn đã thêm Private Key của EC2 vào Jenkins với ID 'AWS_SSH_KEY'
                sshagent(['AWS_SSH_KEY']) {
                    sh """
                    ssh -o StrictHostKeyChecking=no ec2-user@${env.EC2_IP} "
                        docker pull ${env.DOCKER_REPO}:latest
                        docker stop healthcare-app || true
                        docker rm healthcare-app || true
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
            echo "✅ Deployment Successful! App is live at http://${env.EC2_IP}"
        }
        failure {
            echo "❌ Pipeline Failed. Check logs for Semgrep or Trivy findings!"
        }
        always {
            cleanWs()
        }
    }
}
