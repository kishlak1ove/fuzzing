import subprocess
import json
from typing import List, Dict
import re

def strip_ansi(text: str) -> str:
    """Удаляет ANSI escape-последовательности."""
    ansi = re.compile(r'\x1b\[[0-9;?]*[a-zA-Z]|\x1b\][^\x07]*\x07')
    return ansi.sub('', text)

def get_containers() -> List[Dict]:
    """Возвращает список запущенных контейнеров."""
    try:
        result = subprocess.run(
            ["docker", "ps", "-a", "--format", "{{.Names}}|{{.Status}}|{{.Image}}"],
            capture_output=True, text=True, timeout=10
        )
        containers = []
        for line in result.stdout.strip().split("\n"):
            if line and "|" in line:
                name, status, image = line.split("|", 2)
                containers.append({
                    "name": name,
                    "status": status,
                    "image": image,
                    "running": status.startswith("Up")
                })
        return containers
    except Exception as e:
        return [{"error": str(e)}]


def exec_in_container(container: str, command: List[str], timeout: int = 600) -> Dict:
    """Выполняет команду внутри контейнера."""
    try:
        result = subprocess.run(
            ["docker", "exec", container] + command,
            capture_output=True, text=True, timeout=timeout
        )
        return {
            "success": result.returncode == 0,
            "stdout": strip_ansi(result.stdout),
            "stderr": strip_ansi(result.stderr),
            "returncode": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Таймаут выполнения"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_container_logs(container: str, lines: int = 50) -> str:
    """Возвращает последние строки логов контейнера."""
    try:
        result = subprocess.run(
            ["docker", "logs", "--tail", str(lines), container],
            capture_output=True, text=True, timeout=10
        )
        return result.stdout + result.stderr
    except Exception as e:
        return f"Ошибка: {e}"