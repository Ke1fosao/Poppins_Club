# Poppins Club — сайт приватного дитячого садочка

Сучасний веб-сайт для приватного дитячого садочка з повноцінною адмін-панеллю керування контентом та інтегрованим ШІ-помічником на базі Google Gemini.

🇺🇦 Built in Ukraine · Designed & Developed by **Kovtunovych Dmytro Valeriiovych**

---

## ✨ Можливості

- 🎨 **Сучасний дизайн** — Tailwind CSS, плавні анімації, повністю адаптивний (мобілка / планшет / десктоп)
- 🛠 **Повне керування з адмінки** — всі тексти, фото, секції, картки, FAQ, групи редагуються без правки коду
- 🤖 **ШІ-помічник** — Google Gemini знає всю інформацію про садочок з БД (контакти, FAQ, групи, ціни)
- 📝 **Анкета попередньої реєстрації** — 6 кроків, окрема сторінка `/anketa`, валідація на кожному кроці
- 📧 **Контактна форма** — захист від спаму (honeypot + rate-limit + time-of-load + серверна валідація)
- 🖼 **Галереї фото** — карусель приміщень з drag/swipe, колаж напрямків, hero photo
- 🗺 **Google Maps** — тоlerantно парсить будь-який формат (повний iframe, markdown, URL)
- 🔐 **GDPR-чекбокс** — згода на обробку персональних даних на всіх формах

## 🏗 Архітектура

```
┌──────────────────┐         ┌─────────────────────┐
│  React + Vite    │  HTTP   │  Django + DRF       │
│  (frontend/)     │ ◄─────► │  (backend/)         │
│  Tailwind CSS    │  /api/* │  SQLite             │
└──────────────────┘         └─────────────────────┘
        │                              │
        └──── Google Gemini API ◄──────┘
              (ШІ-помічник)
```

## 🚀 Локальний запуск

### Передумови
- Python 3.11+
- Node.js 20+
- npm

### 1. Клонувати репозиторій
```bash
git clone https://github.com/Ke1fosao/Poppins_Club.git
cd Poppins_Club
```

### 2. Backend (Django)
```bash
cd backend

# Створити virtualenv
python -m venv ../.venv
# Windows:
..\.venv\Scripts\activate
# Linux/Mac:
source ../.venv/bin/activate

# Встановити залежності
pip install -r requirements.txt

# Застосувати міграції (вже містять початкові дані: секції, картки, групи, FAQ)
python manage.py migrate

# Створити суперюзера для входу в /admin/
python manage.py createsuperuser

# Запустити dev-сервер
python manage.py runserver
```
Бекенд буде на `http://127.0.0.1:8000/`, адмінка — `http://127.0.0.1:8000/admin/`.

### 3. Frontend (React + Vite)
У новому терміналі:
```bash
cd frontend
npm install

# Скопіюйте .env.example → .env та заповніть VITE_GEMINI_API_KEY
cp .env.example .env
# або вручну скопіювати у Windows

npm run dev
```
Фронтенд буде на `http://localhost:5173/`.

## 🎛 Що можна редагувати з адмінки

| Розділ адмінки | Що змінюється |
|---|---|
| **1. Контакти та Соцмережі** | Телефон, email, адреса, карта, FB/IG/YT, логотипи, текст у шапці й футері |
| **2. Тексти розділів** | Всі заголовки/описи кожної секції, hero-фото, бейдж досвіду, тези про садочок |
| **3. Про нас — картки** | 3 переваги (заголовок, опис, іконка, колір) |
| **4. Напрямки розвитку** | 4 картки розподілені на 2 ряди (картка + опис + іконка + колір) |
| **4а. Фото каруселі (ряд 1)** | Фото 16:9 з порядком |
| **4б. Фото колажу (ряд 2)** | 3 фіксовані позиції з конкретними аспектами |
| **5. Приміщення — слайди з фото** | Карусель приміщень |
| **6. Вікові групи** | Назва, вік, опис, особливості (списком), іконка, «найпопулярніша» |
| **7. Питання та Відповіді** | FAQ з порядком |
| **Анкети (Заявки)** | Всі заявки з 6-крокової анкети, згруповані по кроках |
| **Повідомлення з сайту** | Заявки з контактної форми |

## 🔧 Технічний стек

**Frontend:**
- React 19, Vite 8
- Tailwind CSS 3
- lucide-react (іконки)
- Vanilla History API routing

**Backend:**
- Django 6
- Django REST Framework
- Pillow (зображення)
- WhiteNoise (статика в проді)
- django-cors-headers

**External:**
- Google Gemini API (ШІ-помічник)

## 📦 Деплой

Інструкція для PythonAnywhere — у файлі [DEPLOY.md](./DEPLOY.md).

## 📁 Структура проєкту

```
Poppins_Club/
├── backend/                  # Django проєкт
│   ├── api/                  # Основний додаток: моделі, views, admin
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── admin.py
│   │   └── migrations/
│   ├── zdo_project/          # Конфіг Django
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── media/logo/           # Логотипи (включено в репо)
│   ├── templates/
│   │   └── index.html        # Placeholder, у проді заміняється білдом фронта
│   ├── manage.py
│   └── requirements.txt
├── frontend/                 # React + Vite
│   ├── src/
│   │   ├── App.jsx           # Усе в одному файлі
│   │   ├── main.jsx
│   │   └── index.css
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── .env.example
│   └── .env.production
├── .gitignore
├── README.md
└── DEPLOY.md                 # PythonAnywhere крок-за-кроком
```

## 📄 Ліцензія

Цей проєкт зроблений як портфоліо-робота. Якщо ви — садочок Poppins Club або хочете використати цей шаблон — зв'яжіться з автором.

---

Made with ❤ by **Kovtunovych Dmytro Valeriiovych**
