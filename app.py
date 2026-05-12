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

# -----------------------------------
# ПОДКЛЮЧЕНИЕ К VK
# -----------------------------------
VK_ACCESS_TOKEN = os.getenv("VK_ACCESS_TOKEN")
VK_GROUP_ID = os.getenv("VK_GROUP_ID")

st.title("📊 Аналитика сообщества VK")

# Проверка переменных
if not VK_ACCESS_TOKEN or not VK_GROUP_ID:
    st.error("❌ Переменные окружения VK_ACCESS_TOKEN и VK_GROUP_ID не найдены")
    st.stop()

# Функция загрузки постов
def load_posts():
    url = "https://api.vk.com/method/wall.get"
    params = {
        "access_token": VK_ACCESS_TOKEN,
        "v": "5.199",
        "owner_id": f"-{VK_GROUP_ID}",
        "count": 30
    }
    
    try:
        response = requests.post(url, params=params)
        data = response.json()
        
        if "error" in data:
            st.error(f"Ошибка VK API: {data['error']['error_msg']}")
            return None
        
        items = data.get("response", {}).get("items", [])
        
        for post in items:
            views = post.get("views", {}).get("count", 1)
            likes = post.get("likes", {}).get("count", 0)
            reposts = post.get("reposts", {}).get("count", 0)
            comments = post.get("comments", {}).get("count", 0)
            
            post["er"] = round(((likes + reposts + comments) / views) * 100, 2)
            post["views_cnt"] = views
            post["likes_cnt"] = likes
            post["reposts_cnt"] = reposts
            post["comments_cnt"] = comments
        
        return items
    except Exception as e:
        st.error(f"Ошибка подключения: {e}")
        return None

# Кнопка загрузки
if st.button("📥 Загрузить данные", use_container_width=True):
    with st.spinner("Загружаем данные из VK..."):
        posts = load_posts()
    if posts:
        st.session_state.posts = posts
        st.success(f"✅ Загружено {len(posts)} постов")
    else:
        st.error("Не удалось загрузить посты")

# Отображение данных
if "posts" in st.session_state and st.session_state.posts:
    posts = st.session_state.posts
    df = pd.DataFrame(posts)
    
    # Метрики
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📄 Всего постов", len(posts))
    col2.metric("📈 Средний ER", f"{df['er'].mean():.2f}%")
    col3.metric("👁️ Всего просмотров", f"{df['views_cnt'].sum():,}")
    col4.metric("❤️ Всего лайков", f"{df['likes_cnt'].sum():,}")
    
    # График по дням
    st.subheader("📅 Динамика ER по дням")
    df["date"] = pd.to_datetime(df["date"], unit="s").dt.date
    daily = df.groupby("date")["er"].mean().reset_index()
    
    fig = px.line(daily, x="date", y="er", markers=True, 
                  labels={"date": "Дата", "er": "ER (%)"},
                  title="Средний ER по дням")
    fig.update_layout(plot_bgcolor="white", height=400)
    st.plotly_chart(fig, use_container_width=True)
    
    # Топ постов
    st.subheader("🏆 Топ-5 постов по вовлечённости")
    for i, (_, row) in enumerate(df.nlargest(5, "er").iterrows(), 1):
        date = datetime.fromtimestamp(row["date"].timestamp()).strftime("%d.%m.%Y")
        text = (row.get("text", "") or "(без текста)")[:100]
        
        with st.container():
            st.markdown(f"""
            **{i}. {date}** — ER: `{row['er']}%`  
            *{text}*  
            👁️ {row['views_cnt']} | ❤️ {row['likes_cnt']} | 🔁 {row['reposts_cnt']} | 💬 {row['comments_cnt']}
            """)
            st.divider()
else:
    st.info("👆 Нажмите кнопку «Загрузить данные», чтобы начать")
