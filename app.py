import os
import socket
import sqlite3
import requests
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, render_template_string
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'dulaty_samgau_super_secure_key_2026'

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'mp4', 'mp3', 'wav', 'doc', 'docx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Telegram Бот баптаулары
TELEGRAM_BOT_TOKEN = '9039294267:AAFKlaNgBvqDJbZjhFuJSsFAa90vtRL0o34'
TELEGRAM_CHAT_ID = '7722421089'


def send_telegram_message_with_keyboard(text, reply_markup=None):
    """Telegram ботқа батырмалары бар хабарлама жіберу"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text,
            "parse_mode": "HTML"
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print("Telegram хабарлама қатесі:", e)


def send_telegram_message(text):
    send_telegram_message_with_keyboard(text)


def send_telegram_document(file_path, caption=""):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"
        with open(file_path, 'rb') as f:
            files = {'document': f}
            data = {
                "chat_id": TELEGRAM_CHAT_ID,
                "caption": caption,
                "parse_mode": "HTML"
            }
            requests.post(url, data=data, files=files, timeout=10)
    except Exception as e:
        print("Telegram файл жіберу қатесі:", e)


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"


def init_db():
    conn = sqlite3.connect('samgau.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS proposals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            full_name TEXT NOT NULL,
            faculty TEXT NOT NULL,
            specialty TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT NOT NULL,
            file_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT NOT NULL,
            file_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()


init_db()


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_date_filter(period):
    now = datetime.now()
    if period == 'day':
        start_date = now.strftime('%Y-%m-%d 00:00:00')
    elif period == 'week':
        start_date = (now - timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')
    elif period == 'month':
        start_date = (now - timedelta(days=30)).strftime('%Y-%m-%d %H:%M:%S')
    elif period == 'year':
        start_date = (now - timedelta(days=365)).strftime('%Y-%m-%d %H:%M:%S')
    else:
        start_date = '2000-01-01 00:00:00'
    return start_date


@app.route('/')
def index():
    local_ip = get_local_ip()
    server_url = f"http://{local_ip}:5000"
    return render_template('index.html', server_url=server_url)


@app.route('/proposal', methods=['GET', 'POST'])
def proposal():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        full_name = request.form['full_name']
        faculty = request.form['faculty']
        specialty = request.form['specialty']  # Курс таңдауы (мысалы, "1-курс", "2-курс" т.б.)
        phone = request.form['phone']
        email = request.form['email']

        file = request.files.get('file')

        if not file or file.filename == '':
            flash('Қате! Ұсыныс жіберу үшін PDF презентацияны міндетті түрде тіркеу қажет.', 'danger')
            return redirect(url_for('proposal'))

        if not allowed_file(file.filename):
            flash('Қате! Рұқсат етілмеген файл форматы.', 'danger')
            return redirect(url_for('proposal'))

        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        conn = sqlite3.connect('samgau.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO proposals (title, description, full_name, faculty, specialty, phone, email, file_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (title, description, full_name, faculty, specialty, phone, email, file_path))
        conn.commit()
        conn.close()

        tg_text = (
            f"🚀 <b>ЖАҢА ҰСЫНЫС / СТАРТАП!</b>\n\n"
            f"📌 <b>Тақырыбы:</b> {title}\n"
            f"📝 <b>Сипаттамасы:</b> {description}\n\n"
            f"👤 <b>Автор:</b> {full_name}\n"
            f"🏛 <b>Мектеп:</b> {faculty}\n"
            f"🎓 <b>Курсы:</b> {specialty}\n"
            f"📞 <b>Телефон:</b> {phone}\n"
            f"📧 <b>Email:</b> {email}"
        )
        send_telegram_message(tg_text)

        if file_path and os.path.exists(file_path):
            send_telegram_document(file_path, caption=f"📄 {full_name} жіберген презентация/файл")

        flash('Ұсынысыңыз сәтті сақталды және Telegram ботқа жіберілді!', 'success')
        return redirect(url_for('index'))
    return render_template('proposal.html')


@app.route('/complaint', methods=['GET', 'POST'])
def complaint():
    if request.method == 'POST':
        description = request.form['description']
        file = request.files.get('file')

        if not file or file.filename == '':
            flash('Қате! Шағым жіберу үшін дәлелдеме файлды тіркеу қажет.', 'danger')
            return redirect(url_for('complaint'))

        if not allowed_file(file.filename):
            flash('Қате! Рұқсат етілмеген файл форматы.', 'danger')
            return redirect(url_for('complaint'))

        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        conn = sqlite3.connect('samgau.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO complaints (description, file_path) VALUES (?, ?)', (description, file_path))
        conn.commit()
        conn.close()

        tg_text = (
            f"🛡️ <b>ЖАҢА АНОНИМДІ ШАҒЫМ!</b>\n\n"
            f"🔒 <i>Бұл шағым толықтай анонимді түрде келіп түсті.</i>\n\n"
            f"📝 <b>Шағым мәтіні:</b>\n{description}"
        )
        send_telegram_message(tg_text)

        if file_path and os.path.exists(file_path):
            send_telegram_document(file_path, caption="📎 Анонимді шағымның дәлелдеме файлы")

        flash('Шағымыңыз анонимді түрде сақталды және Комплаенс ботына жіберілді!', 'success')
        return redirect(url_for('index'))
    return render_template('complaint.html')


@app.route('/admin/report/<period>')
def admin_report(period):
    """Екі бөлімнен тұратын (Ұсыныстар және Шағымдар) аналитикалық есеп беті"""
    if period not in ['day', 'week', 'month', 'year', 'all']:
        period = 'all'

    start_date = get_date_filter(period)

    conn = sqlite3.connect('samgau.db')
    cursor = conn.cursor()

    cursor.execute(
        "SELECT title, description, full_name, faculty, specialty, phone, email, created_at FROM proposals WHERE created_at >= ? ORDER BY created_at DESC",
        (start_date,))
    proposals = cursor.fetchall()

    cursor.execute("SELECT description, created_at FROM complaints WHERE created_at >= ? ORDER BY created_at DESC",
                   (start_date,))
    complaints = cursor.fetchall()

    cursor.execute("SELECT faculty, COUNT(*) FROM proposals WHERE created_at >= ? GROUP BY faculty", (start_date,))
    faculty_stats = cursor.fetchall()

    conn.close()

    period_names = {'day': 'Күндік', 'week': 'Апталық', 'month': 'Айлық', 'year': 'Жылдық', 'all': 'Барлық уақыттағы'}

    html_template = """
    <!DOCTYPE html>
    <html lang="kk">
    <head>
        <meta charset="UTF-8">
        <title>Самғау - Аналитикалық есеп ({{ period_name }})</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 30px; color: #333; }
            h1 { color: #0a2540; border-bottom: 2px solid #0a2540; padding-bottom: 10px; }
            h2 { color: #104071; margin-top: 35px; border-bottom: 1px solid #ccc; padding-bottom: 8px; }
            table { width: 100%; border-collapse: collapse; margin-top: 15px; margin-bottom: 25px; }
            th, td { border: 1px solid #ddd; padding: 10px; text-align: left; font-size: 14px; }
            th { background-color: #0a2540; color: white; }
            tr:nth-child(even) { background-color: #f9f9f9; }
            .card { background: #f4f6f9; padding: 15px; border-radius: 8px; margin-bottom: 12px; border-left: 4px solid #0a2540; }
            .complaint-card { border-left-color: #d9381e; background: #fff5f5; }
            .print-btn { background: #0a2540; color: white; padding: 12px 20px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; margin-bottom: 20px; }
            .print-btn:hover { background: #153e66; }
            @media print { .print-btn { display: none; } }
        </style>
    </head>
    <body>
        <button class="print-btn" onclick="window.print()">🖨️ PDF түрінде сақтау / Басып шығару</button>

        <h1>«Самғау» порталының аналитикалық есебі</h1>
        <p><b>Кезең:</b> {{ period_name }} есеп</p>
        <p><b>Құрылған уақыты:</b> {{ now }}</p>

        <!-- 1-БӨЛІМ: ҰСЫНЫСТАР ЖӘНЕ СТАРТАПТАР -->
        <h2>📊 1-БӨЛІМ: Ұсыныстар мен стартаптар статистикасы</h2>

        <h3>Мектептер бойынша кесте</h3>
        <table>
            <tr>
                <th>Мектеп атауы</th>
                <th>Ұсыныстар саны</th>
            </tr>
            {% for stat in faculty_stats %}
            <tr>
                <td>{{ stat[0] }}</td>
                <td><b>{{ stat[1] }}</b></td>
            </tr>
            {% else %}
            <tr>
                <td colspan="2" style="text-align: center; color: #777;">Бұл кезеңде деректер жоқ</td>
            </tr>
            {% endfor %}
        </table>

        <h3>Түскен ұсыныстардың толық тізімі (Барлығы: {{ proposals|length }})</h3>
        {% for p in proposals %}
        <div class="card">
            <p><b>Тақырыбы:</b> {{ p[0] }}</p>
            <p><b>Автор:</b> {{ p[2] }} | <b>Мектеп:</b> {{ p[3] }} | <b>Курсы:</b> {{ p[4] }}</p>
            <p><b>Байланыс:</b> Тел: {{ p[5] }} | Email: {{ p[6] }}</p>
            <p><b>Сипаттамасы:</b> {{ p[1] }}</p>
            <p><small style="color: #666;">Жасалған күні: {{ p[7] }}</small></p>
        </div>
        {% else %}
        <p style="color: #777;">Ұсыныстар әлі түспеді.</p>
        {% endfor %}

        <!-- 2-БӨЛІМ: ШАҒЫМДАР ЖӘНЕ АНТИКОР -->
        <h2>🛡️ 2-БӨЛІМ: Анонимді шағымдар мен антикор файлдары (Барлығы: {{ complaints|length }})</h2>

        {% for c in complaints %}
        <div class="card complaint-card">
            <p><b>Шағым мәтіні:</b> {{ c[0] }}</p>
            <p><small style="color: #666;">Жасалған күні: {{ c[1] }}</small></p>
        </div>
        {% else %}
        <p style="color: #777;">Анонимді шағымдар түспеді.</p>
        {% endfor %}
    </body>
    </html>
    """

    return render_template_string(
        html_template,
        period_name=period_names.get(period, 'Барлық'),
        now=datetime.now().strftime('%Y-%m-%d %H:%M'),
        faculty_stats=faculty_stats,
        proposals=proposals,
        complaints=complaints
    )


# Telegram бот арқылы /start, /report немесе «📊 Анализ» командаларын өңдеу
@app.route('/telegram-webhook', methods=['POST'])
def telegram_webhook():
    data = request.get_json()
    if data and 'message' in data:
        message = data['message']
        chat_id = message['chat']['id']
        text = message.get('text', '')

        local_ip = get_local_ip()
        base_url = f"http://{local_ip}:5000/admin/report"

        if text in ['/start', '/report', '📊 Анализ']:
            keyboard = {
                "inline_keyboard": [
                    [{"text": "📅 Күндік анализ", "url": f"{base_url}/day"}],
                    [{"text": "📆 Апталық анализ", "url": f"{base_url}/week"}],
                    [{"text": "🗓️ Айлық анализ", "url": f"{base_url}/month"}],
                    [{"text": "📈 Жылдық анализ", "url": f"{base_url}/year"}],
                    [{"text": "📋 Барлық есеп мен статистика", "url": f"{base_url}/all"}]
                ]
            }
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": "📊 <b>«Самғау» порталының аналитикалық панеліне қош келдіңіз!</b>\n\nҚажетті кезеңді таңдаңыз (ашылған беттегі батырма арқылы ұсыныстар мен шағымдар кестесін PDF етіп сақтай аласыз):",
                "parse_mode": "HTML",
                "reply_markup": keyboard
            }
            requests.post(url, json=payload)

    return {"ok": True}


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)