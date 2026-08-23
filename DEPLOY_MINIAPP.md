# EduSense — Telegram Mini App (к 15–16 августа)

Один и тот же FastAPI-бэкенд отдаёт обычный сайт и Mini App. Отдельный фронт не нужен.

## Что уже в коде

- `/student` — кабинет ученика (сайт + Mini App)
- `/teacher` — панель учителя (удобна на телефоне; можно открыть и как WebApp)
- Bootstrap: `telegram-web-app.js` + `/js/telegram_webapp.js`
  - `ready()` / `expand()`
  - лёгкая подстановка `themeParams` в CSS-переменные
  - вход по `?code=` и по `start_param` (deep link Mini App)
  - в работе ученика — Telegram **MainButton** «Сдать работу»
- Токен бота **не обязателен** для открытия UI. `TELEGRAM_BOT_TOKEN` — опционально, для будущей проверки `initData`.

## Что нужно вам (хостинг + BotFather)

### 1. HTTPS-URL в интернет

Telegram Mini App **не открывается** с `localhost` без туннеля.

Варианты:

- VPS / Render / Fly / Railway + HTTPS
- или временно [ngrok](https://ngrok.com) / Cloudflare Tunnel на локальный сервер

Публичный корень должен отдавать тот же backend:

- `https://ваш-домен/` — лендинг
- `https://ваш-домен/student` — ученик (URL Mini App)
- `https://ваш-домен/teacher` — учитель
- `https://ваш-домен/api/health` — проверка

### 2. BotFather

1. Создайте бота (`/newbot`), сохраните токен.
2. `/newapp` → выберите бота → название/описание/иконка.
3. **Web App URL** = `https://ваш-домен/student`
4. (Опционально) Menu Button бота → тот же URL.
5. Токен положите в `.env` как `TELEGRAM_BOT_TOKEN=...` (пока только заготовка; валидация initData — позже).

### 3. Deep link с кодом класса/работы

После привязки Mini App:

```text
https://t.me/<bot_username>/<app_short_name>?startapp=EDU-XXXX
```

`startapp` попадёт в `WebApp.initDataUnsafe.start_param` и подставится в код входа (как `?code=`).

Обычная ссылка сайта тоже работает:

```text
https://ваш-домен/student?code=EDU-XXXX
```

## Чеклист к 15–16 августа

- [ ] Backend с HTTPS доступен с телефона (не только Wi‑Fi дома)
- [ ] `/student` открывается в браузере телефона и десктопа
- [ ] Hamburger-меню на узком экране работает (ученик + учитель)
- [ ] BotFather: Mini App URL = `https://…/student`
- [ ] Открыть Mini App из Telegram → экран входа/кабинета без белого экрана
- [ ] `?code=` и/или `startapp=` подставляют код
- [ ] Сдать работу: кнопка на странице и/или MainButton внизу Telegram
- [ ] Учитель может выдать работу и открыть ссылку ученику
- [ ] (Желательно) `TELEGRAM_BOT_TOKEN` в `.env` на проде
- [ ] (Позже) серверная проверка `initData` — не блокер демо

## Локальная проверка сейчас (без Telegram)

```bash
# из корня репозитория
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Открыть:

- http://127.0.0.1:8000/student
- DevTools → mobile viewport → проверить меню и отсутствие горизонтального скролла

Для проверки именно внутри Telegram нужен HTTPS-туннель + BotFather URL.
