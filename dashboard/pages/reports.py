import streamlit as st
import json, glob, os
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="n8n Reports", page_icon="📊")
st.title("📊 Отчёты n8n")

files = sorted(glob.glob("/results/report_n8n_*.json"), reverse=True)
if not files:
    st.info("Отчётов n8n пока нет. Запусти фаззинг через n8n.")
    st.stop()

selected = st.selectbox("Отчёт", [os.path.basename(f) for f in files])
with open(f"/results/{selected}") as fp:
    report = json.load(fp)

# Метрики
col1, col2, col3, col4 = st.columns(4)
col1.metric("Всего запросов", report.get("totalRequests", 0))
col2.metric("Аномалий", report.get("totalAnomalies", 0))
col3.metric("Baseline", report.get("baseline", 0))
col4.metric("Эндпоинтов", report.get("endpointsTested", 0))

# Разбивка по статусам
st.subheader("Ответы по статусам")
sb = report.get("statusBreakdown", {})
if sb:
    df = pd.DataFrame(list(sb.items()), columns=["Status", "Count"])
    st.bar_chart(df.set_index("Status"))

# Сравнение ffuf vs wfuzz
st.subheader("Сравнение инструментов")
tools = report.get("tools", {})
if tools:
    rows = []
    for name, data in tools.items():
        rows.append({
            "Tool": name,
            "Total": data.get("total", 0),
            "Anomalies": data.get("anomalies", 0),
        })
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True)
    fig = px.bar(df, x="Tool", y=["Total", "Anomalies"], barmode="group")
    st.plotly_chart(fig, use_container_width=True)

# Топ аномалий
st.subheader(f"Топ аномалий ({len(report.get('topAnomalies', []))})")
top = report.get("topAnomalies", [])
if top:
    df = pd.DataFrame(top)
    st.dataframe(df, use_container_width=True)
else:
    st.success("Аномалий не найдено")


# === SCHEMATHESIS ===
st.subheader("🔬 Schemathesis (spec-based fuzzer)")
schema = tools.get("schemathesis", {})
if schema and schema.get("total", 0) > 0:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Findings", schema.get("total", 0))
    col2.metric("Failures", schema.get("failures", 0))
    col3.metric("Errors", schema.get("errors", 0))
    col4.metric("Skipped", schema.get("skipped", 0))

    findings = report.get("schemathesisFindings", [])
    if findings:
        df_schema = pd.DataFrame(findings)
        keep = [c for c in ["method", "endpoint", "message", "isFailure", "isError", "time_ms"]
                if c in df_schema.columns]
        st.dataframe(df_schema[keep], hide_index=True)

        fig = px.pie(
            values=[schema.get("failures", 0), schema.get("errors", 0)],
            names=["Failures", "Errors"],
            title="Типы находок Schemathesis",
        )
        st.plotly_chart(fig)
    else:
        st.info("Findings отсутствуют — все тесты прошли")
else:
    st.info("Schemathesis не запускался (нет OpenAPI у цели)")