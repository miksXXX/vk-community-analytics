import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime
import os

# -----------------------------------
# НАСТРОЙКА СТРАНИЦЫ И СТИЛЕЙ
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
            transition: all 0.2s;
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
            letter-spacing: 0.02em;
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
            transition: 0.2s;
        }
        .stButton > button:hover {
            background: #1E3A6F;
        }
        hr {
            margin: 1rem 0;
            border-color: #E9EDF2;
        }
        .sidebar-info {
            background: #EFF3F8;
            padding: 1rem;
            border-radius: 16px;
            font-size: 0.85rem;
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
    """Получает последние посты из сообщества"""
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
    <div class="sidebar-info">
    Здесь собраны ключевые показатели вашего сообщества.<br><br>
    ✅ <strong>ER</strong> — вовлечённость (лайки + репосты + комментарии) / просмотры.<br>
    ✅ <strong>Топ постов</strong> — лучшие публикации по ER.<br>
    ✅ <strong>График</strong> — динамика вовлечённости.
    </div>
    """, unsafe_allow_html=True)
    st.caption("Данные обновляются при каждом нажатии кнопки загрузки.")

# Проверка переменных окружения
if not VK_ACCESS_TOKEN or not VK_GROUP_ID:
    st.error("🔐 Не настроены переменные окружения. Добавьте VK_ACCESS_TOKEN и VK_GROUP_ID в настройках хостинга.")
    st.stop()

# Кнопка загрузки данных
col_btn, _ = st.columns([1, 5])
with col_btn:
    if st.button("🔄 Загрузить данные", use_container_width=True):
        with st.spinner("Загружаем данные из VK..."):
            posts = get_wall_posts(50)
        if posts:
            st.session_state.posts = posts
            st.success(f"✅ Загружено {len(posts)} постов")
        else:
            st.error("Не удалось загрузить посты. Проверьте токен и ID сообщества.")

# Основной блок аналитики
if "posts" in st.session_state and st.session_state.posts:
    posts = st.session_state.posts
    df = pd.DataFrame(posts)

    # --- Метрики (KPI) ---
    total_posts = len(posts)
    avg_er = round(df["er"].mean(), 2)
    total_views = df["views_count"].sum()
    total_interactions = (df["likes_count"] + df["reposts_count"] + df["comments_count"]).sum()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">📄 Всего постов</div>
            <div class="metric-value">{total_posts}</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">📈 Средний ER</div>
            <div class="metric-value">{avg_er}%</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">👁️ Просмотров</div>
            <div class="metric-value">{total_views:,}</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">💬 Взаимодействий</div>
            <div class="metric-value">{total_interactions:,}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # --- График вовлечённости по дням ---
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
        margin=dict(l=20, r=20, t=40, b=20),
        hoverlabel=dict(bgcolor="white", font_size=12)
    )
    fig.update_xaxes(showgrid=False, linecolor="#E9EDF2")
    fig.update_yaxes(showgrid=True, gridcolor="#E9EDF2", zeroline=False)
    st.plotly_chart(fig, use_container_width=True)

    # --- Топ-5 постов по ER ---
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
    st.info("👈 Нажмите «Загрузить данные», чтобы увидеть аналитику вашего сообщества в деловом стиле.")
