import streamlit as st
from lib.docker_utils import get_containers, get_container_logs

st.set_page_config(page_title="Logs", page_icon="📄")
st.title("📄 Логи контейнеров")

containers = get_containers()
names = [c["name"] for c in containers if "name" in c]

if not names:
    st.warning("Контейнеры не найдены")
    st.stop()

col1, col2 = st.columns([2, 1])
with col1:
    selected = st.selectbox("Контейнер", names)
with col2:
    lines = st.number_input("Строк", 10, 500, 50)

if st.button("🔄 Обновить логи"):
    st.rerun()

logs = get_container_logs(selected, lines)
st.code(logs, language="text")