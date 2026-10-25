pipeline {
  agent { label 'docker-agent' }

  options {
    timestamps()
    disableConcurrentBuilds()
    timeout(time: 20, unit: 'MINUTES')
  }

  triggers { pollSCM('H/2 * * * *') }

  stages {
    stage('Checkout') {
      steps { checkout scm }
    }

    stage('Syntax check') {
      steps { sh 'python3 -m compileall -q .' }
    }

    stage('Build image') {
      steps { sh 'docker build -t hrms:${BUILD_NUMBER} .' }
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
    success { echo 'Deployed and healthy.' }
    failure { echo 'Pipeline failed. Check the stage logs.' }
  }
}