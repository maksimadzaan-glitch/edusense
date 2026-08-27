#!/usr/bin/env bash
# Quick recover when EduSense hangs on small VPS
set -euo pipefail

echo "==> Memory / disk"
free -h || true
df -h / | tail -1 || true

echo "==> Restart services"
systemctl restart edusense
systemctl restart nginx
sleep 2

echo "==> Status"
systemctl is-active edusense nginx
ss -lptn | grep -E ':8010|:80|:443' || true

echo "==> Local health"
curl -s -m 5 http://127.0.0.1:8010/api/health || echo "LOCAL HEALTH FAIL"
curl -s -m 8 -o /dev/null -w "public https:%{http_code} time:%{time_total}s\n" https://edusence.ru/api/health || echo "PUBLIC HEALTH FAIL"

echo "==> Last logs"
journalctl -u edusense -n 25 --no-pager || true
echo "Done."
