import subprocess
import time
import re
from pathlib import Path

RESULTS_DIR = Path("/results")

TARGETS = {
    "Juice Shop": {
        "url": "http://juice-shop:3000",
        "endpoint": "/rest/products/search?q=FUZZ"
    },
    "VulnAPI SQLi": {
        "url": "http://vulnapi:5035",
        "endpoint": "/sqli/search?id=FUZZ"
    },
    "VulnAPI XSS": {
        "url": "http://vulnapi:5035",
        "endpoint": "/search?query=FUZZ"
    },
    "VulnAPI PathTraversal": {
        "url": "http://vulnapi:5035",
        "endpoint": "/ptrav/read?file=FUZZ"
    },
    "VulnAPI CmdInjection": {
        "url": "http://vulnapi:5035",
        "endpoint": "/rce/ping?host=FUZZ"
    },
    "SpringVulny Search": {
        "url": "https://javaspringvulny:9000",
        "endpoint": "/search?query=FUZZ"
    },
    "PyGoat SQL": {
        "url": "http://pygoat:8000",
        "endpoint": "/sql?username=FUZZ"
    },
}


def _strip_ansi(text: str) -> str:
    """Удаляет ANSI escape-последовательности."""
    ansi = re.compile(r'\x1b\[[0-9;?]*[a-zA-Z]|\x1b\][^\x07]*\x07')
    return ansi.sub('', text)


def run_fuzz(wordlist: str, experiment: str, target_name: str = "Juice Shop") -> dict:
    if target_name not in TARGETS:
        return {"success": False, "error": f"Неизвестная цель: {target_name}"}

    target = TARGETS[target_name]
    full_url = target["url"] + target["endpoint"]

    ffuf_out = f"/results/ffuf_{experiment}.json"
    wfuzz_out = f"/results/wfuzz_{experiment}.txt"

    try:
        # ffuf
        start = time.time()
        result_ffuf = subprocess.run(
            ["docker", "exec", "ffuf", "ffuf",
             "-u", full_url,
             "-w", wordlist,
             "-mc", "all",
             "-k",
             "-o", ffuf_out,
             "-of", "json", "-s"],
            capture_output=True, text=True, timeout=900
        )
        ffuf_time = round(time.time() - start, 3)

        # wfuzz — захватываем stdout
        start = time.time()
        result_wfuzz = subprocess.run(
            ["docker", "exec", "wfuzz", "wfuzz",
             "-u", full_url,
             "-w", wordlist,
             "--hc", "404"],
            capture_output=True, text=True, timeout=900
        )
        wfuzz_time = round(time.time() - start, 3)

        # Сохраняем чистый stdout в файл
        wfuzz_clean = _strip_ansi(result_wfuzz.stdout)
        with open(wfuzz_out, "w") as f:
            f.write(wfuzz_clean)

        # timings.csv
        timings_path = RESULTS_DIR / "timings.csv"
        with open(timings_path, "a") as f:
            f.write(f"{experiment},ffuf,{target_name},{wordlist},{ffuf_time}\n")
            f.write(f"{experiment},wfuzz,{target_name},{wordlist},{wfuzz_time}\n")

        return {
            "success": True,
            "experiment": experiment,
            "target": target_name,
            "ffuf_time": ffuf_time,
            "wfuzz_time": wfuzz_time,
            "ffuf_output": _strip_ansi(result_ffuf.stdout[-500:]),
            "wfuzz_output": wfuzz_clean[-1500:]
        }

    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Таймаут (15 мин)"}
    except Exception as e:
        return {"success": False, "error": str(e)}