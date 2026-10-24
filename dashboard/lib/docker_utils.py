import docker
import re
from typing import List, Dict

# Удаляем ANSI-последовательности, так как логи контейнеров могут их содержать
def strip_ansi(text: str) -> str:
    ansi = re.compile(r'\x1b\[[0-9;?]*[a-zA-Z]|\x1b\][^\x07]*\x07')
    return ansi.sub('', text)

def _get_client():
    try:
        return docker.from_env()
    except Exception:
        return None

def get_containers() -> List[Dict]:
    """Возвращает список запущенных контейнеров через Docker SDK."""
    client = _get_client()
    if not client:
        return [{"error": "Не удалось подключиться к Docker Daemon. Проверьте права на socket."}]
    
    try:
        containers = []
        for c in client.containers.list(all=True):
            containers.append({
                "name": c.name,
                "status": c.status,
                "image": c.image.tags[0] if c.image.tags else c.short_id,
                "running": c.status == "running"
            })
        return containers
    except Exception as e:
        return [{"error": str(e)}]

def exec_in_container(container: str, command: List[str], timeout: int = 600) -> Dict:
    """Выполняет команду внутри контейнера через Docker API."""
    client = _get_client()
    if not client:
        return {"success": False, "error": "Нет подключения к Docker."}
    
    try:
        target_container = client.containers.get(container)
        
        # exec_run не имеет встроенного таймаута в SDK, но для быстрых команд работает отлично
        exit_code, output = target_container.exec_run(command)
        out_str = output.decode('utf-8', errors='replace')
        
        return {
            "success": exit_code == 0,
            "stdout": strip_ansi(out_str),
            "stderr": "",  # SDK возвращает объединенный вывод в output
            "returncode": exit_code
        }
    except docker.errors.NotFound:
        return {"success": False, "error": f"Контейнер {container} не найден."}
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_container_logs(container: str, lines: int = 50) -> str:
    """Возвращает последние строки логов контейнера."""
    client = _get_client()
    if not client:
        return "Ошибка: Нет подключения к Docker."
    
    try:
        target_container = client.containers.get(container)
        logs = target_container.logs(tail=lines)
        return strip_ansi(logs.decode('utf-8', errors='replace'))
    except Exception as e:
        return f"Ошибка: {e}"