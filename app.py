import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime
import os

# -----------------------------------
# НАСТРОЙКА СТРАНИЦЫ
# -----------------------------------
st.set_page_config(page_title="Аналитика VK", layout="wide", page_icon="📊")

st.markdown("""
    <style>
        .metric-card {
            background: white;
            border-radius: 20px;
            padding: 1rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }
        .metric-value {
            font-size: 2rem;
            font-weight: 700;
            color: #0B1C3A;
        }
        .metric-label {
            font-size: 0.85rem;
            color: #5A6E8A;
        }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------
# ПОДКЛЮЧЕНИЕ К VK
# -----------------------------------
VK_ACCESS_TOKEN = os.getenv("VK_ACCESS_TOKEN")
VK_GROUP_ID = os.getenv("VK_GROUP_ID")

st.title("📊 Аналитика сообщества VK")

if not VK_ACCESS_TOKEN or not VK_GROUP_ID:
    st.error("❌ Переменные окружения не найдены")
    st.stop()

def load_posts():
    url = "https://api.vk.com/method/wall.get"
    params = {
        "access_token": VK_ACCESS_TOKEN,
        "v": "5.199",
        "owner_id": f"-{VK_GROUP_ID}",
        "count": 30
    }
    resp = requests.post(url, params=params).json()
    
    if "error" in resp:
        st.error(f"Ошибка: {resp['error']['error_msg']}")
        return None
    
    items = resp.get("response", {}).get("items", [])
    for p in items:
        views = p.get("views", {}).get("count", 1)
        likes = p.get("likes", {}).get("count", 0)
        reposts = p.get("reposts", {}).get("count", 0)
        comments = p.get("comments", {}).get("count", 0)
        p["er"] = round((likes + reposts + comments) / views * 100, 2)
        p["views_cnt"] = views
        p["likes_cnt"] = likes
    return items

if st.button("📥 Загрузить данные"):
    with st.spinner("Загрузка..."):
        posts = load_posts()
    if posts:
        st.session_state.posts = posts
        st.success(f"Загружено {len(posts)} постов")

if "posts" in st.session_state:
    posts = st.session_state.posts
    df = pd.DataFrame(posts)
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Всего постов", len(posts))
    c2.metric("Средний ER", f"{df['er'].mean():.2f}%")
    c3.metric("Всего просмотров", f"{df['views_cnt'].sum():,}")
    
    st.subheader("Топ-5 постов")
    for _, row in df.nlargest(5, "er").iterrows():
        date = datetime.fromtimestamp(row["date"]).strftime("%d.%m.%Y")
        text = row.get("text", "")[:80]
        st.markdown(f"**{date}** — ER {row['er']}% | ❤️ {row['likes_cnt']}")
        st.caption(text)
        st.markdown("---")
