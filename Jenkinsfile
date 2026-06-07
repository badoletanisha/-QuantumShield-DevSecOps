pipeline {
    agent any

    environment {
        IMAGE_REPO    = "flask-app"
        DOCKER_USER   = credentials('dockerhub-creds')
        IMAGE_NAME    = "tanishabadole28/${IMAGE_REPO}"
        SONAR_HOME    = tool "sonar"
    }

    triggers {
        pollSCM('H/2 * * * *')
    }

    stages {

        stage('Checkout Code') {
            steps {
                checkout scm
            }
        }

       stage('SonarQube Analysis') {
    steps {
        withSonarQubeEnv('sonarqube-server') {
            sh '''
                $SONAR_HOME/bin/sonar-scanner \
                -Dsonar.projectKey=badoletanisha_QuantumShield-DevSecOps \
                -Dsonar.projectName=QuantumShield-DevSecOps \
                -Dsonar.organization=badoletanisha \
                -Dsonar.sources=.
            '''
        }
    }
}

        stage('Quality Gate') {
            steps {
                timeout(time: 5, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: false
                }
            }
        }

        stage('Setup Python Environment') {
            steps {
                sh '''
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                '''
            }
        }

        stage('Lint Code') {
            steps {
                sh '''
                    . venv/bin/activate
                    flake8 app.py --max-line-length=120 || true
                '''
            }
        }

        stage('Run Tests') {
            steps {
                sh '''
                    . venv/bin/activate
                    pytest || true
                '''
            }
        }

        stage('Health Check') {
            steps {
                sh '''
                    . venv/bin/activate
                    python app.py &
                    sleep 5
                    curl -f http://127.0.0.1:5000/health
                    pkill -f app.py || true
                '''
            }
        }

        stage('Build Docker Image') {
            steps {
                sh '''
                    docker build -t ${IMAGE_NAME}:${BUILD_NUMBER} .
                    docker tag ${IMAGE_NAME}:${BUILD_NUMBER} \
                               ${IMAGE_NAME}:latest
                '''
            }
        }

        stage('Trivy Image Scan') {
            steps {
                sh '''
                    trivy image \
                        --severity HIGH,CRITICAL \
                        --format table \
                        --no-progress \
                        --output trivy-report.txt \
                        ${IMAGE_NAME}:${BUILD_NUMBER}
                '''
            }
        }

        stage('Push to Docker Hub') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'dockerhub-creds',
                    usernameVariable: 'DOCKER_USERNAME',
                    passwordVariable: 'DOCKER_PASSWORD'
                )]) {
                    sh '''
                        echo "$DOCKER_PASSWORD" | docker login \
                            -u "$DOCKER_USERNAME" --password-stdin
                        docker push ${IMAGE_NAME}:${BUILD_NUMBER}
                        docker push ${IMAGE_NAME}:latest
                    '''
                }
            }
        }

        stage('Update K8s Manifest') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'github-token',
                    usernameVariable: 'GIT_USER',
                    passwordVariable: 'GIT_PASS'
                )]) {
                    sh '''
                        git config user.email "jenkins@ci.local"
                        git config user.name "Jenkins"
                        git fetch origin
                        git checkout deploy
                        git pull origin deploy
                        sed -i "s|image: .*|image: ${IMAGE_NAME}:${BUILD_NUMBER}|" \
                            k8s-manifest/deployment.yaml
                        git add k8s-manifest/deployment.yaml
                        git commit -m "Update image to build ${BUILD_NUMBER}" \
                            || echo "No changes to commit"
                        git push https://${GIT_USER}:${GIT_PASS}@github.com/badoletanisha/QuantumShield-DevSecOps.git deploy
                    '''
                }
            }
        }
    }

    post {
    always {
        archiveArtifacts artifacts: 'trivy-report.txt',
                         allowEmptyArchive: true
        sh 'pkill -f app.py || true'
    }
        success {
            echo "✅ Pipeline Successful!"
        }
        failure {
            echo "❌ Pipeline Failed!"
        }
    }
}
