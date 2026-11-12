from flask import Flask, request, redirect
import psycopg2
import redis
import string
import random
from urllib.parse import urlparse

app = Flask(__name__)

r = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)

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
    print(f"--- ПОИСК ССЫЛКИ: {short_code} ---")
    
    # 1. Проверяем Redis
    cached_url = r.get(short_code)
    if cached_url:
        print("!!! ВЗЯТО ИЗ КЭША !!!")
        return redirect(cached_url)

    print("В кэше нет. Идем в базу...")
    
    # 2. Идем в PostgreSQL
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT long FROM links WHERE short = %s", (short_code,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    
    if result:
        long_url = result[0]
        print(f"Найдено в базе: {long_url}")
        
        # 3. Сохраняем в Redis
        r.setex(short_code, 3600, long_url)
        print("Сохранено в Redis!")
        
        return redirect(long_url)
        
    print("Ссылка не найдена в базе")
    return "Ссылка не найдена", 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)