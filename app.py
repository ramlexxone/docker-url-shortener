from flask import Flask, request, redirect
import psycopg2
import string
import random
from urllib.parse import urlparse

app = Flask(__name__)

def get_db():
    return psycopg2.connect(
        host="db",
        database="shortener",
        user="user",
        password="password"
    )

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        long_url = request.form['url']
        
        # Проверка на корректный URL
        parsed_url = urlparse(long_url)
        if not parsed_url.scheme or not parsed_url.netloc:
            return "Ошибка: Вы ввели не похоже на ссылку. Не забудьте http:// или https://", 400

        short_code = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
        
        conn = get_db()
        cur = conn.cursor()
        cur.execute("INSERT INTO links (short, long) VALUES (%s, %s)", (short_code, long_url))
        conn.commit()
        cur.close()
        conn.close()
        
        return f"Короткая ссылка: http://localhost/{short_code}"
        
    return '''
        <h1>URL Shortener</h1>
        <form method="post">
            <input type="text" name="url" placeholder="Вставьте длинную ссылку" style="width: 300px;">
            <button type="submit">Сократить</button>
        </form>
    '''

@app.route('/<short_code>')
def redirect_to_long(short_code):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT long FROM links WHERE short = %s", (short_code,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    
    if result:
        return redirect(result[0])
    return "Ссылка не найдена", 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)