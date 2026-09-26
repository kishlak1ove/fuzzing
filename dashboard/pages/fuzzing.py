import streamlit as st
from lib.fuzz_runner import run_fuzz, TARGETS

st.set_page_config(page_title="Fuzzing")
st.title("Запуск фаззинга")

WORDLISTS = {
    "small (15 payloads)": "/seeds/payloads.txt",
    "SecLists: special-chars": "/seeds/SecLists/Fuzzing/special-chars.txt",
    "SecLists: SQLi": "/seeds/SecLists/Fuzzing/Databases/SQLi/Generic-SQLi.txt",
    "SecLists: XSS": "/seeds/SecLists/Fuzzing/XSS/XSS-Jhaddix.txt",
}

col1, col2 = st.columns(2)
with col1:
    target = st.selectbox("Цель", list(TARGETS.keys()))
    st.caption(f"URL: `{TARGETS[target]['url']}{TARGETS[target]['endpoint']}`")
with col2:
    selected = st.selectbox("Словарь", list(WORDLISTS.keys()))

experiment = st.text_input("Название эксперимента", value="test")

if st.button("Запустить фаззинг", type="primary"):
    with st.spinner(f"Эксперимент '{experiment}' против {target}..."):
        result = run_fuzz(WORDLISTS[selected], experiment, target)

    if result.get("success"):
        st.success(f"Эксперимент '{experiment}' завершён!")
        col1, col2 = st.columns(2)
        col1.metric("ffuf", f"{result['ffuf_time']}s")
        col2.metric("wfuzz", f"{result['wfuzz_time']}s")

        with st.expander("Лог ffuf"):
            st.code(result["ffuf_output"])
        with st.expander("Лог wfuzz"):
            st.code(result["wfuzz_output"])
    else:
        st.error(f"Ошибка: {result.get('error')}")