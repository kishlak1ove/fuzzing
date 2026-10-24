import streamlit as st
from lib.docker_utils import exec_in_container

st.set_page_config(page_title="Discovery", page_icon="🔎")
st.title("🔎 Discovery — Katana и Arjun")

# === СПИСОК ЦЕЛЕЙ ===
TARGETS = {
    "VulnAPI — главная": "http://vulnapi:5035",
    "VulnAPI — SQLi Search": "http://vulnapi:5035/sqli/search",
    "VulnAPI — XSS Reflected": "http://vulnapi:5035/xss/reflected",
    "VulnAPI — SSTI": "http://vulnapi:5035/ssti",
    "VulnAPI — Path Traversal": "http://vulnapi:5035/ptrav/read",
    "VulnAPI — RCE Ping": "http://vulnapi:5035/rce/ping",
    "Juice Shop": "http://juice-shop:3000",
    "Juice Shop — Products": "http://juice-shop:3000/rest/products/search",
    "PyGoat": "http://pygoat:8000",
    "Spring Vulny": "https://javaspringvulny:9000",
}

st.markdown("""
**Katana** — краулер для обнаружения эндпоинтов.

**Arjun** — поиск скрытых HTTP-параметров.
""")

tab1, tab2 = st.tabs(["🕷 Katana", "🏹 Arjun"])

# ====== KATANA ======
with tab1:
    st.subheader("Katana — обнаружение эндпоинтов")

    col1, col2 = st.columns([2, 1])
    with col1:
        katana_target_name = st.selectbox(
            "Цель",
            list(TARGETS.keys()),
            key="katana_target_select"
        )
        katana_url = TARGETS[katana_target_name]

        custom = st.text_input(
            "Или свой URL (пусто = из списка)",
            value="",
            key="katana_custom"
        )
        if custom.strip():
            katana_url = custom.strip()

        st.caption(f"URL: `{katana_url}`")
    with col2:
        depth = st.slider("Глубина", 1, 5, 3, key="katana_depth")

    if st.button("🚀 Запустить Katana", key="katana_run"):
        with st.spinner("Сканирую..."):
            result = exec_in_container("katana", [
                "katana",
                "-u", katana_url,
                "-jc",
                "-d", str(depth),
                "-silent",
                "-o", "/results/katana_endpoints.txt"
            ], timeout=300)

        if result.get("success"):
            st.success("✅ Katana завершён!")
            st.code(result["stdout"][:2000] or "(нет вывода)")
        else:
            st.error(result.get("error") or result.get("stderr"))

    st.divider()
    if st.button("📄 Показать эндпоинты", key="katana_show"):
        r = exec_in_container("katana", ["cat", "/results/katana_endpoints.txt"])
        if r.get("success") and r["stdout"]:
            endpoints = r["stdout"].strip().split("\n")
            st.metric("Найдено эндпоинтов", len(endpoints))
            st.code(r["stdout"])
        else:
            st.info("Файл пуст. Запусти Katana сначала.")

# ====== ARJUN ======
with tab2:
    st.subheader("Arjun — поиск скрытых параметров")

    col1, col2 = st.columns([2, 1])
    with col1:
        arjun_target_name = st.selectbox(
            "Цель",
            list(TARGETS.keys()),
            key="arjun_target_select"
        )
        arjun_url = TARGETS[arjun_target_name]

        custom = st.text_input(
            "Или свой URL (пусто = из списка)",
            value="",
            key="arjun_custom"
        )
        if custom.strip():
            arjun_url = custom.strip()

        st.caption(f"URL: `{arjun_url}`")
    with col2:
        method = st.selectbox("Метод", ["GET", "POST", "JSON"], key="arjun_method")

    if st.button("🏹 Запустить Arjun", key="arjun_run"):
        out_file = "/results/arjun_params.json"
        with st.spinner(f"Arjun сканирует {arjun_url}..."):
            args = [
                "arjun",
                "-u", arjun_url,
                "-oJ", out_file,
                "-t", "10",
                "-m", method,
            ]
            result = exec_in_container("arjun", args, timeout=600)

        if result.get("success"):
            st.success(f"✅ Arjun завершён! Файл: `{out_file}`")
            st.code(result["stdout"][:3000] or "(нет вывода — параметры не найдены)")
        else:
            st.error(result.get("error") or result.get("stderr"))

    st.divider()
    if st.button("📄 Показать параметры", key="arjun_show"):
        r = exec_in_container("arjun", ["cat", "/results/arjun_params.json"])
        if r.get("success") and r["stdout"]:
            st.code(r["stdout"], language="json")
        else:
            st.info("Файл пуст или не найден.")

    st.caption("💡 Arjun может не находить параметры — это нормальный результат. Он ищет **скрытые** параметры, которых может не быть.")