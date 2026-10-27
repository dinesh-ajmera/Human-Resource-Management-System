pipeline {
  agent { label 'docker-agent' }

  environment {
    AWS_REGION = 'ap-south-1'
    IMAGE      = 'hrms'
  }

  options {
    timestamps()
    disableConcurrentBuilds()
    timeout(time: 40, unit: 'MINUTES')
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

        stage('Release to Auto Scaling Group') {
      steps {
        sh '''
          set -e
          PARAM=/hrms/dev/image_tag
          ASG=hrms-dev-asg
          PREFS='{"MinHealthyPercentage":50,"InstanceWarmup":120}'

          PREV=$(aws ssm get-parameter --name $PARAM --query Parameter.Value --output text --region $AWS_REGION)
          echo "Previous tag: $PREV   New tag: $IMAGE_TAG"

          aws ssm put-parameter --name $PARAM --value "$IMAGE_TAG" --overwrite --region $AWS_REGION
          aws autoscaling start-instance-refresh --auto-scaling-group-name $ASG \
            --preferences "$PREFS" --region $AWS_REGION

          for i in $(seq 1 60); do
            STATUS=$(aws autoscaling describe-instance-refreshes --auto-scaling-group-name $ASG \
              --max-records 1 --query 'InstanceRefreshes[0].Status' --output text --region $AWS_REGION)
            echo "Refresh status: $STATUS ($i/60)"
            case "$STATUS" in
              Successful) exit 0 ;;
              Failed|Cancelled|Cancelling|RollbackFailed) break ;;
            esac
            sleep 20
          done

          echo "Release did not finish. Rolling back to $PREV"
          aws autoscaling cancel-instance-refresh --auto-scaling-group-name $ASG --region $AWS_REGION || true
          sleep 30
          aws ssm put-parameter --name $PARAM --value "$PREV" --overwrite --region $AWS_REGION
          aws autoscaling start-instance-refresh --auto-scaling-group-name $ASG \
            --preferences "$PREFS" --region $AWS_REGION || true
          exit 1
        '''
      }
    }

    stage('Verify') {
      steps {
        sh '''
          ALB=$(aws elbv2 describe-load-balancers --names hrms-dev-alb \
                --query 'LoadBalancers[0].DNSName' --output text --region $AWS_REGION)
          curl -fsS --retry 10 --retry-delay 5 --retry-connrefused http://$ALB/health
        '''
      }
    }
  }

  post {
    success { echo "Built, scanned, pushed and deployed ${env.IMAGE_TAG}" }
    failure { echo 'Pipeline failed. Check the stage logs.' }
  }
}