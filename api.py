from flask import Flask, request, render_template, session
from openai import OpenAI
import config
import uuid
from datetime import timedelta

app = Flask(__name__)
app.secret_key = str(uuid.uuid4())  # 生成随机密钥
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)  # 会话有效期1天

client = OpenAI(
    api_key=config.XAI_API_KEY,
    base_url="https://api.x.ai/v1",
)

def get_grok_response(messages):
    try:
        completion = client.chat.completions.create(
            model="grok-2-latest",
            messages=messages
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"API调用出错: {str(e)}"

@app.before_request
def make_session_permanent():
    session.permanent = True
    # 为每个新用户初始化设置
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
        session['history'] = []
        session['system_prompt'] = "你是一个乐于助人的AI助手"
        session['max_history'] = 5

@app.route('/', methods=['GET', 'POST'])
def chat():
    if request.method == 'POST':
        # 更新用户设置
        if 'set_prompt' in request.form:
            session['system_prompt'] = request.form['system_prompt']
            session['max_history'] = int(request.form['max_history'])

        # 处理聊天消息
        elif 'message' in request.form:
            user_message = request.form['message']

            # 构建消息历史
            messages = [{"role": "system", "content": session['system_prompt']}]
            messages += session['history'][-session['max_history']*2:]
            messages.append({"role": "user", "content": user_message})

            # 获取Grok回复
            ai_response = get_grok_response(messages)

            # 保存到历史记录（保留最近的max_history*2条）
            session['history'].extend([
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": ai_response}
            ])
            session['history'] = session['history'][-session['max_history']*2:]
            session.modified = True

    return render_template('index.html',
                           history=session['history'],
                           system_prompt=session['system_prompt'],
                           max_history=session['max_history'])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
