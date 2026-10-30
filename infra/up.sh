#!/usr/bin/env bash
# Usage: MY_IP=1.2.3.4 ALERT_EMAIL=you@example.com ./up.sh
set -euo pipefail
: "${MY_IP:?Set MY_IP (your own public IP)}"
: "${ALERT_EMAIL:?Set ALERT_EMAIL}"
JENKINS_IP=$(curl -fsS https://checkip.amazonaws.com | tr -d '\n')   # run this ON the Jenkins server
cd "$(dirname "$0")/envs/dev"
terraform init -input=false
terraform apply \
  -var "alb_allowed_cidrs=[\"${MY_IP}/32\",\"${JENKINS_IP}/32\"]" \
  -var "alert_email=${ALERT_EMAIL}"