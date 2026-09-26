import streamlit as st
from lib.docker_utils import get_containers

st.set_page_config(
    page_title="Web Fuzzing Lab",
    page_icon="🛡️",
    layout="wide"
)

st.title("🛡️ Web Fuzzing Lab")
st.markdown("### Лаборатория веб-фаззинга")

st.markdown("""
Добро пожаловать! Это дашборд для проведения экспериментов по веб-фаззингу
с использованием открытых инструментов.

**Разделы (слева в меню):**
- 📦 **Containers** — статус всех контейнеров стенда
- 🚀 **Fuzzing** — запуск фаззинга одним кликом
- 📊 **Results** — таблицы, графики и сравнение инструментов
- 🕷️ **Discovery** — запуск Katana и Arjun
- 📄 **Logs** — просмотр логов контейнеров
""")

# Краткая сводка
st.divider()
st.subheader("📊 Текущее состояние")

try:
    containers = get_containers()
    running = [c for c in containers if c.get("running")]
    stopped = [c for c in containers if not c.get("running") and "error" not in c]

    col1, col2, col3 = st.columns(3)
    col1.metric("Всего контейнеров", len(containers))
    col2.metric("Запущено", len(running))
    col3.metric("Остановлено", len(stopped))
except Exception as e:
    st.error(f"Не удалось получить статус: {e}")

pages = [
    st.Page("pages/containers.py", title="Containers"),
    st.Page("pages/discovery.py", title="Discovery"),
    st.Page("pages/fuzzing.py", title="Fuzzing"),
    st.Page("pages/logs.py", title="Logs"),
    st.Page("pages/results.py", title="Results"),
    st.Page("pages/reports.py", title="n8n Reports"),
    st.Page("pages/runs.py", title="Runs"), 
]

pg = st.navigation(pages)
pg.run()