#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/envs/dev"
terraform destroy -var 'alb_allowed_cidrs=[]' -var 'alert_email=none@example.com'