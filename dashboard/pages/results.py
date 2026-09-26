import streamlit as st
import plotly.express as px
from lib.results_parser import (
    list_experiments, parse_ffuf_to_df, load_timings,
    load_wfuzz_results, parse_wfuzz_to_df,
    delete_experiment, delete_all_experiments
)

st.set_page_config(page_title="Results")
st.title("Результаты экспериментов")

# ====== Управление экспериментами ======
with st.expander("Управление экспериментами"):
    col1, col2 = st.columns(2)

    experiments_list = list_experiments()

    with col1:
        st.markdown("**Удалить один эксперимент**")
        if experiments_list:
            to_delete = st.selectbox(
                "Выберите эксперимент",
                experiments_list,
                key="del_one"
            )
            if st.button("Удалить выбранный"):
                result = delete_experiment(to_delete)
                st.success(f"Удалено: {', '.join(result['deleted'])}")
                if result["errors"]:
                    st.warning(f"Ошибки: {result['errors']}")
                st.rerun()
        else:
            st.info("Нет экспериментов")

    with col2:
        st.markdown("**Удалить всё**")
        st.caption("Все эксперименты и timings.csv будут очищены")
        if st.button("Очистить всё", type="secondary"):
            if st.session_state.get("confirm_delete_all"):
                result = delete_all_experiments()
                st.success(f"Удалено: {len(result['deleted'])} файлов")
                st.session_state["confirm_delete_all"] = False
                st.rerun()
            else:
                st.session_state["confirm_delete_all"] = True
                st.warning("Нажмите ещё раз для подтверждения")

# ====== Просмотр результатов ======
timings = load_timings()

if timings.empty:
    st.info("Пока нет данных. Запустите первый эксперимент.")
    st.stop()

# Фильтр по цели
targets = ["Все"] + sorted(timings["Target"].unique().tolist())
selected_target = st.selectbox("Фильтр по цели", targets)

if selected_target != "Все":
    timings = timings[timings["Target"] == selected_target]

st.subheader("Сравнение времени")
fig = px.bar(
    timings, x="Experiment", y="Time", color="Tool",
    barmode="group",
    title=f"Время работы ({selected_target})"
)
st.plotly_chart(fig, use_container_width=True)
st.dataframe(timings, use_container_width=True)

st.divider()
st.subheader("Детальный просмотр")
selected = st.selectbox("Эксперимент", experiments_list)

# ====== ffuf ======
st.markdown("### 🔧 Результаты ffuf")
df = parse_ffuf_to_df(selected)

if not df.empty:
    normal = df[df["Status"] == 200]
    anomalies = df[df["Status"] != 200]

    col1, col2, col3 = st.columns(3)
    col1.metric("Всего запросов", len(df))
    col2.metric("✅ Нормальных (200)", len(normal))
    col3.metric("⚠️ Аномалий", len(anomalies))

    if not anomalies.empty:
        st.error(f"🔴 Найдено {len(anomalies)} аномалий ffuf")

        by_status = anomalies.groupby("Status").size().reset_index(name="Count")
        st.markdown("**По статусам:**")
        st.dataframe(by_status, use_container_width=True)

        st.markdown("**Аномальные ответы:**")
        st.dataframe(anomalies.sort_values("Status"), use_container_width=True)
    else:
        st.success("Аномалий ffuf не найдено")

    with st.expander(f"✅ Нормальные ответы ffuf ({len(normal)})"):
        st.dataframe(normal, use_container_width=True)

    st.subheader("Распределение по длине ответа (ffuf)")
    fig = px.histogram(
        df, x="Length", color="Status",
        title="Длина ответа по статусам",
        nbins=30
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Нет данных ffuf для этого эксперимента")

# ====== wfuzz ======
st.divider()
st.markdown("### 🔧 Результаты wfuzz")
df_wfuzz = parse_wfuzz_to_df(selected)

if not df_wfuzz.empty:
    normal_w = df_wfuzz[df_wfuzz["Status"] == 200]
    anomalies_w = df_wfuzz[df_wfuzz["Status"] != 200]

    col1, col2, col3 = st.columns(3)
    col1.metric("Всего", len(df_wfuzz))
    col2.metric("✅ Нормальных", len(normal_w))
    col3.metric("⚠️ Аномалий", len(anomalies_w))

    if not anomalies_w.empty:
        st.error(f"🔴 Аномалии wfuzz ({len(anomalies_w)})")
        st.dataframe(anomalies_w, use_container_width=True)

    with st.expander(f"✅ Нормальные ответы wfuzz ({len(normal_w)})"):
        st.dataframe(normal_w, use_container_width=True)
else:
    st.info("Нет данных wfuzz для этого эксперимента")