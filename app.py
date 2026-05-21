import os
import json
from flask import Flask, render_template
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

app = Flask(__name__)

API_KEY = os.getenv('API_KEY')
MODEL = os.getenv('MODEL', 'gpt-5.5')
PROXY_API_URL = 'https://api.proxyapi.ru/openai/v1'

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

    # Очистка от markdown-обёртки если модель её добавила
    if content.startswith('```'):
        lines = content.split('\n')
        content = '\n'.join(lines[1:-1]) if len(lines) > 2 else lines[1].removeprefix('json')

    return json.loads(content)


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


if __name__ == '__main__':
    app.run(debug=True, port=5000)
