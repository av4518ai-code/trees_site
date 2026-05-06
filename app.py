from flask import Flask, render_template, request, jsonify, send_file, abort
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
import os
import re

# Инициализация Flask приложения
app = Flask(__name__)

# Пути к файлам
VOICE_MD_PATH = os.path.join(os.path.dirname(__file__), 'voice.md')
PDF_OUTPUT_PATH = os.path.join(os.path.dirname(__file__), 'theater_post.pdf')

# ------------------------------------------------------------------
# Регистрация шрифта Arial для поддержки кириллицы
# ------------------------------------------------------------------
def register_fonts():
    """
    Регистрирует шрифт Arial для корректного отображения русского текста.
    Пытается найти шрифт в системных папках Windows.
    """
    try:
        # Путь к шрифту Arial в Windows
        arial_path = "C:\\Windows\\Fonts\\arial.ttf"
        arial_bold_path = "C:\\Windows\\Fonts\\arialbd.ttf"
        
        if os.path.exists(arial_path):
            pdfmetrics.registerFont(TTFont('Arial', arial_path))
            print("Шрифт Arial зарегистрирован")
        else:
            print("Шрифт Arial не найден, используются стандартные шрифты")
            
        if os.path.exists(arial_bold_path):
            pdfmetrics.registerFont(TTFont('Arial-Bold', arial_bold_path))
    except Exception as e:
        print(f"Ошибка регистрации шрифта: {e}")

# Регистрируем шрифты при запуске
register_fonts()

# ------------------------------------------------------------------
# Вспомогательные функции для работы с voice.md
# ------------------------------------------------------------------

def read_voice_settings():
    """
    Читает настройки из voice.md.
    Если файл отсутствует, создает его со стандартными значениями.
    Возвращает словарь с настройками.
    """
    default_content = """# Настройки голоса для генерации постов театральных мероприятий

общий_тон: уютный, вдохновляющий, театральный
длина_поста: средняя
количество_эмодзи: 2
стиль_заголовка: восклицательный
дополнительные_указания: использовать театральные метафоры, упоминать атмосферу, кулисы, магию сцены
"""
    if not os.path.exists(VOICE_MD_PATH):
        with open(VOICE_MD_PATH, 'w', encoding='utf-8') as f:
            f.write(default_content)
        content = default_content
    else:
        with open(VOICE_MD_PATH, 'r', encoding='utf-8') as f:
            content = f.read()
    
    settings = {}
    # Парсим простые строки вида "ключ: значение"
    # Ищем строки, которые не являются комментариями (#) или пустыми
    for line in content.split('\n'):
        line = line.strip()
        if line and not line.startswith('#') and ':' in line:
            key, value = line.split(':', 1)
            settings[key.strip()] = value.strip()
    
    return settings

# ------------------------------------------------------------------
# Генератор постов
# ------------------------------------------------------------------

def generate_post_text(description, genre, mood, settings):
    """
    Генерирует текст поста на основе описания, жанра, настроения и настроек из voice.md.
    Формирует развернутый художественный анонс с театральными метафорами.
    """
    # Извлекаем настройки с дефолтными значениями
    tone = settings.get('общий_тон', 'вдохновляющий')
    length = settings.get('длина_поста', 'средняя')
    emoji_count = int(settings.get('количество_эмодзи', '2'))
    title_style = settings.get('стиль_заголовка', 'восклицательный')
    extra = settings.get('дополнительные_указания', '')
    
    # Набор эмодзи для театра
    emojis = ['🎭', '🎬', '✨', '🔥', '🌟', '🎻', '🎟️']
    
    # Формируем заголовок
    title_base = f"Анонс: {genre.capitalize()}"
    if title_style == 'восклицательный':
        title = f"{title_base}!"
    else:
        title = title_base
    
    # Добавляем эмодзи к заголовку
    post_emojis = ' '.join(emojis[:emoji_count])
    header = f"{post_emojis} {title} {post_emojis}"
    
    # Основной текст на основе настроения
    mood_map = {
        'вдохновляющее': 'Почувствуйте дыхание вдохновения! Это событие наполнит ваше сердце светом и теплом, напоминая, что искусство способно исцелять души. Каждый жест актеров, каждая нота в музыке — всё это части единой мозаики, зовущей к созиданию.',
        'таинственное': 'Мрак и тайны окутывают сцену. Приготовьтесь разгадать загадки, скрытые в тенях кулис. За каждым занавесом — своя история, за каждой маской — скрытое лицо. Истина где-то рядом, но ускользает, как туман в лучах софитов.',
        'дерзкое': 'Нарушая правила и ломая стереотипы, этот пост станет вызовом всему привычному! Мы переворачиваем сцену вверх дном, смешивая жанры и эпохи. Будьте готовы к тому, что привычный мир театра никогда не будет прежним.',
        'ностальгическое': 'Окунитесь в атмосферу прошлых лет, где каждое мгновение пропитано воспоминаниями. Старые афиши, запах гримерок, шелест шелковых платьев — всё это возвращает нас в золотую эру, когда театр был храмом для избранных.',
        'эпичное': 'Битвы, страсти и великие свершения ждут вас на самой грандиозной сцене этого сезона! Масштабные декорации, сотни костюмов и голоса, сотрясающие стены театра. Это не просто пост — это легенда, вписанная в историю искусства.'
    }
    
    mood_text = mood_map.get(mood, 'Незабываемое событие ждет вас.')
    
    # Вступление (общий тон)
    intro = f"Представьте атмосферу, где царит {tone}. Сцена готовится раскрыть свои объятия..."
    
    # Основное описание (то, что ввел пользователь, расширяем)
    main_desc = f"Сюжет разворачивается следующим образом: {description}. Каждый поворот сценария — это новая грань человеческой души, отраженная в зеркале театрального искусства."
    
    # Заключение
    outro = "Не упустите шанс стать частью этой магии. Купите билеты уже сегодня и позвольте театру изменить ваше восприятие реальности."
    
    # Дополнительные метафоры из настроек
    metaphor = f"\n\n{extra}" if extra else ""
    
    # Сборка тела поста в зависимости от длины
    if length == 'короткая':
        body = f"{main_desc}\n\n{outro}"
    elif length == 'средняя':
        body = f"{intro}\n\n{main_desc}\n\n{mood_text}\n\n{outro}"
    else: # длинная
        body = f"{intro}\n\n{main_desc}\n\n{mood_text}\n\nЗа кулисами кипит жизнь: гримеры создают образы, реквизиторы проверяют детали, а актеры пропускают роли через свои сердца.{metaphor}\n\n{outro}"
    
    # Финальная сборка
    post = f"{header}\n\n{body}\n\n#Театр #Искусство #{genre.capitalize()} #Анонс"
    return post

# ------------------------------------------------------------------
# Маршруты Flask
# ------------------------------------------------------------------

@app.route('/')
def index():
    """Главная страница с формой"""
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    """
    Обрабатывает запрос на генерацию поста.
    Принимает JSON: description, genre, mood.
    Возвращает JSON: {post: текст}
    """
    data = request.json
    description = data.get('description', '').strip()
    genre = data.get('genre', 'спектакль')
    mood = data.get('mood', 'вдохновляющее')
    
    # Валидация: описание обязательно
    if not description:
        return jsonify({'error': 'Описание мероприятия обязательно'}), 400
    
    # Читаем настройки голоса
    settings = read_voice_settings()
    
    # Генерируем текст
    post_text = generate_post_text(description, genre, mood, settings)
    
    return jsonify({'post': post_text})

@app.route('/save_pdf', methods=['POST'])
def save_pdf():
    """
    Принимает текст поста и генерирует PDF файл с поддержкой кириллицы и переносов.
    Использует SimpleDocTemplate и Paragraph для корректного рендеринга текста.
    Возвращает файл для скачивания.
    """
    data = request.json
    post_text = data.get('post', '').strip()
    
    if not post_text:
        return jsonify({'error': 'Нет текста для сохранения'}), 400
    
    try:
        # Создаем PDF документ с помощью Platypus (для автоматических переносов)
        # Используем SimpleDocTemplate для управления потоком документа
        doc = SimpleDocTemplate(
            PDF_OUTPUT_PATH,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm,
            # Устанавливаем темный фон (через canvas позже)
        )
        
        # Определяем стили с использованием зарегистрированного шрифта Arial
        # Проверяем, зарегистрирован ли шрифт, иначе используем Helvetica
        try:
            normal_font = 'Arial'
            bold_font = 'Arial-Bold'
        except:
            normal_font = 'Helvetica'
            bold_font = 'Helvetica-Bold'
        
        # Создаем стили для параграфов
        styles = getSampleStyleSheet()
        
        # Стиль для заголовка (тёмный для контраста)
        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Heading1'],
            fontName=bold_font,
            fontSize=18,
            textColor=HexColor('#4a148c'),  # Тёмно-фиолетовый
            spaceAfter=14,
            alignment=TA_LEFT
        )
        
        # Стиль для основного текста (чёрный для контраста на белом фоне)
        body_style = ParagraphStyle(
            'BodyStyle',
            parent=styles['Normal'],
            fontName=normal_font,
            fontSize=11,
            textColor=HexColor('#000000'),
            spaceAfter=12,
            leading=16,  # Межстрочный интервал
            alignment=TA_LEFT
        )
        
        # Стиль для даты
        date_style = ParagraphStyle(
            'DateStyle',
            parent=styles['Normal'],
            fontName=normal_font,
            fontSize=8,
            textColor=HexColor('#888888'),
            alignment=TA_LEFT
        )
        
        # Список элементов для добавления в PDF
        story = []
        
        # Добавляем заголовок
        story.append(Paragraph("Театральный Анонс", title_style))
        story.append(Spacer(1, 0.5*cm))
        
        # Обрабатываем текст поста: разбиваем на параграфы по переносам строк
        # Заменяем двойные переносы на новые параграфы
        paragraphs = post_text.split('\n')
        
        for para in paragraphs:
            if para.strip():  # Пропускаем пустые строки
                # Экранируем спецсимволы для XML (ReportLab использует XML-подобный синтаксис)
                para_escaped = para.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                story.append(Paragraph(para_escaped, body_style))
        
        # Добавляем дату внизу
        story.append(Spacer(1, 1*cm))
        from datetime import datetime
        date_str = datetime.now().strftime("%d.%m.%Y %H:%M")
        story.append(Paragraph(f"Сгенерировано: {date_str}", date_style))
        
        # Строим PDF
        doc.build(story)
        
        # Отправляем файл пользователю
        return send_file(
            PDF_OUTPUT_PATH, 
            as_attachment=True, 
            download_name='theater_post.pdf',
            mimetype='application/pdf'
        )
        
    except Exception as e:
        print(f"Ошибка при создании PDF: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Ошибка генерации PDF: {str(e)}'}), 500

# ------------------------------------------------------------------
# Запуск приложения
# ------------------------------------------------------------------

if __name__ == '__main__':
    # Убедимся, что voice.md существует при старте
    read_voice_settings()
    app.run(debug=True, port=5000)
