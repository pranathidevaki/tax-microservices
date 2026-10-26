// JENKINS PIPELINE  (syllabus weeks 4, 5, 7, 9)
// Every time it runs:  Checkout from GitHub -> Build Docker images -> Run unit tests -> (optional) Deploy to Kubernetes
// Works on Windows (bat) and Linux/Mac (sh) Jenkins.
// Jenkins setup: New Item -> Pipeline -> "Pipeline script from SCM" -> Git -> repo URL -> Script Path: Jenkinsfile

// run a command with sh on Linux/Mac and bat on Windows
def run(String cmd) {
    if (isUnix()) { sh cmd } else { bat cmd }
}

pipeline {
    agent any

    // Check GitHub every 2 minutes; if there's a new commit, build automatically (Continuous Integration)
    triggers {
        pollSCM('H/2 * * * *')
    }

    parameters {
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
                run "docker build -t income-tax-service:${TAG} -t income-tax-service:latest income-tax-service"
                run "docker build -t gst-service:${TAG} -t gst-service:latest gst-service"
                run "docker build -t tax-frontend:${TAG} -t tax-frontend:latest frontend"
            }
        }

        stage('Unit tests') {
            parallel {
                stage('income-tax-service') {
                    steps { run "docker run --rm income-tax-service:${TAG} python -m pytest -v" }
                }
                stage('gst-service') {
                    steps { run "docker run --rm gst-service:${TAG} node --test" }
                }
            }
        }

        stage('Deploy to Kubernetes') {
            when { expression { params.DEPLOY_TO_K8S } }
            steps {
                run "kubectl apply -f k8s/"
                // point each Deployment at THIS build's image -> Kubernetes does a rolling update
                run "kubectl set image deployment/income-tax-service income-tax-service=income-tax-service:${TAG}"
                run "kubectl set image deployment/gst-service gst-service=gst-service:${TAG}"
                run "kubectl set image deployment/frontend frontend=tax-frontend:${TAG}"
                run "kubectl rollout status deployment/income-tax-service --timeout=120s"
                run "kubectl rollout status deployment/gst-service --timeout=120s"
                run "kubectl rollout status deployment/frontend --timeout=120s"
                run "kubectl get pods,svc"
            }
        }
    }

    post {
        success { echo "Build #${env.BUILD_NUMBER} passed." }
        failure { echo "Build #${env.BUILD_NUMBER} FAILED - open the red stage to see why." }
    }
}
