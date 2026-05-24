import os
import json
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from openai import OpenAI
import requests as http_requests

load_dotenv()

app = Flask(__name__)

API_KEY = os.getenv('API_KEY')
MODEL = os.getenv('MODEL', 'gpt-5.5')
PROXY_API_URL = 'https://api.proxyapi.ru/openai/v1'

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# Кэш для сгенерированных статей (чтобы не дёргать API на каждый заход)
article_cache = {}

# Базовая информация о деревьях (статьи генерируются через API)
trees = [
    {'id': 'apple', 'name': 'Яблоня «Мелба»', 'emoji': '🍎', 'short_desc': 'Сочная, ароматная, созревает в августе.'},
    {'id': 'pear', 'name': 'Груша «Лада»', 'emoji': '🍐', 'short_desc': 'Неприхотливая, сладкая, для средней полосы.'},
    {'id': 'cherry', 'name': 'Вишня «Молодёжная»', 'emoji': '🍒', 'short_desc': 'Обильный урожай, устойчива к морозам.'},
    {'id': 'plum', 'name': 'Слива «Заречная ранняя»', 'emoji': '🟣', 'short_desc': 'Крупные тёмно-фиолетовые плоды.'},
    {'id': 'apricot', 'name': 'Абрикос «Краснощёкий»', 'emoji': '🍑', 'short_desc': 'Самоопыляемый, отлично для юга.'},
    {'id': 'peach', 'name': 'Персик «Киевский ранний»', 'emoji': '🍑', 'short_desc': 'Для начинающих, устойчив к болезням.'},
    {'id': 'sweet_cherry', 'name': 'Черешня «Ипуть»', 'emoji': '🍒', 'short_desc': 'Тёмно-красная, сладкая, зимостойкая.'},
    {'id': 'fig', 'name': 'Инжир «Брунсвик»', 'emoji': '🍈', 'short_desc': 'Для домашнего сада и контейнеров.'}
]

def generate_article(tree):
    """Генерирует статью о дереве через ProxyAPI"""
    prompt = f'''Ты — опытный садовод и агроном. Напиши статью о плодовом дереве "{tree['name']}" для начинающих.
Верни ТОЛЬКО JSON (без markdown, без пояснений) в формате:
{{
    "intro": "вступительный абзац — история, почему сорт популярен",
    "details": "подробное описание дерева, плодов, вкуса, урожайности",
    "steps": ["шаг 1", "шаг 2", "шаг 3", "шаг 4"],
    "care": ["совет 1", "совет 2", "совет 3"],
    "image_placeholder": "подпись под заглушкой изображения"
}}
Сделай текст живым, с разной эмоциональной окраской — то восторженно, то спокойно-поучительно.'''

    client = OpenAI(api_key=API_KEY, base_url=PROXY_API_URL)

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{'role': 'user', 'content': prompt}],
        temperature=1.0,
        max_completion_tokens=1500
    )

    content = response.choices[0].message.content.strip()

    if content.startswith('```'):
        lines = content.split('\n')
        content = '\n'.join(lines[1:-1]) if len(lines) > 2 else lines[1].removeprefix('json')

    return json.loads(content)


def publish_to_telegram(tree, article):
    """Отправляет статью в Telegram группу"""
    if not TELEGRAM_BOT_TOKEN or 'your_bot_token' in TELEGRAM_BOT_TOKEN:
        return {'ok': False, 'error': 'TELEGRAM_BOT_TOKEN не настроен'}

    if not TELEGRAM_CHAT_ID or 'your_chat_id' in TELEGRAM_CHAT_ID:
        return {'ok': False, 'error': 'TELEGRAM_CHAT_ID не настроен'}

    escapes = {'<': '&lt;', '>': '&gt;', '&': '&amp;', '"': '&quot;'}

    def h(text):
        return ''.join(escapes.get(c, c) for c in text)

    msg = f'''<b>{tree['emoji']} {h(tree['name'])}</b>

{h(article['intro'])}

{h(article['details'])}

<b>🌱 Шаги посадки:</b>
{chr(10).join(f'{i+1}. {h(s)}' for i, s in enumerate(article['steps']))}

<b>🛠️ Уход:</b>
{chr(10).join(f'— {h(c)}' for c in article['care'])}'''

    url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': msg,
        'parse_mode': 'HTML',
        'disable_web_page_preview': True
    }

    try:
        resp = http_requests.post(url, data=payload, timeout=15)
        data = resp.json()
        if data.get('ok'):
            return {'ok': True}
        else:
            return {'ok': False, 'error': data.get('description', 'Неизвестная ошибка Telegram')}
    except Exception as e:
        return {'ok': False, 'error': str(e)}


@app.route('/')
def index():
    """Главная страница со списком деревьев"""
    return render_template('index.html', trees=trees)


@app.route('/article/<tree_id>')
def article(tree_id):
    """Страница статьи о дереве (генерируется через API)"""
    tree = next((t for t in trees if t['id'] == tree_id), None)
    if tree is None:
        return 'Статья не найдена', 404

    if tree_id not in article_cache:
        try:
            article_cache[tree_id] = generate_article(tree)
        except Exception as e:
            return f'Ошибка генерации статьи: {e}', 500

    return render_template('article.html', tree=tree, article=article_cache[tree_id])


@app.route('/publish/<tree_id>', methods=['POST'])
def publish(tree_id):
    """Публикует статью в Telegram"""
    tree = next((t for t in trees if t['id'] == tree_id), None)
    if tree is None:
        return jsonify({'ok': False, 'error': 'Дерево не найдено'}), 404

    if tree_id not in article_cache:
        try:
            article_cache[tree_id] = generate_article(tree)
        except Exception as e:
            return jsonify({'ok': False, 'error': f'Ошибка генерации: {e}'}), 500

    result = publish_to_telegram(tree, article_cache[tree_id])
    status = 200 if result['ok'] else 400
    return jsonify(result), status


if __name__ == '__main__':
    app.run(debug=True, port=5000)
