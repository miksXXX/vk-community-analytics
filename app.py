import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime
import os

# Конфигурация
VK_ACCESS_TOKEN = os.getenv("VK_ACCESS_TOKEN")
VK_GROUP_ID = os.getenv("VK_GROUP_ID")
VK_API_VERSION = "5.199"
VK_API_URL = "https://api.vk.com/method/"

def get_wall_posts(count=100):
    """Получить последние посты со стены"""
    params = {
        "access_token": VK_ACCESS_TOKEN,
        "v": VK_API_VERSION,
        "owner_id": f"-{VK_GROUP_ID}",
        "count": count
    }
    
    response = requests.post(f"{VK_API_URL}wall.get", params=params)
    data = response.json()
    
    if "error" in data:
        st.error(f"Ошибка API: {data['error']['error_msg']}")
        return None
    
    return data.get("response", {}).get("items", [])

def calculate_er(post):
    """Рассчитать ER для поста"""
    views = post.get("views", {}).get("count", 1)
    if views == 0:
        return 0
    
    likes = post.get("likes", {}).get("count", 0)
    reposts = post.get("reposts", {}).get("count", 0)
    comments = post.get("comments", {}).get("count", 0)
    
    total = likes + reposts + comments
    return round((total / views) * 100, 2)

# Интерфейс Streamlit
st.set_page_config(page_title="VK Analytics", layout="wide")
st.title("📊 Аналитика сообщества VK")

# Проверка наличия токена
if not VK_ACCESS_TOKEN or not VK_GROUP_ID:
    st.error("❌ Не настроены переменные окружения. Добавьте VK_ACCESS_TOKEN и VK_GROUP_ID в Secrets на Render.")
    st.stop()

# Кнопка загрузки
if st.button("🔄 Загрузить данные из VK"):
    with st.spinner("Загружаем посты..."):
        posts = get_wall_posts(100)
    
    if posts:
        # Добавляем ER к каждому посту
        for post in posts:
            post["er"] = calculate_er(post)
        
        # Сохраняем в сессию
        st.session_state.posts = posts
        st.success(f"✅ Загружено {len(posts)} постов")
    else:
        st.error("Не удалось загрузить посты")

# Показываем аналитику, если данные есть
if "posts" in st.session_state and st.session_state.posts:
    posts = st.session_state.posts
    
    # Основные метрики
    col1, col2, col3, col4 = st.columns(4)
    
    total_posts = len(posts)
    avg_er = sum(p["er"] for p in posts) / total_posts
    total_views = sum(p.get("views", {}).get("count", 0) for p in posts)
    total_likes = sum(p.get("likes", {}).get("count", 0) for p in posts)
    
    with col1:
        st.metric("📝 Постов", total_posts)
    with col2:
        st.metric("📈 Средний ER", f"{avg_er:.2f}%")
    with col3:
        st.metric("👁️ Просмотров", f"{total_views:,}")
    with col4:
        st.metric("❤️ Лайков", f"{total_likes:,}")
    
    # Топ-5 постов
    st.subheader("🏆 Топ-5 постов по вовлеченности")
    top_posts = sorted(posts, key=lambda x: x["er"], reverse=True)[:5]
    
    for i, post in enumerate(top_posts, 1):
        text = post.get("text", "(без текста)")[:100]
        date = datetime.fromtimestamp(post["date"]).strftime("%d.%m.%Y")
        st.markdown(f"**{i}. {date}** — ER: {post['er']}%")
        st.caption(text[:80] + "..." if len(text) > 80 else text)
        st.markdown("---")
    
    # График по дням
    st.subheader("📅 Динамика по дням")
    df = pd.DataFrame([{
        "date": datetime.fromtimestamp(p["date"]).date(),
        "er": p["er"]
    } for p in posts])
    
    daily_avg = df.groupby("date")["er"].mean().reset_index()
    fig = px.line(daily_avg, x="date", y="er", title="Средний ER по дням", markers=True)
    st.plotly_chart(fig, use_container_width=True)

else:
    st.info("👆 Нажми кнопку выше, чтобы загрузить данные из вашего сообщества")
