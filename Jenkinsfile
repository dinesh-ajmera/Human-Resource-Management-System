pipeline {
  agent { label 'docker-agent' }

  environment {
    AWS_REGION = 'ap-south-1'
    IMAGE      = 'hrms'
  }

  options {
    timestamps()
    disableConcurrentBuilds()
    timeout(time: 25, unit: 'MINUTES')
  }

  triggers { pollSCM('H/2 * * * *') }

  stages {
    stage('Checkout') {
      steps {
        checkout scm
        script {
          def sha = sh(returnStdout: true, script: 'git rev-parse --short HEAD').trim()
          env.IMAGE_TAG = "${env.BUILD_NUMBER}-${sha}"
        }
      }
    }

    stage('Syntax check') {
      steps { sh 'python3 -m compileall -q .' }
    }

    stage('Build image') {
      steps { sh 'docker build -t ${IMAGE}:${IMAGE_TAG} .' }
    }

    stage('Scan image') {
      steps {
        // report HIGH and CRITICAL, but only fail the build on fixable CRITICAL
        sh 'trivy image --no-progress --severity HIGH,CRITICAL --ignore-unfixed ${IMAGE}:${IMAGE_TAG}'
        sh 'trivy image --no-progress --exit-code 1 --severity CRITICAL --ignore-unfixed ${IMAGE}:${IMAGE_TAG}'
      }
    }

    stage('Push to ECR') {
      steps {
        sh '''
          set -e
          ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
          REGISTRY=$ACCOUNT.dkr.ecr.${AWS_REGION}.amazonaws.com
          aws ecr get-login-password --region ${AWS_REGION} \
            | docker login --username AWS --password-stdin $REGISTRY
          docker tag ${IMAGE}:${IMAGE_TAG} $REGISTRY/${IMAGE}:${IMAGE_TAG}
          docker push $REGISTRY/${IMAGE}:${IMAGE_TAG}
          echo "Pushed $REGISTRY/${IMAGE}:${IMAGE_TAG}"
        '''
      }
    }

    stage('Deploy with Ansible') {
      steps {
        withCredentials([
          file(credentialsId: 'hrms-ssh-key', variable: 'SSH_KEY'),
          string(credentialsId: 'ansible-vault-pass', variable: 'VAULT_PASS'),
          string(credentialsId: 'hrms-server-ip', variable: 'SERVER_IP')
        ]) {
          dir('ansible') {
            sh '''
              set -e
              mkdir -p ~/.ssh
              ssh-keyscan -H "$SERVER_IP" >> ~/.ssh/known_hosts
              printf '[hrms]\n%s ansible_user=ubuntu ansible_python_interpreter=/usr/bin/python3\n' "$SERVER_IP" > inventory.jenkins
              VF=$(mktemp)
              trap 'rm -f "$VF" inventory.jenkins' EXIT
              printf '%s' "$VAULT_PASS" > "$VF"
              ansible-playbook -i inventory.jenkins playbook.yml \
                --vault-password-file "$VF" \
                -e ansible_ssh_private_key_file="$SSH_KEY"
            '''
          }
        }
      }
    }

    stage('Verify') {
      steps {
        withCredentials([string(credentialsId: 'hrms-server-ip', variable: 'SERVER_IP')]) {
          sh 'curl -fsS --retry 10 --retry-delay 5 --retry-connrefused http://$SERVER_IP:5000/health'
        }
      }
    }
  }

  post {
    success { echo "Built, scanned, pushed and deployed ${env.IMAGE_TAG}" }
    failure { echo 'Pipeline failed. Check the stage logs.' }
  }
}