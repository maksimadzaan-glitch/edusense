#!/usr/bin/env bash
# Nginx + Let's Encrypt for edusense.ru
# Run on VPS as root: bash /opt/edusense/deploy/adminvps/setup-domain.sh

set -euo pipefail

DOMAIN="${1:-edusense.ru}"
APP_DIR="/opt/edusense"
NGINX_SITE="/etc/nginx/sites-available/edusense"

echo "==> Nginx config for $DOMAIN"
sed "s/YOUR_DOMAIN.ru/${DOMAIN}/g" "$APP_DIR/deploy/adminvps/nginx-edusense.conf" > "$NGINX_SITE"
ln -sf "$NGINX_SITE" /etc/nginx/sites-enabled/edusense
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl reload nginx

echo "==> HTTPS (certbot)"
certbot --nginx -d "$DOMAIN" -d "www.$DOMAIN" --non-interactive --agree-tos --register-unsafely-without-email --redirect

echo "==> Done"
echo "  https://$DOMAIN/student"
echo "  https://$DOMAIN/teacher"
echo "  https://$DOMAIN/api/health"
