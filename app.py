from flask import Flask, render_template, request, redirect, session
import sqlite3
import pickle
import feedparser

app = Flask(__name__)

app.secret_key = "secret123"

# Load ML model
model = pickle.load(open("model.pkl", "rb"))
vectorizer = pickle.load(open("vectorizer.pkl", "rb")) 

# Database
conn = sqlite3.connect("news.db", check_same_thread=False)
cur = conn.cursor()

# Create tables
cur.execute("""
CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    password TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS history(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    news TEXT,
    result TEXT
)
""")

conn.commit()

# API KEY
API_KEY = "YOUR_API_KEY"

# HOME
@app.route('/')
def home():

    if 'user' not in session:
        return redirect('/login')

    return render_template('index.html')

# REGISTER
@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        cur.execute(
            "INSERT INTO users(username,password) VALUES(?,?)",
            (username, password)
        )

        conn.commit()

        return redirect('/login')

    return render_template('register.html')

# LOGIN
@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        cur.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        )

        user = cur.fetchone()

        if user:

            session['user'] = username

            return redirect('/')

        else:

            return "Invalid Login"

    return render_template('login.html')

# LOGOUT
@app.route('/logout')
def logout():

    session.pop('user', None)

    return redirect('/login')

# PREDICTION
@app.route('/predict', methods=['POST'])
def predict():

    news = request.form['news']

    vector = vectorizer.transform([news])

    prediction = model.predict(vector)

    if prediction[0] == 1:
        result = "REAL NEWS ✅"
    else:
        result = "FAKE NEWS ❌"

    cur.execute(
        "INSERT INTO history(news,result) VALUES(?,?)",
        (news, result)
    )

    conn.commit()

    return render_template(
        'index.html',
        prediction=result,
        news_text=news
    )
    
# DETECT LIVE NEWS
@app.route('/detect-live-news', methods=['POST'])
def detect_live_news():

    news = request.form['news']

    # Convert into vector
    vector = vectorizer.transform([news])

    # Predict
    prediction = model.predict(vector)

    # Result
    if prediction[0] == 1:

        result = "REAL NEWS ✅"

    else:

        result = "FAKE NEWS ❌"

    # Save history
    cur.execute(
        "INSERT INTO history(news,result) VALUES(?,?)",
        (news, result)
    )

    conn.commit()

    return render_template(
        'index.html',
        prediction=result,
        news_text=news
    )

#----------------latest news-----------------
@app.route('/live-news')
def live_news():

    news_url = "http://feeds.bbci.co.uk/news/rss.xml"

    feed = feedparser.parse(news_url)

    articles = feed.entries

    return render_template(
        'live_news.html',
        articles=articles
    )

# DASHBOARD
@app.route('/dashboard')
def dashboard():

    cur.execute("SELECT COUNT(*) FROM history")
    total = cur.fetchone()[0]

    cur.execute(
        "SELECT COUNT(*) FROM history WHERE result='FAKE NEWS ❌'"
    )
    fake = cur.fetchone()[0]

    cur.execute(
        "SELECT COUNT(*) FROM history WHERE result='REAL NEWS ✅'"
    )
    real = cur.fetchone()[0]

    return render_template(
        'dashboard.html',
        total=total,
        fake=fake,
        real=real
    )

# HISTORY
@app.route('/history')
def history():

    cur.execute("SELECT * FROM history")

    data = cur.fetchall()

    return render_template(
        'history.html',
        data=data
    )

# ADMIN
@app.route('/admin')
def admin():

    cur.execute("SELECT * FROM users")

    users = cur.fetchall()

    return render_template(
        'admin.html',
        users=users
    )

if __name__ == "__main__":

    app.run(debug=True)