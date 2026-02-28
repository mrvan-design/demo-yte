pipeline {
    agent any

    environment {
        GIT_REPO       = "https://github.com/mrvan-design/demo-yte.git"
        GIT_BRANCH     = "main"

        DOCKER_REPO    = "vantaiz/demo-yte"
        DOCKERHUB_CRED = "dockerhub-credentials-id"
        IMAGE_TAG      = "${BUILD_NUMBER}"

        EC2_IP         = "54.169.105.178"
        CONTAINER_NAME = "healthcare-app"
    }

    options {
    skipDefaultCheckout(true)
    timestamps()
    timeout(time: 30, unit: 'MINUTES')
    disableConcurrentBuilds()
}
    stages {

        stage('Clean Workspace') {
            steps { deleteDir() }
        }

        stage('Checkout Source') {
    steps {
        // Thêm credentialsId vào đây (Dùng ID của GitHub Token hoặc SSH Key bạn đã tạo)
        git branch: "${GIT_BRANCH}", 
            url: "${GIT_REPO}", 
            credentialsId: 'github-token-creds' 
    }
}

        stage('Verify Python Source') {
            steps {
                sh '''
                    echo "==== VERIFY PYTHON FILES ===="
                    PY_FILES=$(find . -type f -name "*.py")

                    if [ -z "$PY_FILES" ]; then
                        echo "❌ No Python files found!"
                        exit 1
                    fi

                    echo "$PY_FILES"
                    echo "✅ Python files detected"
                '''
            }
        }

stage('Semgrep Scan') {
    agent {
        docker {
            image 'returntocorp/semgrep'
            args  '-v $WORKSPACE:/src'
        }
    }
    steps {
        sh 'semgrep /src/app/ --config p/python --no-git-ignore --disable-version-check'
    }
}
        stage('Docker Login') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: "${DOCKERHUB_CRED}",
                    usernameVariable: 'DOCKER_USER',
                    passwordVariable: 'DOCKER_PASS'
                )]) {
                    sh '''
                        echo "==== Docker Login ===="
                        echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin
                    '''
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                sh '''
                    echo "==== Building Docker Image (amd64) ===="

                    docker build \
                      --platform linux/amd64 \
                      --pull \
                      -t ${DOCKER_REPO}:latest .

                    docker tag ${DOCKER_REPO}:latest ${DOCKER_REPO}:${IMAGE_TAG}
                '''
            }
        }

        stage('Container Scan - Trivy (Fail on CRITICAL)') {
            steps {
                sh '''
                    echo "==== Running Trivy Scan ===="

                    docker run --rm \
                      -v /var/run/docker.sock:/var/run/docker.sock \
                      -v trivy-cache:/root/.cache/trivy \
                      aquasec/trivy:latest \
                      image \
                      --scanners vuln \
                      --severity CRITICAL \
                      --exit-code 1 \
                      --no-progress \
                      ${DOCKER_REPO}:latest
                '''
            }
        }

        stage('Push Docker Image') {
            steps {
                sh '''
                    echo "==== Pushing Docker Image ===="

                    docker push ${DOCKER_REPO}:latest
                    docker push ${DOCKER_REPO}:${IMAGE_TAG}

                    docker logout
                '''
            }
        }

        stage('Deploy to EC2') {
            steps {
                sshagent(['AWS_SSH_KEY']) {
                    sh '''
                    echo "==== Deploying to EC2 ===="

                    ssh -o ConnectTimeout=10 \
                        -o StrictHostKeyChecking=no \
                        ec2-user@${EC2_IP} "

                        docker pull ${DOCKER_REPO}:latest &&
                        docker rm -f ${CONTAINER_NAME} || true &&
                        docker run -d \
                          --name ${CONTAINER_NAME} \
                          -p 80:8000 \
                          --restart unless-stopped \
                          ${DOCKER_REPO}:latest
                    "
                    '''
                }
            }
        }
    }

    post {
        success {
            echo "✅ Deployment Successful"
            echo "🌐 http://${EC2_IP}"
        }
        failure {
            echo "❌ Pipeline Failed"
        }
        always {
            cleanWs()
        }
    }
}