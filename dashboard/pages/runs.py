import streamlit as st
import json, glob, os
import pandas as pd

st.set_page_config(page_title="Runs", page_icon="📋")
st.title("📋 Все запуски")

runs = []

# === n8n Runs (из report_*.json) ===
for f in sorted(glob.glob("/results/report_n8n_*.json"), reverse=True):
    try:
        with open(f) as fp:
            r = json.load(fp)

        tools_list = []
        for tool_name, tool_data in r.get("tools", {}).items():
            if tool_data.get("total", 0) > 0:
                tools_list.append(tool_name)

        schema = r.get("tools", {}).get("schemathesis", {})
        schema_findings = schema.get("failures", 0) + schema.get("errors", 0)

        runs.append({
            "source": "n8n",
            "experiment": r.get("runId", os.path.basename(f)),
            "target": r.get("target", ""),
            "vuln_type": r.get("vulnType", ""),
            "tools": ", ".join(tools_list),
            "total_requests": r.get("totalRequests", 0),
            "anomalies": r.get("totalAnomalies", 0),
            "schema_findings": schema_findings,
            "baseline": r.get("baseline", 0),
            "timestamp": r.get("timestamp", ""),
            "file": os.path.basename(f),
        })
    except Exception:
        pass

# === bash Runs (из timings.csv) ===
timings_path = "/results/timings.csv"
if os.path.exists(timings_path):
    try:
        df_t = pd.read_csv(
            timings_path, header=None,
            names=["Experiment", "Tool", "Target", "Wordlist", "Time"]
        )
        for exp, group in df_t.groupby("Experiment"):
            runs.append({
                "source": "bash",
                "experiment": str(exp),
                "target": str(group["Target"].iloc[0]),
                "vuln_type": "",
                "tools": ", ".join(group["Tool"].unique().tolist()),
                "total_requests": 0,
                "anomalies": 0,
                "schema_findings": 0,
                "baseline": 0,
                "timestamp": "",
                "file": "timings.csv",
            })
    except Exception as e:
        st.warning(f"timings.csv parse error: {e}")

if not runs:
    st.info("Пока нет ни одного запуска. Запусти фаззинг через n8n или bash.")
    st.stop()

df = pd.DataFrame(runs)

# === Фильтры ===
col1, col2, col3 = st.columns(3)
with col1:
    source_filter = st.selectbox("Источник", ["Все", "n8n", "bash"])
with col2:
    targets = ["Все"] + sorted(df["target"].unique().tolist())
    target_filter = st.selectbox("Цель", targets)
with col3:
    sort_by = st.selectbox("Сортировка", [
        "Дата (новые)", "Дата (старые)", "Аномалии", "Запросы"
    ])

if source_filter != "Все":
    df = df[df["source"] == source_filter]
if target_filter != "Все":
    df = df[df["target"] == target_filter]

if sort_by == "Дата (новые)":
    df = df.sort_values("timestamp", ascending=False)
elif sort_by == "Дата (старые)":
    df = df.sort_values("timestamp", ascending=True)
elif sort_by == "Аномалии":
    df = df.sort_values("anomalies", ascending=False)
elif sort_by == "Запросы":
    df = df.sort_values("total_requests", ascending=False)

# === Метрики ===
st.divider()
col1, col2, col3, col4 = st.columns(4)
col1.metric("Всего запусков", len(df))
col2.metric("n8n", len(df[df["source"] == "n8n"]))
col3.metric("bash", len(df[df["source"] == "bash"]))
col4.metric("Суммарно аномалий", int(df["anomalies"].sum()))

# === Таблица ===
st.subheader("Список запусков")
display_cols = [
    "source", "experiment", "target", "vuln_type", "tools",
    "total_requests", "anomalies", "schema_findings", "timestamp",
]
available = [c for c in display_cols if c in df.columns]
display_df = df[available].copy()
display_df.columns = [
    "Источник", "Experiment", "Цель", "Уязвимость", "Инструменты",
    "Запросов", "Аномалий", "Schema-findings", "Дата",
][:len(available)]
st.dataframe(display_df, hide_index=True)

 # === Детали выбранного запуска ===
st.divider()
st.subheader("Детали запуска")

experiments = df["experiment"].astype(str).tolist()
if not experiments:
    st.warning("После фильтров не осталось экспериментов")
    st.stop()

selected = st.selectbox(
    "Выбери эксперимент",
    experiments,
    index=0,
    key="runs_selected_experiment",
)

matches = df[df["experiment"].astype(str) == str(selected)]

if matches.empty:
    st.warning(f"Эксперимент «{selected}» не найден. Возможно, файл удалён.")
    st.stop()

row = matches.reset_index(drop=True).iloc[0]

col1, col2, col3, col4 = st.columns(4)
col1.metric("Источник", row["source"])
col2.metric("Аномалий", int(row["anomalies"]))
col3.metric("Schema-findings", int(row["schema_findings"]))
col4.metric("Baseline", int(row["baseline"]))

if row["source"] == "n8n":
    st.caption(f"Файл отчёта: `{row['file']}`")
    report_path = f"/results/{row['file']}"
    if os.path.exists(report_path):
        with st.expander("📄 Полный JSON отчёта"):
            with open(report_path) as fp:
                st.json(json.load(fp))
else:
    st.caption("bash-запуск. Детали: `/results/ffuf_<exp>.json`, `/results/wfuzz_<exp>.txt`")