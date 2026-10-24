import streamlit as st
import plotly.graph_objects as go

COLORS = {
    "primary":   "#8ea8d4",   # мягкий синий
    "secondary": "#a8c4e0",   # светло-голубой
    "success":   "#a3c9a8",   # мягкий шалфейный
    "warning":   "#e0c088",   # тёплый песочный
    "danger":    "#d99a9a",   # приглушённый розовый
    "muted":     "#8892a4",   # мягкий серый
}

FUZZER_COLORS = {
    "ffuf":         "#8ea8d4",
    "wfuzz":        "#a8c4e0",
    "feroxbuster":  "#a3c9a8",
    "schemathesis": "#e0c088",
    "cats":         "#d99a9a",
}

# === СТИЛЬ PLOTLY ===
def apply_plotly_theme(fig, title=""):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", size=13, color="#e6edf3"),
        title=dict(text=title, font=dict(size=16, color="#e6edf3")),
        margin=dict(l=40, r=20, t=50, b=40),
        hoverlabel=dict(bgcolor="#161b22", font_size=13),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
    )
    fig.update_xaxes(gridcolor="#21262d", zerolinecolor="#21262d")
    fig.update_yaxes(gridcolor="#21262d", zerolinecolor="#21262d")
    return fig


# === КАРТОЧКА МЕТРИКИ ===
def metric_card(label, value, color=None, delta=None, icon=""):
    color = color or COLORS["primary"]
    delta_html = ""
    if delta is not None:
        d_color = COLORS["success"] if delta >= 0 else COLORS["danger"]
        arrow = "▲" if delta >= 0 else "▼"
        delta_html = f'<span style="color:{d_color};font-size:0.85em;margin-left:6px;">{arrow} {abs(delta)}</span>'

    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #161b22 0%, #0d1117 100%);
        border: 1px solid #21262d;
        border-left: 4px solid {color};
        border-radius: 10px;
        padding: 16px 20px;
        margin-bottom: 8px;
    ">
        <div style="color:#8b949e; font-size:0.85em; text-transform:uppercase; letter-spacing:0.5px;">
            {icon} {label}
        </div>
        <div style="color:#e6edf3; font-size:2em; font-weight:700; margin-top:4px;">
            {value}{delta_html}
        </div>
    </div>
    """, unsafe_allow_html=True)


# === ЗАГОЛОВОК СТРАНИЦЫ ===
def page_header(title, subtitle="", icon=""):
    st.markdown(f"""
    <div style="margin-bottom:24px;">
        <h1 style="color:#e6edf3; margin-bottom:4px;">
            {icon} {title}
        </h1>
        <p style="color:#8b949e; font-size:0.95em; margin:0;">{subtitle}</p>
    </div>
    """, unsafe_allow_html=True)


# === СТАТУС-БЕЙДЖ ===
def status_badge(text, kind="success"):
    colors = {
        "success": COLORS["success"],
        "warning": COLORS["warning"],
        "danger":  COLORS["danger"],
        "info":    COLORS["secondary"],
        "muted":   COLORS["muted"],
    }
    color = colors.get(kind, COLORS["muted"])
    return f'<span style="background:{color}22; color:{color}; padding:2px 8px; border-radius:6px; font-size:0.85em; font-weight:500;">{text}</span>'