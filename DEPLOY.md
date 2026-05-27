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

## 4. Збудуйте фронтенд

PythonAnywhere має Node.js на безкоштовному тарифі (трохи старий, але достатній для білда Vite).

```bash
# Активуйте virtualenv якщо вилетіли
workon poppins-env

cd ~/Poppins_Club/frontend

# Встановити залежності (займе 1-2 хвилини)
npm install

# Білд
npm run build
```

Якщо `npm install` падає через нестачу пам'яті — спробуйте з прапором:
```bash
NODE_OPTIONS=--max-old-space-size=512 npm install --no-audit --no-fund
```

Після білда в `frontend/dist/` буде:
- `index.html`
- `assets/index-XXXX.js`
- `assets/index-XXXX.css`

---

## 5. Скопіюйте `index.html` у Django templates

Django повинен віддавати `index.html` як головну сторінку. Скопіюйте файл у `backend/templates/`:

```bash
cp ~/Poppins_Club/frontend/dist/index.html ~/Poppins_Club/backend/templates/index.html
```

> Цю команду треба повторювати щоразу, коли ви наново перебудовуєте фронт.

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
```

Збережіть (`Ctrl+O`, `Enter`, `Ctrl+X` у nano).

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

## 🔄 Як оновлювати сайт пізніше

```bash
# Відкрийте PA Bash console:
workon poppins-env
cd ~/Poppins_Club

# Підтягнути зміни з GitHub
git pull

# Якщо змінювали бекенд:
cd backend
pip install -r requirements.txt   # якщо додалися залежності
python manage.py migrate          # якщо є нові міграції
python manage.py collectstatic --noinput

# Якщо змінювали фронтенд:
cd ../frontend
npm install                       # якщо змінився package.json
npm run build
cp dist/index.html ../backend/templates/index.html

# Перезапустити Web App
# Dashboard → Web → Reload button
```

---

## 🐛 Troubleshooting

### Помилка `DisallowedHost`
У `DJANGO_ALLOWED_HOSTS` (як у `.env`, так і у WSGI-файлі) має бути ваш домен на PA, наприклад:
```
ke1fosao.pythonanywhere.com
```

### Помилка `404 на /admin/static`
Перевірте, що **Static files mapping** у PA Web дашборді налаштований. Перезапустіть Web App.

### `index.html` показує "Збірка фронтенду відсутня"
Не виконано крок 5 — копіювання `frontend/dist/index.html` → `backend/templates/index.html`.

### `npm install` падає на free PA
PA безкоштовний тариф обмежений по CPU/RAM. Спробуйте:
```bash
NODE_OPTIONS=--max-old-space-size=512 npm install --no-audit --no-fund --legacy-peer-deps
```
Якщо не виходить — зробіть `npm run build` локально, закомітьте `frontend/dist/` у репо (тимчасово прибравши з `.gitignore`), і на PA робіть тільки `git pull` без `npm`.

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

Made with ❤ by Kovtunovych Dmytro Valeriiovych
