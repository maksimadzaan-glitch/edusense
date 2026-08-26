#!/usr/bin/env bash
# EduSense — первичная установка на Ubuntu VPS (AdminVPS и аналоги)
# Запуск: sudo bash deploy/adminvps/setup.sh

set -euo pipefail

APP_DIR="/opt/edusense"
REPO="https://github.com/maksimadzaan-glitch/edusense.git"
SERVICE="edusense.service"

echo "==> Обновление системы и пакетов"
apt-get update -y
apt-get install -y git python3 python3-venv python3-pip nginx certbot python3-certbot-nginx

echo "==> Клонирование репозитория"
if [ ! -d "$APP_DIR/.git" ]; then
  git clone "$REPO" "$APP_DIR"
else
  cd "$APP_DIR" && git pull --ff-only
fi

cd "$APP_DIR"

echo "==> Python venv + зависимости"
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt

echo "==> Права для www-data"
chown -R www-data:www-data "$APP_DIR"

if [ ! -f "$APP_DIR/.env" ]; then
  cp "$APP_DIR/.env.example" "$APP_DIR/.env"
  echo ""
  echo "!!! Создан $APP_DIR/.env — отредактируйте ключи:"
  echo "    nano $APP_DIR/.env"
  echo ""
fi

echo "==> systemd"
cp "$APP_DIR/deploy/adminvps/edusense.service" "/etc/systemd/system/$SERVICE"
systemctl daemon-reload
systemctl enable "$SERVICE"
systemctl restart "$SERVICE"

echo "==> Готово. Проверка:"
sleep 2
curl -sf "http://127.0.0.1:8010/api/health" && echo "" || echo "Сервис ещё не отвечает — проверьте: journalctl -u edusense -n 50"

echo ""
echo "Дальше:"
echo "  1) nano /opt/edusense/.env  — вставьте ключи"
echo "  2) systemctl restart edusense"
echo "  3) Настройте nginx + SSL (см. DEPLOY_VPS.md или инструкцию в чате)"
