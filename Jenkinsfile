// JENKINS PIPELINE  (syllabus weeks 4, 5, 7, 9)
// Every time it runs:  Checkout -> Build Docker images -> Unit tests -> (optional) Push to Docker Hub -> (optional) Deploy to Kubernetes
// Works on Windows (bat) and Linux/Mac (sh) Jenkins.
// Jenkins setup: New Item -> Pipeline -> "Pipeline script from SCM" -> Git -> repo URL -> Script Path: Jenkinsfile

// run a command with sh on Linux/Mac and bat on Windows
def runCmd(String cmd) {
    if (isUnix()) { sh cmd } else { bat cmd }
}

pipeline {
    agent any

    // Check GitHub every 2 minutes; if there's a new commit, build automatically (Continuous Integration)
    triggers {
        pollSCM('H/2 * * * *')
    }

    parameters {
        booleanParam(name: 'PUSH_TO_DOCKERHUB', defaultValue: false,
                     description: 'Push the images to Docker Hub (needs Jenkins credentials with ID dockerhub-creds)')
        string(name: 'DOCKERHUB_USER', defaultValue: 'pranathidevaki',
               description: 'Your Docker Hub username')
        booleanParam(name: 'DEPLOY_TO_K8S', defaultValue: false,
                     description: 'Also deploy the new images to Kubernetes (Docker Desktop cluster)')
    }

    environment {
        TAG = "${env.BUILD_NUMBER}"   // every build gets its own image tag: 1, 2, 3 ...
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build Docker images') {
            steps {
                runCmd "docker build -t income-tax-service:${TAG} -t income-tax-service:latest income-tax-service"
                runCmd "docker build -t gst-service:${TAG} -t gst-service:latest gst-service"
                runCmd "docker build -t tax-frontend:${TAG} -t tax-frontend:latest frontend"
            }
        }

        stage('Unit tests') {
            parallel {
                stage('income-tax-service') {
                    steps { runCmd "docker run --rm income-tax-service:${TAG} python -m pytest -v" }
                }
                stage('gst-service') {
                    steps { runCmd "docker run --rm gst-service:${TAG} node --test" }
                }
            }
        }

        stage('Push Docker Images') {
            when { expression { params.PUSH_TO_DOCKERHUB } }
            steps {
                withCredentials([usernamePassword(credentialsId: 'dockerhub-creds',
                                                  usernameVariable: 'DH_USER', passwordVariable: 'DH_PASS')]) {
                    script {
                        // log in with the token stored in Jenkins (never written in the code)
                        if (isUnix()) {
                            sh 'echo "$DH_PASS" | docker login -u "$DH_USER" --password-stdin'
                        } else {
                            bat 'echo %DH_PASS%| docker login -u %DH_USER% --password-stdin'
                        }
                        for (img in ['income-tax-service', 'gst-service', 'tax-frontend']) {
                            runCmd "docker tag ${img}:${TAG} ${params.DOCKERHUB_USER}/${img}:${TAG}"
                            runCmd "docker tag ${img}:${TAG} ${params.DOCKERHUB_USER}/${img}:latest"
                            runCmd "docker push ${params.DOCKERHUB_USER}/${img}:${TAG}"
                            runCmd "docker push ${params.DOCKERHUB_USER}/${img}:latest"
                        }
                    }
                }
            }
        }

        stage('Deploy to Kubernetes') {
            when { expression { params.DEPLOY_TO_K8S } }
            steps {
                runCmd "kubectl apply -f k8s/"
                // point each Deployment at THIS build's image -> Kubernetes does a rolling update
                runCmd "kubectl set image deployment/income-tax-service income-tax-service=income-tax-service:${TAG}"
                runCmd "kubectl set image deployment/gst-service gst-service=gst-service:${TAG}"
                runCmd "kubectl set image deployment/frontend frontend=tax-frontend:${TAG}"
                runCmd "kubectl rollout status deployment/income-tax-service --timeout=120s"
                runCmd "kubectl rollout status deployment/gst-service --timeout=120s"
                runCmd "kubectl rollout status deployment/frontend --timeout=120s"
                runCmd "kubectl get pods,svc"
            }
        }
    }

    post {
        success { echo "Build #${env.BUILD_NUMBER} passed." }
        failure { echo "Build #${env.BUILD_NUMBER} FAILED - open the red stage to see why." }
    }
}
