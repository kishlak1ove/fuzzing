import streamlit as st
from lib.docker_utils import get_containers, get_container_logs

st.set_page_config(page_title="Containers", page_icon="📦")
st.title("📦 Статус контейнеров")

if st.button("🔄 Обновить"):
    st.rerun()

containers = get_containers()

if not containers:
    st.warning("Контейнеры не найдены")
else:
    for c in containers:
        if "error" in c:
            st.error(c["error"])
            continue

        status_icon = "🟢" if c["running"] else "🔴"
        with st.expander(f"{status_icon} {c['name']} — {c['status']}"):
            st.write(f"**Образ:** `{c['image']}`")
            st.write(f"**Статус:** {c['status']}")
            if st.checkbox("Показать логи", key=c["name"]):
                logs = get_container_logs(c["name"], lines=30)
                st.code(logs, language="text")