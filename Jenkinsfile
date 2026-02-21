pipeline {
    agent any

    environment {
        APP_PORT = "80"
        EC2_IP = "13.229.81.158"
        DOCKER_REPO = "vantaiz/demo-yte"
        DOCKERHUB_CRED = "dockerhub-credentials-id"
        IMAGE_TAG = "${BUILD_NUMBER}"
    }

    options {
        timestamps()
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Static Analysis - Semgrep') {
            steps {
                sh '''
                echo "Running Semgrep..."
                docker run --rm \
                  -v $WORKSPACE:/src \
                  semgrep/semgrep \
                  semgrep scan \
                  --config auto \
                  --no-git-ignore \
                  --severity ERROR \
                  /src
                '''
            }
        }

        stage('SCA Scan - Trivy FS') {
            steps {
                sh '''
                echo "Running Trivy FS scan..."
                docker run --rm \
                  -v $WORKSPACE:/app \
                  -v trivy-cache:/root/.cache/ \
                  aquasec/trivy fs \
                  --scanners vuln \
                  --severity HIGH,CRITICAL \
                  --exit-code 1 \
                  /app
                '''
            }
        }

        stage('Image Security Scan - Trivy') {
            steps {
                script {
                    def status = sh(
                        script: """
                            docker run --rm \
                              -v /var/run/docker.sock:/var/run/docker.sock \
                              -v trivy-cache:/root/.cache/ \
                              aquasec/trivy image \
                              --severity HIGH,CRITICAL \
                              --exit-code 1 \
                              ${DOCKER_REPO}:latest
                        """,
                        returnStatus: true
                    )

                    if (status != 0) {
                        echo "⚠️ Vulnerabilities detected in the image, but continuing pipeline..."
                        // Optionally fail the build if needed
                        // currentBuild.result = 'FAILURE'
                    } else {
                        echo "✅ No critical vulnerabilities found in the image."
                    }
                }
            }
        }

        stage('Build & Push Docker Image (amd64)') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: "${DOCKERHUB_CRED}",
                    usernameVariable: 'DOCKER_USER',
                    passwordVariable: 'DOCKER_PASS'
                )]) {
                    sh """
                      echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin
                    
                      docker buildx create --use || true
                    
                      docker buildx build \
                        --platform linux/amd64 \
                        -t ${DOCKER_REPO}:latest \
                        -t ${DOCKER_REPO}:${IMAGE_TAG} \
                        --push .
                    """
                }
            }
        }

        stage('Deploy to AWS EC2') {
            steps {
                sshagent(['AWS_SSH_KEY']) {
                    sh """
                    ssh -o StrictHostKeyChecking=no ec2-user@${EC2_IP} '
                        set -e
                        docker pull ${DOCKER_REPO}:latest
                        docker stop healthcare-app || true
                        docker rm healthcare-app || true
                        docker run -d \
                            -p 80:8080 \
                            --name healthcare-app \
                            --restart unless-stopped \
                            ${DOCKER_REPO}:latest
                    '
                    """
                }
            }
        }
    }

    post {
        success {
            echo "✅ Deployment Successful!"
            echo "App URL: http://${EC2_IP}"
        }

        failure {
            echo "❌ Pipeline Failed - Check security scan results."
        }

        always {
            cleanWs()
        }
    }
}
