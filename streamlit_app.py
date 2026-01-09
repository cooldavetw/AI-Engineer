import streamlit as st
import requests
import base64
import json
import re
import uuid

# API
FLOWISE_API_URL = "https://192.168.11.20:443/aibuilder/api/v1/prediction/0ca3fcee-b687-49a9-bc32-6701dcb26d63"


# 在啟動時初始化 sessionId
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# 初始化 session_state 中的查詢歷史紀錄
if "user_id" not in st.session_state:
    token = st.query_params['token']
    payload_b64 = token.split('.')[1]
    # Add padding if needed
    padding = '=' * (-len(payload_b64) % 4)
    decoded_bytes = base64.urlsafe_b64decode(payload_b64 + padding)
    payload = json.loads(decoded_bytes)

    st.session_state.user_id = payload['username']

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "clear_chat" not in st.session_state:
    st.session_state.clear_chat = False

if "chat_input" not in st.session_state:
    st.session_state.chat_input = ""

if "default_question_triggered" not in st.session_state:
    st.session_state.default_question_triggered = False

if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None

# 歡迎訊息
WELCOME_MESSAGE = """
歡迎使用伺服器維修手冊查詢助手！👋

我可以幫你快速查詢伺服器手冊中的重點資訊，像是處理器相容性、記憶體上限、電源供應等問題 💡  
只要輸入你的問題，我會為你找出最相關的內容 🙂🔍
"""

# 預設問題清單
default_questions = [
    "支援哪些處理器類型？",
    "記憶體容量上限為何？",
    "支援幾個硬碟？",
    "電源供應選項有哪些?",
    "擴充插槽支援哪些類型？",
    "支援散熱風扇規格?",
    "處理器安裝升級程序",
    "記憶體模組",
    "電源供應單元的更換",
    "硬碟托架與 RAID 配置",
    "BIOS 配置後的啟動"
]


def query_flowise(payload):
    try:
        response = requests.post(FLOWISE_API_URL, json=payload, timeout=(5, 120), verify=False)
        response.raise_for_status()
        # st.write("✅ Flowise 回應:", response.json())
        return response.json()
    except Exception as e:
        # st.error(f"⚠️ Flowise 錯誤：{e}")
        return {"text": f"⚠️ Flowise 錯誤：{e}"}


def get_flowise_answer(question: str) -> str:
    user_prompt = question
    result = query_flowise({"question": user_prompt,
    "overrideConfig": {
        "sessionId": st.session_state.session_id
    }})
    raw_text = result.get("text", "⚠️ 無法取得 Flowise 回應內容。")
    final_answer = remove_think_tags(raw_text)

    return final_answer


def remove_think_tags(text: str) -> str:
    # 移除 <think> 內部的內容以及標籤本身
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)


# ---------- 畫面 ----------
st.title("🛠️ 伺服器維修手冊查詢助手 📘")


# ---------- 清除對話 ----------
if st.button("🧹 清除對話紀錄"):
    st.session_state.chat_history.clear()
    st.session_state.clear_chat = True
else:
    st.session_state.clear_chat = False  # 沒按就還原

# ---------- 初始訊息 ----------
if not st.session_state.chat_history:
    st.session_state.chat_history.append({"role": "assistant", "content": WELCOME_MESSAGE})

# ---------- 顯示聊天紀錄 ----------
for chat in st.session_state.chat_history:
    with st.chat_message(chat["role"]):
        st.markdown(chat["content"])


# ---------- 處理預設問題按鈕觸發 ----------
if "default_question_triggered" not in st.session_state:
    st.session_state.default_question_triggered = False
if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None

# 顯示預設問題按鈕
st.markdown("### 🔍 常見問題快速提問")
cols = st.columns(3)
for i, question in enumerate(default_questions):
    if cols[i % 3].button(question, key=f"default_q_{i}"):
        st.session_state.pending_prompt = question
        st.session_state.default_question_triggered = True

# 顯示輸入框（永遠顯示）
user_input = st.chat_input("🤖 你可以問我任何伺服器相關的問題喔！")

# 優先處理手動輸入
if user_input:
    st.session_state.pending_prompt = user_input
    st.session_state.default_question_triggered = False

# ---------- AI 回答 ----------
if st.session_state.pending_prompt:
    prompt = st.session_state.pending_prompt
    st.session_state.pending_prompt = None  # 重設 pending

    st.session_state.chat_history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("💬 等待 AI 回覆中..."):
            answer = get_flowise_answer(prompt)
            st.session_state.chat_history.append({"role": "assistant", "content": answer})
            st.markdown(answer)
