import json
import re
from pathlib import Path
import pandas as pd

RESULTS_DIR = Path("/results")


def _strip_ansi(text: str) -> str:
    """Удаляет ANSI escape-последовательности."""
    ansi = re.compile(r'\x1b\[[0-9;?]*[a-zA-Z]|\x1b\][^\x07]*\x07')
    return ansi.sub('', text)


def list_experiments() -> list:
    """Список экспериментов — берём из timings.csv."""
    path = RESULTS_DIR / "timings.csv"
    if not path.exists():
        return []
    try:
        df = pd.read_csv(
            path,
            names=["Experiment", "Tool", "Target", "Wordlist", "Time"]
        )
        return sorted(df["Experiment"].unique().tolist())
    except Exception:
        return []


def load_ffuf_results(experiment: str) -> dict:
    """Загружает JSON от ffuf."""
    path = RESULTS_DIR / f"ffuf_{experiment}.json"
    if not path.exists():
        return None
    try:
        with open(path) as f:
            return json.load(f)
    except Exception as e:
        return {"error": str(e)}


def parse_ffuf_to_df(experiment: str) -> pd.DataFrame:
    """Преобразует результаты ffuf в DataFrame."""
    data = load_ffuf_results(experiment)
    if not data or "results" not in data:
        return pd.DataFrame()

    rows = []
    for r in data["results"]:
        rows.append({
            "Payload": r["input"].get("FUZZ", ""),
            "Status": r["status"],
            "Length": r["length"],
            "Words": r.get("words", 0),
            "Lines": r.get("lines", 0),
            "Duration_ms": round(r.get("duration", 0) / 1_000_000, 2),
            "Content-Type": r.get("content-type", "")
        })
    return pd.DataFrame(rows)


def load_timings() -> pd.DataFrame:
    """Загружает timings.csv."""
    path = RESULTS_DIR / "timings.csv"
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(
            path,
            names=["Experiment", "Tool", "Target", "Wordlist", "Time"]
        )
    except Exception:
        return pd.DataFrame()


def load_wfuzz_results(experiment: str) -> str:
    """Загружает TXT от wfuzz с очисткой ANSI."""
    path = RESULTS_DIR / f"wfuzz_{experiment}.txt"
    if not path.exists():
        return ""
    return _strip_ansi(path.read_text())


def parse_wfuzz_to_df(experiment: str) -> pd.DataFrame:
    """
    Парсит вывод wfuzz в DataFrame.
    Корректно склеивает перенесённые payload'ы.
    """
    text = load_wfuzz_results(experiment)
    if not text:
        return pd.DataFrame()

    lines = text.split("\n")
    merged = []

    for line in lines:
        # Строка-начало записи (9 цифр + двоеточие)
        if re.match(r'^\s*\d{9}:', line):
            merged.append(line.rstrip())
        # Пустая строка — пропускаем
        elif not line.strip():
            continue
        # Строки заголовков/итогов — не приклеиваем
        elif line.startswith(("Total", "Processed", "Filtered",
                              "Requests", "===", "*", "Target", "ID")):
            continue
        # Строка-продолжение — приклеиваем
        elif merged:
            merged[-1] += " " + line.strip()

    rows = []
    for line in merged:
        # Формат: 000000245: 200 0 L 19 W 148 Ch "payload"
        m = re.match(
            r'^\s*(\d+):\s+(\d+)\s+(\d+)\s+L\s+(\d+)\s+W\s+(\d+)\s+Ch\s+"?(.*?)"?\s*$',
            line
        )
        if m:
            rows.append({
                "ID": int(m.group(1)),
                "Status": int(m.group(2)),
                "Lines": int(m.group(3)),
                "Words": int(m.group(4)),
                "Length": int(m.group(5)),
                "Payload": m.group(6).strip().strip('"')
            })
    return pd.DataFrame(rows)


def delete_experiment(experiment: str) -> dict:
    """Удаляет все файлы эксперимента."""
    deleted = []
    errors = []

    for pattern in [f"ffuf_{experiment}.json", f"wfuzz_{experiment}.txt"]:
        path = RESULTS_DIR / pattern
        if path.exists():
            try:
                path.unlink()
                deleted.append(pattern)
            except Exception as e:
                errors.append(f"{pattern}: {e}")

    timings_path = RESULTS_DIR / "timings.csv"
    if timings_path.exists():
        try:
            df = pd.read_csv(
                timings_path,
                names=["Experiment", "Tool", "Target", "Wordlist", "Time"]
            )
            df = df[df["Experiment"] != experiment]
            df.to_csv(timings_path, index=False, header=False)
            deleted.append("строки из timings.csv")
        except Exception as e:
            errors.append(f"timings.csv: {e}")

    return {"deleted": deleted, "errors": errors}


def delete_all_experiments() -> dict:
    """Удаляет все результаты экспериментов."""
    deleted = []
    errors = []

    for pattern in ["ffuf_*.json", "wfuzz_*.txt"]:
        for path in RESULTS_DIR.glob(pattern):
            try:
                path.unlink()
                deleted.append(path.name)
            except Exception as e:
                errors.append(f"{path.name}: {e}")

    timings_path = RESULTS_DIR / "timings.csv"
    if timings_path.exists():
        try:
            timings_path.write_text("")
            deleted.append("timings.csv (очищен)")
        except Exception as e:
            errors.append(f"timings.csv: {e}")

    return {"deleted": deleted, "errors": errors}