#!/usr/bin/env bash
# Recover when HTTPS hangs from outside but local may still work
set -euo pipefail

echo "==> Before"
free -h | sed -n '1,3p' || true
ss -s || true
systemctl is-active edusense nginx || true

echo "==> Kill wedged listeners / restart"
systemctl stop edusense || true
pkill -f 'uvicorn backend.main:app' || true
sleep 1
chown -R www-data:www-data /opt/edusense || true
systemctl start edusense
systemctl restart nginx
sleep 2

echo "==> After"
systemctl is-active edusense nginx
ss -lptn | grep -E ':8010|:443|:80' || true
curl -s -m 4 http://127.0.0.1:8010/api/health || echo LOCAL_FAIL
curl -s -m 8 -o /dev/null -w "public:%{http_code} t=%{time_total}\n" https://127.0.0.1/api/health -k --resolve edusence.ru:443:127.0.0.1 || echo PUBLIC_LOCAL_FAIL
journalctl -u edusense -n 20 --no-pager || true
echo Done
