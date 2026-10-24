from pymongo import MongoClient
import streamlit as st
import pandas as pd

MONGO_URI = "mongodb://mongodb:27017"
DB_NAME = "web_fuzz"


@st.cache_resource
def get_client():
    """Единое подключение к MongoDB (кэшируется Streamlit)."""
    return MongoClient(MONGO_URI)


def get_db():
    return get_client()[DB_NAME]


# === TARGETS ===
def list_targets():
    """Список всех таргетов."""
    db = get_db()
    return list(db.targets.find().sort("last_seen", -1))


# === RUNS ===
def list_runs(limit=100, target=None, vuln_type=None):
    """Список последних запусков."""
    db = get_db()
    query = {}
    if target:
        query["target"] = target
    if vuln_type:
        query["vulnType"] = vuln_type

    cursor = db.runs.find(query).sort("timestamp", -1).limit(limit)
    return list(cursor)


def get_run(run_id):
    """Один run по runId."""
    db = get_db()
    return db.runs.find_one({"_id": run_id}) or db.runs.find_one({"runId": run_id})


def get_runs_df(limit=100, target=None, vuln_type=None):
    """DataFrame с runs (для таблиц/графиков)."""
    runs = list_runs(limit, target, vuln_type)
    if not runs:
        return pd.DataFrame()

    rows = []
    for r in runs:
        tools = r.get("tools", {}) or {}
        rows.append({
            "runId": r.get("runId") or str(r.get("_id", "")),
            "target": r.get("target", ""),
            "vulnType": r.get("vulnType", ""),
            "timestamp": r.get("timestamp"),
            "totalRequests": r.get("totalRequests", 0),
            "totalAnomalies": r.get("totalAnomalies", 0),
            "endpointsTested": r.get("endpointsTested", 0),
            "paramsTested": r.get("paramsTested", 0),
            "ffuf_total": tools.get("ffuf", {}).get("total", 0),
            "ffuf_anom": tools.get("ffuf", {}).get("anomalies", 0),
            "wfuzz_total": tools.get("wfuzz", {}).get("total", 0),
            "wfuzz_anom": tools.get("wfuzz", {}).get("anomalies", 0),
            "schema_total": tools.get("schemathesis", {}).get("total", 0),
            "schema_failures": tools.get("schemathesis", {}).get("failures", 0),
            "cats_total": tools.get("cats", {}).get("total", 0),
            "cats_errors": tools.get("cats", {}).get("errors", 0),
        })
    return pd.DataFrame(rows)


# === FINDINGS ===
def list_findings(run_id, tool=None, limit=1000):
    """Findings для конкретного run."""
    db = get_db()
    query = {"runId": run_id}
    if tool:
        query["tool"] = tool

    cursor = db.findings.find(query).limit(limit)
    return list(cursor)


def get_findings_df(run_id, tool=None, limit=1000):
    """DataFrame с findings."""
    findings = list_findings(run_id, tool, limit)
    if not findings:
        return pd.DataFrame()

    rows = []
    for f in findings:
        rows.append({
            "tool": f.get("tool", ""),
            "endpoint": f.get("endpoint", ""),
            "param": f.get("param", ""),
            "payload": f.get("payload", ""),
            "status": f.get("status"),
            "length": f.get("length"),
            "time_ms": f.get("time_ms"),
            "message": f.get("message", ""),
            "isFailure": f.get("isFailure"),
            "isError": f.get("isError"),
        })
    return pd.DataFrame(rows)


# === AGGREGATIONS ===
def count_findings_by_tool(run_id):
    """Сколько findings каждого инструмента в run."""
    db = get_db()
    cursor = db.findings.aggregate([
        {"$match": {"runId": run_id}},
        {"$group": {"_id": "$tool", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ])
    return {doc["_id"]: doc["count"] for doc in cursor}


def top_endpoints(run_id, limit=10):
    """Топ эндпоинтов по числу аномалий."""
    db = get_db()
    cursor = db.findings.aggregate([
        {"$match": {"runId": run_id}},
        {"$group": {"_id": "$endpoint", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": limit}
    ])
    return [{"endpoint": doc["_id"], "count": doc["count"]} for doc in cursor]


def compare_runs(run_id_new, run_id_old):
    """Сравнение findings двух запусков — что нового, что исчезло."""
    db = get_db()

    new_keys = set()
    old_keys = set()

    # Формируем уникальный ключ для каждого finding
    def make_key(f):
        return f"{f.get('tool')}|{f.get('endpoint')}|{f.get('payload', '')[:100]}"

    for f in db.findings.find({"runId": run_id_new}):
        new_keys.add(make_key(f))
    for f in db.findings.find({"runId": run_id_old}):
        old_keys.add(make_key(f))

    return {
        "new": len(new_keys - old_keys),
        "removed": len(old_keys - new_keys),
        "common": len(new_keys & old_keys),
        "new_keys": list(new_keys - old_keys)[:50],
        "removed_keys": list(old_keys - new_keys)[:50],
    }