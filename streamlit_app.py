import streamlit as st
from openai import OpenAI

st.title("OpenAI LLM 测试")

api_key = st.text_input("API Key", type="password")
base_url = st.text_input("Base URL", value="https://api.openai.com/v1")
text = st.text_area("输入要优化的文本")

if st.button("开始优化"):
    if not api_key or not text:
        st.warning("请填写API Key和文本")
    else:
        client = OpenAI(api_key=api_key, base_url=base_url)
        try:
            completion = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "你是一个有用的助手。"},
                    {"role": "user", "content": text}
                ]
            )
            st.success("优化结果：")
            st.write(completion.choices[0].message.content)
        except Exception as e:
            st.error(f"调用失败: {e}")
