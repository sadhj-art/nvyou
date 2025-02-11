from flask import Flask, render_template, request, redirect, url_for, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
import sqlite3
import requests

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # 设置一个复杂密钥

# 初始化登录管理
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# 数据库初始化
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  username TEXT UNIQUE, 
                  password TEXT)''')
    conn.commit()
    conn.close()

init_db()

# 用户类
class User(UserMixin):
    def __init__(self, user_id):
        self.id = user_id

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

# 百度API配置
BAIDU_API_KEY = "bce-v3/ALTAK-YYIcBRzWZlbvR9E2wmJfh/5a03ba85c9ef26b3317a74adc498d62654f16918"
BAIDU_SECRET_KEY = "469f9b318d04482aa8d3aaca211e11a3"
ACCESS_TOKEN_URL = f"https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={BAIDU_API_KEY}&client_secret={BAIDU_SECRET_KEY}"

def get_access_token():
    response = requests.get(ACCESS_TOKEN_URL)
    return response.json().get('access_token')

# 登录路由
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE username=? AND password=?", (username, password))
        user = c.fetchone()
        conn.close()
        if user:
            login_user(User(user[0]))
            return redirect(url_for('chat'))
        else:
            return "登录失败"
    return render_template('login.html')

# 聊天页面
@app.route('/chat')
@login_required
def chat():
    return render_template('chat.html', uid=session['_user_id'])

# 处理AI请求
@app.route('/ask', methods=['POST'])
@login_required
def ask():
    user_message = request.form['message']
    prompt = request.form.get('prompt', '')
    model = request.form.get('model', 'ERNIE-Bot')
    uid = session['_user_id']

    # 组合提示词
    full_message = f"{prompt}\n用户{uid}: {user_message}"

    # 调用百度API
    access_token = get_access_token()
    url = f"https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions?access_token={access_token}"
    headers = {'Content-Type': 'application/json'}
    data = {
        "messages": [{"role": "user", "content": full_message}],
        "user_id": str(uid)  # 使用UID保持会话独立
    }
    response = requests.post(url, headers=headers, json=data)
    return response.json().get('result', '请求失败')

if __name__ == '__main__':
    app.run(debug=True)