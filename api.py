from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware  # 新增导入
from pydantic import BaseModel
import requests
from dotenv import load_dotenv
import os

load_dotenv()

# 先创建app实例
app = FastAPI()

# 立即添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 百度API配置
BAIDU_API_KEY = os.getenv("bce-v3/ALTAK-YYIcBRzWZlbvR9E2wmJfh/5a03ba85c9ef26b3317a74adc498d62654f16918")
BAIDU_SECRET_KEY = os.getenv("469f9b318d04482aa8d3aaca211e11a3")

class ChatRequest(BaseModel):
    message: str
    prompt: str = "你是一个有帮助的AI助手"  # 默认提示词

def get_access_token():
    """获取百度API的access_token"""
    url = "https://aip.baidubce.com/oauth/2.0/token"
    params = {
        "grant_type": "client_credentials",
        "client_id": BAIDU_API_KEY,
        "client_secret": BAIDU_SECRET_KEY
    }
    response = requests.post(url, params=params)
    return response.json().get("access_token")

@app.post("/chat")
async def chat_with_baidu(request: ChatRequest):
    try:
        # 获取access_token
        access_token = get_access_token()
        if not access_token:
            raise HTTPException(status_code=500, detail="获取token失败")

        # 构造请求（以文心4.0为例）
        url = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions_pro"
        headers = {"Content-Type": "application/json"}
        payload = {
            "messages": [
                {"role": "system", "content": request.prompt},  # 自定义提示词
                {"role": "user", "content": request.message}
            ]
        }

        # 发送请求
        response = requests.post(
            f"{url}?access_token={access_token}",
            json=payload,
            headers=headers
        )

        if response.status_code == 200:
            result = response.json()
            return {"reply": result["result"]}
        else:
            raise HTTPException(status_code=500, detail=response.text)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8888)
