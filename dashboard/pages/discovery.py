import streamlit as st
from lib.docker_utils import exec_in_container

st.set_page_config(page_title="Discovery")
st.title("Discovery — Katana и Arjun")

st.markdown("""
**Katana** — краулер для обнаружения эндпоинтов.

**Arjun** — поиск скрытых HTTP-параметров.
""")

tab1, tab2 = st.tabs(["Katana", "Arjun"])

# ====== KATANA ======
with tab1:
    st.subheader("Katana — обнаружение эндпоинтов")

    target_url = st.text_input(
        "URL цели",
        value="http://juice-shop:3000",
        key="katana_url"
    )
    depth = st.slider("Глубина", 1, 5, 3, key="katana_depth")

    if st.button("Запустить Katana", key="katana_run"):
        with st.spinner("Сканирую..."):
            result = exec_in_container("katana", [
                "katana",
                "-u", target_url,
                "-jc",
                "-d", str(depth),
                "-silent",
                "-o", "/results/katana_endpoints.txt"   # ← в корень /results/
            ], timeout=300)

        if result.get("success"):
            st.success("Katana завершён!")
            st.code(result["stdout"][:2000] or "(нет вывода)")
        else:
            st.error(result.get("error") or result.get("stderr"))

    # Показ результатов
    st.divider()
    if st.button("Показать найденные эндпоинты", key="katana_show"):
        r = exec_in_container("katana", ["cat", "/results/katana_endpoints.txt"])
        if r.get("success") and r["stdout"]:
            endpoints = r["stdout"].strip().split("\n")
            st.metric("Найдено эндпоинтов", len(endpoints))
            st.code(r["stdout"])
        else:
            st.info("Файл пуст или не найден. Запустите Katana сначала.")

# ====== ARJUN ======
with tab2:
    st.subheader("Arjun — поиск скрытых параметров")

    target = st.text_input(
        "URL для анализа",
        value="http://juice-shop:3000/rest/products/search",
        key="arjun_url"
    )

    if st.button("Запустить Arjun", key="arjun_run"):
        with st.spinner("Ищу параметры..."):
            result = exec_in_container("arjun", [
                "arjun",
                "-u", target,
                "-oJ", "/results/arjun_params.json",   # ← в корень /results/
                "-t", "10"
            ], timeout=600)

        if result.get("success"):
            st.success("Arjun завершён!")
            st.code(result["stdout"][:2000] or "(нет вывода)")
        else:
            st.error(result.get("error") or result.get("stderr"))

    # Показ результатов
    st.divider()
    if st.button("Показать найденные параметры", key="arjun_show"):
        r = exec_in_container("arjun", ["cat", "/results/arjun_params.json"])
        if r.get("success") and r["stdout"]:
            st.code(r["stdout"], language="json")
        else:
            st.info("Файл пуст или не найден. Запустите Arjun сначала.")