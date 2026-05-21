# 🌳 Разведение плодовых деревьев для новичков

Сайт-путеводитель по плодовым деревьям для начинающих садоводов. Статьи генерируются языковой моделью через [ProxyAPI](https://proxyapi.ru).

## Возможности

- 8 карточек плодовых деревьев с адаптивной сеткой (1–3 колонки)
- Статьи с живым текстом: история, описание, шаги посадки, уход
- Генерация статей через LLM (Gemini / GPT / Claude) — уникальный контент под каждый запрос
- Сохранение статьи в PDF (через `html2pdf.js`)
- Стекломорфный дизайн: тёмный фон, blur-карточки, плавные анимации
- Адаптивность под мобильные, планшеты и десктоп
- Open Graph / Twitter Cards для расшаривания

## Технологии

- **Backend:** Python, Flask
- **AI:** ProxyAPI (OpenAI-совместимый эндпоинт)
- **Frontend:** CSS (glassmorphism), Intersection Observer, html2pdf.js
- **Шаблоны:** Jinja2

## Установка и запуск

```bash
# 1. Клонировать
git clone https://github.com/av4518ai-code/trees_site.git
cd trees_site

# 2. Установить зависимости
pip install flask python-dotenv openai

# 3. Создать .env с API-ключом ProxyAPI
echo "API_KEY=ваш_ключ" > .env
echo "MODEL=gpt-5.5" >> .env

# 4. Запустить
python app.py
```

Откройте http://localhost:5000 в браузере.

## Переменные окружения (.env)

| Переменная  | Описание                    | По умолчанию |
|-------------|-----------------------------|--------------|
| `API_KEY`   | Ключ ProxyAPI               | (обязателен) |
| `MODEL`     | Модель для генерации статей | `gpt-5.5`    |

## Структура проекта

```
flask_site/
├── app.py              # Flask-приложение, маршруты, генерация статей
├── .env                # API-ключ и настройки (в gitignore)
├── .gitignore
├── README.md
├── templates/
│   ├── index.html      # Главная с сеткой карточек
│   └── article.html    # Страница статьи с PDF-кнопкой
└── static/
    ├── style.css       # Стили (тёмная тема, glassmorphism)
    └── script.js       # Intersection Observer для появления карточек
```
