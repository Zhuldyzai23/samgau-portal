import os
import socket
import sqlite3
import requests
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'dulaty_samgau_super_secure_key_2026'

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'mp4', 'mp3', 'wav', 'doc', 'docx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Telegram Бот баптаулары (Сіз берген API мен Chat ID)
TELEGRAM_BOT_TOKEN = '9039294267:AAFKlaNgBvqDJbZjhFuJSsFAa90vtRL0o34'
TELEGRAM_CHAT_ID = '7722421089'


def send_telegram_message(text):
    """Telegram бот арқылы мәтіндік хабарлама жіберу"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text,
            "parse_mode": "HTML"
        }
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print("Telegram хабарламасын жіберу қатесі:", e)


def send_telegram_document(file_path, caption=""):
    """Telegram бот арқылы файлды (PDF, фото т.б.) жіберу"""
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
        print("Telegram файлы жіберу қатесі:", e)


# Телефоннан кіру үшін компьютердің IP-адресін анықтау
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
        specialty = request.form['specialty']
        phone = request.form['phone']
        email = request.form['email']

        file = request.files.get('file')
        file_path = None
        filename_str = "Жоқ"
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            filename_str = filename

        # Деректерді базаға сақтау
        conn = sqlite3.connect('samgau.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO proposals (title, description, full_name, faculty, specialty, phone, email, file_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (title, description, full_name, faculty, specialty, phone, email, file_path))
        conn.commit()
        conn.close()

        # Telegram ботқа толық ақпаратты жіберу
        tg_text = (
            f"🚀 <b>ЖАҢА ҰСЫНЫС / СТАРТАП!</b>\n\n"
            f"📌 <b>Тақырыбы:</b> {title}\n"
            f"📝 <b>Сипаттамасы:</b> {description}\n\n"
            f"👤 <b>Автор:</b> {full_name}\n"
            f"🏛 <b>Факультет:</b> {faculty}\n"
            f"🎓 <b>Мамандығы:</b> {specialty}\n"
            f"📞 <b>Телефон:</b> {phone}\n"
            f"📧 <b>Email:</b> {email}"
        )
        send_telegram_message(tg_text)

        # Егер файл (PDF т.б.) тіркелсе, оны да ботқа қосып жіберу
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
        file_path = None
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

        # Базаға сақтау
        conn = sqlite3.connect('samgau.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO complaints (description, file_path) VALUES (?, ?)', (description, file_path))
        conn.commit()
        conn.close()

        # Telegram ботқа анонимді түрде жіберу
        tg_text = (
            f"🛡️ <b>ЖАҢА АНОНИМДІ ШАҒЫМ!</b>\n\n"
            f"🔒 <i>Бұл шағым толықтай анонимді түрде келіп түсті.</i>\n\n"
            f"📝 <b>Шағым мәтіні:</b>\n{description}"
        )
        send_telegram_message(tg_text)

        # Дәлелдеме файл болса жіберу
        if file_path and os.path.exists(file_path):
            send_telegram_document(file_path, caption="📎 Анонимді шағымның дәлелдеме файлы")

        flash('Шағымыңыз анонимді түрде сақталды және Комплаенс ботына жіберілді!', 'success')
        return redirect(url_for('index'))
    return render_template('complaint.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)