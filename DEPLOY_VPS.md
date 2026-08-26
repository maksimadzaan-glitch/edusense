# EduSense — деплой на VPS (AdminVPS)

## 1. Заказ VPS

1. [adminvps.ru](https://adminvps.ru) → тариф **VPS** (Ubuntu 22.04 или 24.04).
2. Минимум: **1 vCPU, 1–2 GB RAM, 20 GB SSD**.
3. После создания в панели найдите:
   - **IP-адрес** сервера
   - **root-пароль** (или SSH-ключ)

## 2. DNS домена .ru

У регистратора домена:

| Тип | Имя | Значение |
|-----|-----|----------|
| A | `@` | IP вашего VPS |
| A | `www` | IP вашего VPS |

Подождите 5–30 минут.

## 3. Подключение по SSH

Windows (PowerShell):

```powershell
ssh root@ВАШ_IP
```

## 4. Установка приложения

```bash
cd /opt
git clone https://github.com/maksimadzaan-glitch/edusense.git
cd edusense
sudo bash deploy/adminvps/setup.sh
```

## 5. Переменные окружения

```bash
nano /opt/edusense/.env
```

Обязательно:

- `GIGACHAT_CREDENTIALS`
- `GIGACHAT_SCOPE=GIGACHAT_API_PERS`
- `GIGACHAT_MODEL=GigaChat-2`
- `TELEGRAM_BOT_TOKEN`
- `AI_PROVIDER=gigachat`

Опционально PostgreSQL (генерация вариантов):

```bash
sudo apt install -y postgresql postgresql-contrib
sudo -u postgres createuser edusense -P
sudo -u postgres createdb edusense_universal -O edusense
```

В `.env`:

```env
POSTGRES_URL=postgresql+psycopg://edusense:ПАРОЛЬ@localhost:5432/edusense_universal
```

Перезапуск:

```bash
sudo systemctl restart edusense
```

## 6. Nginx + HTTPS

Замените `edusense.ru` на ваш домен:

```bash
sudo sed 's/YOUR_DOMAIN.ru/edusense.ru/g' /opt/edusense/deploy/adminvps/nginx-edusense.conf | sudo tee /etc/nginx/sites-available/edusense
sudo ln -sf /etc/nginx/sites-available/edusense /etc/nginx/sites-enabled/edusense
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d edusense.ru -d www.edusense.ru
```

## 7. Проверка

- `https://ваш-домен.ru/api/health`
- `https://ваш-домен.ru/student`
- `https://ваш-домен.ru/teacher`

## 8. Telegram BotFather

- Mini App URL: `https://ваш-домен.ru/student`
- Menu Button: тот же URL

## Полезные команды

```bash
sudo systemctl status edusense
sudo journalctl -u edusense -f
cd /opt/edusense && git pull && sudo systemctl restart edusense
```
