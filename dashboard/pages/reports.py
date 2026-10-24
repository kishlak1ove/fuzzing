import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import sys
sys.path.insert(0, "/app")

from lib.ui import (
    page_header, metric_card, apply_plotly_theme,
    COLORS, status_badge,
)
from lib.mongo_client import (
    get_db, list_runs, get_findings_df,
    count_findings_by_tool, top_endpoints, compare_runs,
)

st.set_page_config(page_title="Reports", page_icon="📊", layout="wide")
page_header("Отчёты", "Фаззинг с покрытием OWASP Top 10", "📊")

db = get_db()

# === ФИЛЬТРЫ ===
col1, col2, col3 = st.columns(3)
with col1:
    target_filter = st.selectbox(
        "🎯 Target",
        ["Все"] + sorted(db.targets.distinct("url")),
    )
with col2:
    vuln_filter = st.selectbox(
        "🎯 Уязвимость",
        ["Все"] + sorted([v for v in db.runs.distinct("vulnType") if v]),
    )
with col3:
    owasp_filter = st.selectbox(
        "🔐 OWASP",
        ["Все", "A01", "A02", "A03", "A04", "A05",
         "A06", "A07", "A08", "A09", "A10"],
    )

# === СПИСОК RUN ===
target_opt = None if target_filter == "Все" else target_filter
vuln_opt = None if vuln_filter == "Все" else vuln_filter
runs = list_runs(limit=200, target=target_opt, vuln_type=vuln_opt)

if owasp_filter != "Все":
    runs = [r for r in runs if r.get("owaspCategory") == owasp_filter]

if not runs:
    st.warning("Нет запусков под выбранные фильтры.")
    st.stop()

options = [
    f"{r.get('target', '?')} | {r.get('vulnType', '?')} | {r.get('timestamp', '?')}"
    for r in runs
]
selected_label = st.selectbox("📁 Запуск", options, index=0)
selected_run = runs[options.index(selected_label)]
run_id = selected_run.get("runId")

st.divider()

# === МЕТРИКИ ===
tools = selected_run.get("tools", {}) or {}

col1, col2, col3, col4 = st.columns(4)
with col1:
    metric_card("Запросов", selected_run.get("totalRequests", 0),
                color=COLORS["primary"], icon="🔢")
with col2:
    metric_card("Аномалий", selected_run.get("totalAnomalies", 0),
                color=COLORS["danger"], icon="⚠️")
with col3:
    metric_card("Baseline", selected_run.get("baseline", 0),
                color=COLORS["secondary"], icon="📏")
with col4:
    metric_card("Эндпоинтов", selected_run.get("endpointsTested", 0),
                color=COLORS["success"], icon="🎯")

# === OWASP-КАРТОЧКА ===
owasp_cat = selected_run.get("owaspCategory", "")
owasp_name = selected_run.get("owaspName", "")

if owasp_cat:
    st.markdown(
        f"""
        <div style="
            background: {COLORS['primary']}15;
            border-left: 3px solid {COLORS['primary']};
            border-radius: 8px;
            padding: 12px 18px;
            margin: 16px 0;
        ">
            <span style="color:{COLORS['muted']}; font-size:0.9em;">🔐 OWASP Top 10 →</span>
            <span style="color:{COLORS['primary']}; font-weight:700; font-size:1.05em; margin-left:8px;">{owasp_cat}</span>
            <span style="color:#c9d1d9; margin-left:10px;">{owasp_name}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.caption(f"🎯 `{selected_run.get('target', '')}`  ·  RunId: `{run_id}`")

st.divider()

# === ВКЛАДКИ ===
tab_overview, tab_dict, tab_schema, tab_dynamics, tab_owasp, tab_metrics = st.tabs([
    "📊 Обзор", "🗡 Dictionary", "🔬 Schema", "📈 Динамика", "🔐 OWASP", "📊 Метрики"
])

# ============ TAB 1: OVERVIEW ============
with tab_overview:
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("##### 📊 Ответы по статусам")
        sb = selected_run.get("statusBreakdown", {})
        if sb:
            df_status = pd.DataFrame(
                [{"Status": str(k), "Count": int(v)} for k, v in sb.items()]
            ).sort_values("Status")
            colors_map = []
            for s in df_status["Status"]:
                if s.startswith("2"):
                    colors_map.append(COLORS["success"])
                elif s.startswith("3"):
                    colors_map.append(COLORS["secondary"])
                elif s.startswith("4"):
                    colors_map.append(COLORS["warning"])
                else:
                    colors_map.append(COLORS["danger"])
            fig = go.Figure(go.Bar(
                x=df_status["Status"], y=df_status["Count"],
                marker_color=colors_map,
                text=df_status["Count"], textposition="outside",
            ))
            apply_plotly_theme(fig, "")
            fig.update_layout(showlegend=False, height=320)
            st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.markdown("##### 🛠 Сравнение инструментов")
        if tools:
            rows = []
            for name, data in tools.items():
                rows.append({
                    "Tool": str(name),
                    "Total": int(data.get("total", 0)),
                    "Findings": int(
                        data.get("failures", 0)
                        or data.get("errors", 0)
                        or data.get("anomalies", 0)
                    ),
                })
            df_tools = pd.DataFrame(rows)

            fig = go.Figure()
            fig.add_trace(go.Bar(
                name="Всего",
                x=df_tools["Tool"], y=df_tools["Total"],
                marker_color=COLORS["muted"],
                text=df_tools["Total"], textposition="outside",
            ))
            fig.add_trace(go.Bar(
                name="Findings",
                x=df_tools["Tool"], y=df_tools["Findings"],
                marker_color=COLORS["danger"],
                text=df_tools["Findings"], textposition="outside",
            ))
            apply_plotly_theme(fig, "")
            fig.update_layout(barmode="group", height=320,
                              legend=dict(orientation="h", y=1.15))
            st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.markdown("##### 🎯 Топ эндпоинтов по аномалиям")
    top_eps = top_endpoints(run_id, limit=12)
    if top_eps:
        df_top_eps = pd.DataFrame(top_eps)
        fig = go.Figure(go.Bar(
            x=df_top_eps["count"], y=df_top_eps["endpoint"],
            orientation="h",
            marker_color=COLORS["primary"],
            text=df_top_eps["count"], textposition="outside",
        ))
        apply_plotly_theme(fig, "")
        fig.update_layout(height=380)
        st.plotly_chart(fig, use_container_width=True)


# ============ TAB 2: DICTIONARY ============
with tab_dict:
    st.caption(
        "Findings из словарных фаззеров. **Зависят от типа уязвимости.** "
        "Покрывают OWASP A03 (Injection)."
    )

    counts = count_findings_by_tool(run_id)
    dict_counts = {k: v for k, v in counts.items() if k in ["ffuf", "wfuzz"]}

    if not dict_counts:
        st.info("Нет dictionary findings.")
    else:
        cols = st.columns(len(dict_counts))
        for i, (tool, cnt) in enumerate(dict_counts.items()):
            with cols[i]:
                st.metric(tool, cnt)

        st.divider()

        tool_choice = st.selectbox(
            "Инструмент", ["Все"] + list(dict_counts.keys()),
            key="dict_tool_filter",
        )
        df_dict = get_findings_df(
            run_id,
            tool=None if tool_choice == "Все" else tool_choice,
            limit=2000,
        )

        if not df_dict.empty:
            csv = df_dict.to_csv(index=False).encode("utf-8")
            st.download_button(
                "⬇️ CSV",
                data=csv,
                file_name=f"{run_id}_dict.csv",
                mime="text/csv",
                key="dict_csv",
            )
            st.dataframe(df_dict, use_container_width=True, height=500)


# ============ TAB 3: SCHEMA ============
with tab_schema:
    st.caption(
        "Findings из schema-based фаззеров. **Не зависят от типа уязвимости.** "
        "Покрывают OWASP A05, A08, A10."
    )

    schema_counts = {k: v for k, v in counts.items()
                     if k in ["schemathesis", "cats"]}

    if not schema_counts:
        st.info("Нет schema findings.")
    else:
        cols = st.columns(len(schema_counts))
        for i, (tool, cnt) in enumerate(schema_counts.items()):
            with cols[i]:
                st.metric(tool, cnt)

        st.divider()

        tool_choice = st.selectbox(
            "Инструмент", ["Все"] + list(schema_counts.keys()),
            key="schema_tool_filter",
        )
        df_schema = get_findings_df(
            run_id,
            tool=None if tool_choice == "Все" else tool_choice,
            limit=2000,
        )

        if not df_schema.empty:
            csv = df_schema.to_csv(index=False).encode("utf-8")
            st.download_button(
                "⬇️ CSV",
                data=csv,
                file_name=f"{run_id}_schema.csv",
                mime="text/csv",
                key="schema_csv",
            )
            st.dataframe(df_schema, use_container_width=True, height=500)


# ============ TAB 4: DYNAMICS ============
with tab_dynamics:
    st.markdown("##### 📈 Динамика по времени")
    st.caption(
        "Показывает как менялись аномалии между запусками одной цели "
        "и одного типа уязвимости."
    )

    same_runs = [
        r for r in runs
        if r.get("target") == selected_run.get("target")
        and r.get("vulnType") == selected_run.get("vulnType")
    ]

    if len(same_runs) < 2:
        st.info(
            f"Нужно ≥2 запуска с target=`{selected_run.get('target')}` "
            f"и vulnType=`{selected_run.get('vulnType')}`. Сейчас: {len(same_runs)}."
        )
    else:
        df_hist = pd.DataFrame([
            {
                "timestamp": r.get("timestamp"),
                "requests": r.get("totalRequests", 0),
                "anomalies": r.get("totalAnomalies", 0),
            }
            for r in reversed(same_runs)
        ])

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_hist["timestamp"], y=df_hist["requests"],
            mode="lines+markers", name="Запросов",
            line=dict(color=COLORS["primary"], width=2),
            marker=dict(size=8),
        ))
        fig.add_trace(go.Scatter(
            x=df_hist["timestamp"], y=df_hist["anomalies"],
            mode="lines+markers", name="Аномалий",
            line=dict(color=COLORS["danger"], width=2),
            marker=dict(size=8),
        ))
        apply_plotly_theme(fig, "")
        fig.update_layout(height=350, legend=dict(orientation="h", y=1.15))
        st.plotly_chart(fig, use_container_width=True)

        st.divider()
        st.markdown("##### 🔬 Diff с предыдущим запуском")

        prev = same_runs[1]
        diff = compare_runs(run_id, prev.get("runId"))

        col1, col2, col3 = st.columns(3)
        col1.metric("🆕 Новых", diff["new"])
        col2.metric("❌ Исчезло", diff["removed"])
        col3.metric("🔄 Общих", diff["common"])


# ============ TAB 5: OWASP ============
with tab_owasp:
    st.markdown("##### 🔐 Покрытие OWASP Top 10")

    all_runs = list_runs(limit=500)

    owasp_map = {
        "A01": "Broken Access Control",
        "A02": "Cryptographic Failures",
        "A03": "Injection",
        "A04": "Insecure Design",
        "A05": "Security Misconfiguration",
        "A06": "Vulnerable and Outdated Components",
        "A07": "Identification and Authentication Failures",
        "A08": "Software and Data Integrity Failures",
        "A09": "Security Logging and Monitoring Failures",
        "A10": "Server-Side Request Forgery (SSRF)",
    }

    counts_owasp = {cat: 0 for cat in owasp_map}
    findings_owasp = {cat: 0 for cat in owasp_map}

    for r in all_runs:
        cat = r.get("owaspCategory")
        if cat in counts_owasp:
            counts_owasp[cat] += 1

    for f in db.findings.find({}, {"owaspCategory": 1}):
        cat = f.get("owaspCategory")
        if cat in findings_owasp:
            findings_owasp[cat] += 1

    df_owasp = pd.DataFrame([
        {
            "Код": cat,
            "Категория": owasp_map[cat],
            "Запусков": counts_owasp[cat],
            "Findings": findings_owasp[cat],
        }
        for cat in owasp_map
    ])

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Запусков",
        x=df_owasp["Код"], y=df_owasp["Запусков"],
        marker_color=COLORS["primary"],
        text=df_owasp["Запусков"], textposition="outside",
    ))
    fig.add_trace(go.Bar(
        name="Findings",
        x=df_owasp["Код"], y=df_owasp["Findings"],
        marker_color=COLORS["danger"],
        text=df_owasp["Findings"], textposition="outside",
    ))
    apply_plotly_theme(fig, "")
    fig.update_layout(barmode="group", height=380,
                      legend=dict(orientation="h", y=1.15))
    st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.dataframe(df_owasp, use_container_width=True, hide_index=True)

    total_covered = sum(1 for c in counts_owasp.values() if c > 0)
    st.caption(f"📊 Покрыто **{total_covered} / 10** категорий OWASP Top 10")

    # ============ TAB 6: METRICS ============
with tab_metrics:
    st.markdown("##### 📊 Метрики фаззинга")
    st.caption(
        "Собираются автоматически из MongoDB (`runs.metrics`). "
        "Показывают эффективность и производительность каждого запуска."
    )
    
    # === Все запуски с метриками ===
    all_runs_m = list_runs(limit=500)
    
    # Фильтр: только runs, где есть metrics
    runs_with_metrics = [r for r in all_runs_m if r.get("metrics")]
    
    if not runs_with_metrics:
        st.warning("Нет запусков с заполненными метриками. Запусти Analyze workflow.")
        st.stop()
    
    # === Карточки текущего выбранного запуска ===
    st.markdown(f"##### 🎯 Текущий запуск")
    st.caption(f"`{selected_run.get('target', '')}` · RunId: `{run_id}`")
    
    metrics = selected_run.get("metrics", {}) or {}
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        metric_card(
            "Duration",
            f"{metrics.get('totalDurationSec', '—')} s",
            color=COLORS["primary"],
            icon="⏱"
        )
    with col2:
        metric_card(
            "Req/sec",
            metrics.get("requestsPerSec", "—"),
            color=COLORS["success"],
            icon="⚡"
        )
    with col3:
        metric_card(
            "Finding Rate",
            f"{round(metrics.get('findingRate', 0) * 100, 2)} %",
            color=COLORS["warning"],
            icon="🎯"
        )
    with col4:
        metric_card(
            "OWASP Coverage",
            f"{metrics.get('owaspCoverage', 0)} / 10",
            color=COLORS["danger"],
            icon="🔐"
        )
    
    st.divider()
    
    # === Bar chart: Duration по всем runs ===
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.markdown("##### ⏱ Длительность по запускам")
        
        df_duration = pd.DataFrame([
            {
                "RunId": r.get("runId", "?")[-40:],
                "Target": r.get("target", "?"),
                "Duration (sec)": (r.get("metrics") or {}).get("totalDurationSec", 0) or 0,
            }
            for r in runs_with_metrics
        ]).sort_values("Duration (sec)", ascending=False).head(15)
        
        fig = go.Figure(go.Bar(
            x=df_duration["RunId"],
            y=df_duration["Duration (sec)"],
            marker_color=COLORS["primary"],
            text=df_duration["Duration (sec)"].round(0).astype(int),
            textposition="outside",
            hovertemplate="<b>%{x}</b><br>%{y} sec<br>Target: %{customdata}",
            customdata=df_duration["Target"],
        ))
        apply_plotly_theme(fig, "")
        fig.update_layout(
            height=380,
            xaxis=dict(tickangle=-45),
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col_right:
        st.markdown("##### ⚡ Пропускная способность (Req/sec)")
        
        df_rps = pd.DataFrame([
            {
                "RunId": r.get("runId", "?")[-40:],
                "Req/sec": (r.get("metrics") or {}).get("requestsPerSec", 0) or 0,
                "Requests": r.get("totalRequests", 0),
            }
            for r in runs_with_metrics
        ]).sort_values("Req/sec", ascending=False).head(15)
        
        fig = go.Figure(go.Bar(
            x=df_rps["RunId"],
            y=df_rps["Req/sec"],
            marker_color=COLORS["success"],
            text=df_rps["Req/sec"].round(1),
            textposition="outside",
            hovertemplate="<b>%{x}</b><br>%{y} req/sec<br>Total: %{customdata}",
            customdata=df_rps["Requests"],
        ))
        apply_plotly_theme(fig, "")
        fig.update_layout(
            height=380,
            xaxis=dict(tickangle=-45),
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # === Line chart: динамика по времени ===
    st.markdown("##### 📈 Динамика метрик по времени")
    
    # Фильтр: одна цель + один тип уязвимости
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        targets_m = ["Все"] + sorted(set(r.get("target", "?") for r in runs_with_metrics))
        target_filter_m = st.selectbox("🎯 Target", targets_m, key="metrics_target")
    with col_f2:
        vuln_filter_m = ["Все"] + sorted(set(r.get("vulnType", "?") for r in runs_with_metrics))
        vuln_choice_m = st.selectbox("🎯 Vulnerability", vuln_filter_m, key="metrics_vuln")
    
    filtered_runs = runs_with_metrics
    if target_filter_m != "Все":
        filtered_runs = [r for r in filtered_runs if r.get("target") == target_filter_m]
    if vuln_choice_m != "Все":
        filtered_runs = [r for r in filtered_runs if r.get("vulnType") == vuln_choice_m]
    
    if len(filtered_runs) < 2:
        st.info(f"Нужно ≥2 запуска. Сейчас: {len(filtered_runs)}.")
    else:
        df_hist = pd.DataFrame([
            {
                "timestamp": r.get("timestamp", ""),
                "Duration": (r.get("metrics") or {}).get("totalDurationSec", 0) or 0,
                "Req/sec": (r.get("metrics") or {}).get("requestsPerSec", 0) or 0,
                "FindingRate": ((r.get("metrics") or {}).get("findingRate", 0) or 0) * 100,
                "Anomalies": r.get("totalAnomalies", 0),
            }
            for r in sorted(filtered_runs, key=lambda x: x.get("timestamp", ""))
        ])
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_hist["timestamp"], y=df_hist["Duration"],
            mode="lines+markers", name="Duration (sec)",
            line=dict(color=COLORS["primary"], width=2),
            marker=dict(size=10),
        ))
        fig.add_trace(go.Scatter(
            x=df_hist["timestamp"], y=df_hist["Anomalies"],
            mode="lines+markers", name="Anomalies",
            yaxis="y2",
            line=dict(color=COLORS["danger"], width=2),
            marker=dict(size=10),
        ))
        apply_plotly_theme(fig, "")
        fig.update_layout(
            height=380,
            yaxis=dict(title="Duration (sec)"),
            yaxis2=dict(title="Anomalies", overlaying="y", side="right"),
            legend=dict(orientation="h", y=1.15),
        )
        st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # === OWASP Heatmap ===
    st.markdown("##### 🔐 OWASP Coverage Matrix")
    
    owasp_cats = ["A01", "A02", "A03", "A04", "A05", "A06", "A07", "A08", "A09", "A10"]
    
    # Матрица: runs × OWASP
    heatmap_data = []
    heatmap_y = []
    for r in runs_with_metrics[:20]:
        row = []
        run_cat = r.get("owaspCategory", "")
        for cat in owasp_cats:
            row.append(1 if cat == run_cat else 0)
        heatmap_data.append(row)
        heatmap_y.append(r.get("runId", "?")[-30:])
    
    if heatmap_data:
        fig = go.Figure(data=go.Heatmap(
            z=heatmap_data,
            x=owasp_cats,
            y=heatmap_y,
            colorscale=[
                [0, "#1c2128"],
                [1, COLORS["success"]],
            ],
            showscale=False,
            hovertemplate="<b>%{y}</b><br>%{x}<br>Status: %{z}<extra></extra>",
        ))
        apply_plotly_theme(fig, "")
        fig.update_layout(height=max(300, len(heatmap_y) * 30))
        st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # === Сравнение инструментов ===
    st.markdown("##### 🛠 Сравнение инструментов по находкам")
    
    tool_data = {}
    for r in runs_with_metrics:
        tools_r = r.get("tools", {}) or {}
        for tool_name, tool_stats in tools_r.items():
            if tool_name not in tool_data:
                tool_data[tool_name] = {
                    "total": 0,
                    "findings": 0,
                    "runs": 0,
                }
            total = tool_stats.get("total", 0) or 0
            findings = (
                tool_stats.get("findings", 0)
                or tool_stats.get("failures", 0)
                or tool_stats.get("anomalies", 0)
                or 0
            )
            tool_data[tool_name]["total"] += total
            tool_data[tool_name]["findings"] += findings
            if total > 0:
                tool_data[tool_name]["runs"] += 1
    
    if tool_data:
        df_tools_m = pd.DataFrame([
            {
                "Tool": t,
                "Runs": d["runs"],
                "Total Requests": d["total"],
                "Findings": d["findings"],
                "Finding Rate": round(d["findings"] / d["total"] * 100, 2) if d["total"] > 0 else 0,
            }
            for t, d in tool_data.items()
        ]).sort_values("Findings", ascending=False)
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            name="Total",
            x=df_tools_m["Tool"], y=df_tools_m["Total Requests"],
            marker_color=COLORS["muted"],
            text=df_tools_m["Total Requests"],
            textposition="outside",
        ))
        fig.add_trace(go.Bar(
            name="Findings",
            x=df_tools_m["Tool"], y=df_tools_m["Findings"],
            marker_color=COLORS["danger"],
            text=df_tools_m["Findings"],
            textposition="outside",
        ))
        apply_plotly_theme(fig, "")
        fig.update_layout(
            barmode="group",
            height=380,
            legend=dict(orientation="h", y=1.15),
        )
        st.plotly_chart(fig, use_container_width=True)
        
        st.dataframe(df_tools_m, use_container_width=True, hide_index=True)
    
    st.divider()
    
    # === Raw таблица + CSV ===
    st.markdown("##### 📄 Все метрики (raw)")
    
    df_raw = pd.DataFrame([
        {
            "RunId": r.get("runId", "?"),
            "Target": r.get("target", "?"),
            "VulnType": r.get("vulnType", "?"),
            "OWASP": r.get("owaspCategory", "?"),
            "Duration (sec)": (r.get("metrics") or {}).get("totalDurationSec", 0),
            "Req/sec": (r.get("metrics") or {}).get("requestsPerSec", 0),
            "TotalRequests": r.get("totalRequests", 0),
            "Anomalies": r.get("totalAnomalies", 0),
            "FindingRate": (r.get("metrics") or {}).get("findingRate", 0),
            "OWASP_Coverage": (r.get("metrics") or {}).get("owaspCoverage", 0),
            "Timestamp": r.get("timestamp", ""),
        }
        for r in runs_with_metrics
    ])
    
    csv_metrics = df_raw.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Скачать CSV метрик",
        data=csv_metrics,
        file_name="fuzzing_metrics.csv",
        mime="text/csv",
        key="metrics_csv",
    )
    
    st.dataframe(df_raw, use_container_width=True, height=400, hide_index=True)