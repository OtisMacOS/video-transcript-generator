from openai import OpenAI

# ====== 在这里填写你的API Key和Base URL ======
API_KEY = "sk-xxxxxxx"         # 例如 
BASE_URL =  "http:!@@#S"   

client = OpenAI(
    api_key=API_KEY,
    base_url=BASE_URL if BASE_URL else None
)

try:
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",  # 你也可以用 "gpt-4o"、"gpt-4" 等
        messages=[
            {"role": "system", "content": "你是一个有用的助手。"},
            {"role": "user", "content": "你好！"}
        ]
    )
    print("✅ 测试成功，返回内容：")
    print(completion.choices[0].message.content)
except Exception as e:
    print("❌ 测试失败，错误信息：")
    print(e)
