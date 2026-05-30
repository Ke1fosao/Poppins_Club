# 🚀 Деплой Poppins Club на PythonAnywhere (безкоштовно)

Покрокова інструкція, як підняти сайт на безкоштовному хостингу PythonAnywhere. Підходить для портфоліо й демо.

---

## 📋 Перед початком

- Аккаунт на [https://www.pythonanywhere.com](https://www.pythonanywhere.com) — безкоштовний тариф "Beginner"
- Код залитий у GitHub: `https://github.com/Ke1fosao/Poppins_Club`
- Згенеруйте новий Django `SECRET_KEY` тут: [https://djecrety.ir/](https://djecrety.ir/) — запишіть, знадобиться нижче

---

## 1. Створіть аккаунт PythonAnywhere

1. Перейдіть на [pythonanywhere.com](https://www.pythonanywhere.com) → **Pricing & signup** → **Create a Beginner account**
2. Виберіть username (буде у домені: `username.pythonanywhere.com`). У прикладах нижче — `ke1fosao`.
3. Підтвердіть email

---

## 2. Клонуйте репозиторій

1. Відкрийте **Dashboard** → **Consoles** → запустіть **Bash**
2. У консолі:
```bash
cd ~
git clone https://github.com/Ke1fosao/Poppins_Club.git
cd Poppins_Club
```

---

## 3. Створіть virtualenv і встановіть залежності

```bash
# Перевірте версію Python (на PA є 3.11/3.12/3.13)
python3.13 --version

# Створити virtualenv
mkvirtualenv --python=python3.13 poppins-env

# Тепер активний; підказка покаже (poppins-env) $
# Якщо вискочили — активувати знову:
# workon poppins-env

# Встановити залежності бекенду
cd ~/Poppins_Club/backend
pip install -r requirements.txt
```

---

## 4. Фронтенд уже зібраний у репозиторії ✓

**Важливо:** PythonAnywhere безкоштовний тариф НЕ має `npm`. Тому фронт збираємо локально на своєму ПК (один раз перед деплоєм) і пушимо вже зібраний `frontend/dist/` у репо. На PA просто `git pull` і все.

Якщо ви тільки клонували репо на PA — `dist/` уже там. Переходьте до кроку 5.

### Якщо потрібно перебудувати фронт (зміни в коді)

На своєму локальному ПК:
```bash
cd frontend
npm run build
git add frontend/dist
git commit -m "rebuild frontend"
git push
```

А потім на PA:
```bash
cd ~/Poppins_Club
git pull
cp frontend/dist/index.html backend/templates/index.html
# і потім Reload Web App у PA дашборді
```

---

## 5. `index.html` уже на місці ✓

`backend/templates/index.html` тепер **зберігається в репозиторії вже зібраним** (синхронізований
із `frontend/dist/index.html`). Тому копіювати вручну **НЕ треба** — після `git pull` він уже правильний.

> ⚠️ **Не робіть `cp ... templates/index.html` на сервері!** Це створює локальну зміну
> відстежуваного файлу, через яку наступний `git pull` падає з помилкою
> *«Your local changes would be overwritten by merge»*. Якщо вже зробили — див. Troubleshooting нижче.

---

## 6. Налаштування production env-змінних

Створіть файл з налаштуваннями:
```bash
cd ~/Poppins_Club/backend
nano .env  # або vim
```

Введіть (замініть `ke1fosao` на свій username та `YOUR_NEW_SECRET_KEY` на згенерований):

```env
DJANGO_SECRET_KEY=YOUR_NEW_SECRET_KEY
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=ke1fosao.pythonanywhere.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://ke1fosao.pythonanywhere.com

# ШІ-помічник (Google Gemini)
GEMINI_API_KEY=ваш_ключ_gemini

# Telegram-бот сповіщень (див. розділ «Telegram-бот» нижче)
TELEGRAM_BOT_TOKEN=токен_від_BotFather
TELEGRAM_WEBHOOK_SECRET=будь_який_довгий_випадковий_рядок
SITE_BASE_URL=https://ke1fosao.pythonanywhere.com
# TELEGRAM_ALLOWED_IDS=123456789   # (необов'язково) обмежити бот лише вашим Telegram id
```

Збережіть (`Ctrl+O`, `Enter`, `Ctrl+X` у nano).

> 🔒 `.env` у git **не потрапляє** — секрети живуть лише на сервері.

---

## 7. Міграції + статика + суперюзер

```bash
cd ~/Poppins_Club/backend

# Експортуємо env у поточну сесію (для команд нижче)
export $(cat .env | xargs)

# Міграції БД (з нульового стану це створить таблиці + засіє контент)
python manage.py migrate

# Створити адміна для входу у /admin/
python manage.py createsuperuser
# Введіть username, email, password

# Зібрати весь статичний контент у backend/staticfiles/
python manage.py collectstatic --noinput
```

---

## 8. Створіть Web App у PA

1. **Dashboard** → **Web** → **Add a new web app**
2. Domain: залишити дефолтний `ke1fosao.pythonanywhere.com` → **Next**
3. Виберіть **Manual configuration** (НЕ "Django"!)
4. Python version: **3.13** (або яку ви ставили у virtualenv) → **Next**
5. Готово

---

## 9. Налаштування Web App

На сторінці вашого Web App пройдіться по налаштуваннях:

### 9.1 Code
- **Source code**: `/home/ke1fosao/Poppins_Club/backend`
- **Working directory**: `/home/ke1fosao/Poppins_Club/backend`

### 9.2 Virtualenv
- Введіть: `/home/ke1fosao/.virtualenvs/poppins-env`

### 9.3 WSGI configuration file
Клікніть на посилання `/var/www/ke1fosao_pythonanywhere_com_wsgi.py` і ЦІЛКОМ замініть вміст на:

```python
import os
import sys

# ---- Path ----
project_path = '/home/ke1fosao/Poppins_Club/backend'
if project_path not in sys.path:
    sys.path.insert(0, project_path)

# ---- Env vars (production) ----
os.environ['DJANGO_SECRET_KEY'] = 'PASTE_YOUR_GENERATED_SECRET_KEY_HERE'
os.environ['DJANGO_DEBUG'] = 'False'
os.environ['DJANGO_ALLOWED_HOSTS'] = 'ke1fosao.pythonanywhere.com'
os.environ['DJANGO_CSRF_TRUSTED_ORIGINS'] = 'https://ke1fosao.pythonanywhere.com'

os.environ['DJANGO_SETTINGS_MODULE'] = 'zdo_project.settings'

# ---- Django ----
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

> Замініть `ke1fosao` на ваш username усюди.
> Збережіть (Ctrl+S чи кнопка Save вгорі).
>
> 💡 `GEMINI_API_KEY`, `TELEGRAM_BOT_TOKEN` тощо **не потрібно** дублювати тут — вони
> автоматично читаються з `backend/.env` (крок 6). Тут лишіть лише Django-змінні вище.

### 9.4 Static files (mapping)
Прокрутіть до секції **Static files** і додайте **3 рядки**:

| URL | Directory |
|---|---|
| `/static/` | `/home/ke1fosao/Poppins_Club/backend/staticfiles/` |
| `/media/` | `/home/ke1fosao/Poppins_Club/backend/media/` |
| `/assets/` | `/home/ke1fosao/Poppins_Club/frontend/dist/assets/` |

> Перший — Django static (CSS адмінки тощо), другий — завантажені фото, третій — JS/CSS збірки фронта.

### 9.5 Перезапустіть Web App
Натисніть велику зелену кнопку **🔄 Reload ke1fosao.pythonanywhere.com** угорі сторінки.

---

## 10. Готово!

Відкрийте `https://ke1fosao.pythonanywhere.com` — сайт повинен запрацювати.

- `/` — головна
- `/anketa` — анкета
- `/admin/` — адмін-панель (увійти суперюзером з кроку 7)
- `/api/content/` — JSON всіх даних сайту

---

## 11. 🔔 Telegram-бот сповіщень (один раз)

Бот надсилає кожну нову заявку/повідомлення у Telegram і дозволяє міняти статус кнопками.

1. **Створіть бота** у [@BotFather](https://t.me/BotFather) → `/newbot` → отримаєте **токен**.
2. **Додайте у `backend/.env`** (крок 6):
   ```env
   TELEGRAM_BOT_TOKEN=токен_від_BotFather
   TELEGRAM_WEBHOOK_SECRET=довгий_випадковий_рядок
   SITE_BASE_URL=https://ke1fosao.pythonanywhere.com
   ```
3. **Зареєструйте webhook** (один раз, у PA Bash console):
   ```bash
   workon poppins-env
   cd ~/Poppins_Club/backend
   python manage.py telegram_webhook set https://ke1fosao.pythonanywhere.com
   # перевірити: python manage.py telegram_webhook info
   ```
4. **Напишіть боту `/start`** — і ви почнете отримувати сповіщення. Готово!

> Безкоштовний PA дозволяє webhook (вхідний HTTPS), тому постійний процес НЕ потрібен.
> Якщо змінили токен/секрет — повторіть крок 3 та зробіть **Reload**.

---

## 🔄 Як оновлювати сайт пізніше

Фронтенд збираєте **локально** (`npm run build`) і пушите разом із `frontend/dist/` та
синхронізованим `backend/templates/index.html`. На PA — лише `git pull`:

```bash
# Відкрийте PA Bash console:
workon poppins-env
cd ~/Poppins_Club

git pull

cd backend
pip install -r requirements.txt   # лише якщо додалися залежності
python manage.py migrate          # якщо є нові міграції
python manage.py collectstatic --noinput   # лише якщо чіпали Django-статику

# Перезапустити Web App: Dashboard → Web → Reload
```

> ❗ **НЕ виконуйте `cp ... templates/index.html`** — файл уже зібраний у репозиторії.
> Ручне копіювання ламає наступний `git pull`.

---

## 🐛 Troubleshooting

### Помилка `DisallowedHost`
У `DJANGO_ALLOWED_HOSTS` (як у `.env`, так і у WSGI-файлі) має бути ваш домен на PA, наприклад:
```
ke1fosao.pythonanywhere.com
```

### Помилка `404 на /admin/static`
Перевірте, що **Static files mapping** у PA Web дашборді налаштований. Перезапустіть Web App.

### `git pull` падає: *«Your local changes to backend/templates/index.html would be overwritten»*
Так буває, якщо колись копіювали `index.html` вручну (`cp`) — створилася локальна зміна
відстежуваного файлу. Приберіть її та повторіть pull:
```bash
cd ~/Poppins_Club
git checkout -- backend/templates/index.html
git pull
cd backend && python manage.py migrate
# Dashboard → Web → Reload
```
Більше `cp` робити не треба — файл приходить уже зібраним із `git pull`.

### Сайт показує стару версію після оновлення
Майже завжди це означає, що `git pull` **не завершився** (див. помилку вище) — перевірте,
що `git log -1` показує найновіший коміт. Також зробіть **Reload** у Web-дашборді та
оновіть сторінку в браузері з `Ctrl+F5` (скидання кешу).

### `npm: command not found` на PA
Це нормально — PA безкоштовний тариф не має Node.js. Збирайте фронт **локально** на своєму ПК і пушите `frontend/dist/` у репо разом з кодом. На PA — тільки `git pull`. У цьому проєкті `dist/` уже не у `.gitignore` і пушиться разом з усім.

### ШІ-помічник пише "API ключ відсутній"
`VITE_GEMINI_API_KEY` має бути у `frontend/.env.production` ДО запуску `npm run build`. Якщо змінили — перебудуйте фронт.

### Карта Google Maps не відображається
Зайдіть в адмінку → **Контакти та Соцмережі** → поле "Посилання на карту" → вставте src з iframe Google Maps або повний iframe-тег. Сервер сам витягне src.

### Логи помилок
Web → секція **Log files** → відкрити `Error log` і `Server log`.

---

## 💡 Підказки

- **CPU секунди** на free тарифі обмежені; не запускайте Node.js-білди дуже часто.
- Безкоштовний акаунт PA "засинає" через 3 місяці неактивності — раз на 2-3 місяці заходьте у Web дашборд і клікайте **Run until 3 months from today**.
- Можна підключити свій домен на платних тарифах.
- Для продакшн-навантаження краще використати MySQL замість SQLite — PA дає 1 MySQL базу безкоштовно.

---

Made with ❤ by Kovtunovych Dmytro Valeriyovych
