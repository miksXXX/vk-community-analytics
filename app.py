import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime
import os
import sys
import subprocess

# -----------------------------------
# ПРОВЕРКА: ЗАПУЩЕН ЛИ STREAMLIT
# -----------------------------------
if not sys.argv[0].endswith('streamlit'):
    # Если запустили как python app.py, то перезапускаем через streamlit
    subprocess.Popen(["streamlit", "run", __file__, "--server.port", os.getenv("PORT", "8501"), "--server.address", "0.0.0.0"])
    print("🔄 Перезапускаем через streamlit...")
    sys.exit(0)

# -----------------------------------
# ОСНОВНОЙ КОД (тот же, что был)
# -----------------------------------
st.set_page_config(page_title="Аналитика VK Сообщества", layout="wide", page_icon="📊")

# Бизнес-стиль + русский шрифт
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }
        .stApp {
            background-color: #F7F9FC;
        }
        .metric-card {
            background: white;
            border-radius: 24px;
            padding: 1.5rem;
            box-shadow: 0 4px 12px rgba(0,0,0,0.03);
            border: 1px solid #E9EDF2;
        }
        .metric-value {
            font-size: 2.2rem;
            font-weight: 700;
            color: #0B1C3A;
        }
        .metric-label {
            font-size: 0.9rem;
            color: #5A6E8A;
            font-weight: 500;
        }
        .post-card {
            background: white;
            border-radius: 18px;
            padding: 1.2rem;
            margin-bottom: 0.85rem;
            border-left: 4px solid #2C6BFF;
            box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        }
        .post-metrics {
            font-size: 0.85rem;
            color: #2C6BFF;
            font-weight: 500;
        }
        .stButton > button {
            background: #0B1C3A;
            color: white;
            border-radius: 40px;
            padding: 0.5rem 1.8rem;
            font-weight: 500;
            border: none;
        }
        .stButton > button:hover {
            background: #1E3A6F;
        }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------
# ПОДКЛЮЧЕНИЕ К VK API
# -----------------------------------
VK_ACCESS_TOKEN = os.getenv("VK_ACCESS_TOKEN")
VK_GROUP_ID = os.getenv("VK_GROUP_ID")
VK_API_VERSION = "5.199"
VK_API_URL = "https://api.vk.com/method/"

def get_wall_posts(count=50):
    params = {
        "access_token": VK_ACCESS_TOKEN,
        "v": VK_API_VERSION,
        "owner_id": f"-{VK_GROUP_ID}",
        "count": count,
    }
    response = requests.post(f"{VK_API_URL}wall.get", params=params)
    data = response.json()

    if "error" in data:
        st.error(f"⚠️ Ошибка VK API: {data['error']['error_msg']}")
        return None

    items = data.get("response", {}).get("items", [])
    for post in items:
        views = post.get("views", {}).get("count", 1)
        likes = post.get("likes", {}).get("count", 0)
        reposts = post.get("reposts", {}).get("count", 0)
        comments = post.get("comments", {}).get("count", 0)

        post["er"] = round(((likes + reposts + comments) / max(views, 1)) * 100, 2)
        post["views_count"] = views
        post["likes_count"] = likes
        post["reposts_count"] = reposts
        post["comments_count"] = comments

    return items

# -----------------------------------
# ИНТЕРФЕЙС
# -----------------------------------
st.title("📊 Аналитика сообщества VK")

# Боковая панель с подсказками
with st.sidebar:
    st.markdown("## 🧭 О панели")
    st.markdown("""
    Здесь собраны ключевые показатели вашего сообщества.

    ✅ **ER** — вовлечённость (лайки + репосты + комментарии) / просмотры.
    ✅ **Топ постов** — лучшие публикации по ER.
    ✅ **График** — динамика вовлечённости.
    """)
    st.caption("Данные обновляются при каждом нажатии кнопки загрузки.")

if not VK_ACCESS_TOKEN or not VK_GROUP_ID:
    st.error("🔐 Не настроены переменные окружения. Добавьте VK_ACCESS_TOKEN и VK_GROUP_ID в настройках хостинга.")
    st.stop()

if st.button("🔄 Загрузить данные", use_container_width=True):
    with st.spinner("Загружаем данные из VK..."):
        posts = get_wall_posts(50)
    if posts:
        st.session_state.posts = posts
        st.success(f"✅ Загружено {len(posts)} постов")
    else:
        st.error("Не удалось загрузить посты. Проверьте токен и ID сообщества.")

if "posts" in st.session_state and st.session_state.posts:
    posts = st.session_state.posts
    df = pd.DataFrame(posts)

    total_posts = len(posts)
    avg_er = round(df["er"].mean(), 2)
    total_views = df["views_count"].sum()
    total_interactions = (df["likes_count"] + df["reposts_count"] + df["comments_count"]).sum()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📄 Всего постов", total_posts)
    with col2:
        st.metric("📈 Средний ER", f"{avg_er}%")
    with col3:
        st.metric("👁️ Просмотров", f"{total_views:,}")
    with col4:
        st.metric("💬 Взаимодействий", f"{total_interactions:,}")

    st.markdown("---")
    st.subheader("📅 Динамика вовлечённости (ER) по дням")
    
    df["date"] = pd.to_datetime(df["date"], unit="s").dt.date
    daily_er = df.groupby("date")["er"].mean().reset_index()

    fig = px.line(
        daily_er,
        x="date",
        y="er",
        labels={"date": "Дата", "er": "Средний ER (%)"},
        markers=True,
        color_discrete_sequence=["#2C6BFF"]
    )
    fig.update_layout(
        plot_bgcolor="white",
        title_font=dict(size=14),
        font=dict(family="Inter", size=12),
        margin=dict(l=20, r=20, t=40, b=20)
    )
    fig.update_xaxes(showgrid=False, linecolor="#E9EDF2")
    fig.update_yaxes(showgrid=True, gridcolor="#E9EDF2", zeroline=False)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("🏆 Лучшие посты по вовлечённости")
    top_posts = df.sort_values("er", ascending=False).head(5)

    for i, row in top_posts.iterrows():
        post_date = datetime.fromtimestamp(row["date"].timestamp()).strftime("%d.%m.%Y")
        post_text = (row.get("text", "") or "(без текста)")[:120]
        if len(row.get("text", "")) > 120:
            post_text += "…"

        st.markdown(f"""
        <div class="post-card">
            <div style="font-weight: 600; margin-bottom: 6px;">📌 {post_date}</div>
            <div style="margin-bottom: 10px; color: #1E2F45;">{post_text}</div>
            <div class="post-metrics">
                ER {row['er']}% &nbsp;|&nbsp; 
                👁️ {row['views_count']} &nbsp;|&nbsp; 
                ❤️ {row['likes_count']} &nbsp;|&nbsp; 
                🔁 {row['reposts_count']} &nbsp;|&nbsp; 
                💬 {row['comments_count']}
            </div>
        </div>
        """, unsafe_allow_html=True)

else:
    st.info("👈 Нажмите «Загрузить данные», чтобы увидеть аналитику вашего сообщества.")
