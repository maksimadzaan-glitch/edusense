# Автодеплой EduSense

После настройки: только `git push` — VPS обновляется сам.  
Панель AdminVPS не нужна.

## Разовая настройка (5 минут)

### 1. Секреты в GitHub

Открой:
https://github.com/maksimadzaan-glitch/edusense/settings/secrets/actions

Нажми **New repository secret** три раза:

| Name | Value |
|------|--------|
| `VPS_HOST` | `168.113.208.95` |
| `VPS_USER` | `root` |
| `VPS_PASSWORD` | пароль root от VPS (вставь из буфера) |

В поле Value для пароля: Ctrl+V — регистр не ломается, в отличие от панели провайдера.

### 2. Запушь код (вместе с workflow)

В PowerShell:

```powershell
cd "C:\Users\rusti\OneDrive\Рабочий стол\ege_tracker"
git add .
git commit -m "Add VPS autodeploy"
git push
```

### 3. Проверка

https://github.com/maksimadzaan-glitch/edusense/actions

Зелёная галочка = сайт на VPS обновлён.

---

## Каждый раз после правок

```powershell
cd "C:\Users\rusti\OneDrive\Рабочий стол\ege_tracker"
git add .
git commit -m "что поменял"
git push
```

Жди ~1 минуту на вкладке Actions.

## Запасной ручной деплой

Если GitHub Actions недоступен — скопируй пароль в буфер и:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\deploy.ps1
```
