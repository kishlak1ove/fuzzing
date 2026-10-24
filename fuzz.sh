#!/bin/bash
set -e

WORDLIST="${1:?Использование: ./fuzz.sh <wordlist> <experiment> <target> [tool]}"
EXPERIMENT="${2:?Укажите название эксперимента}"
TARGET_NAME="${3:?Укажите цель}"
TOOL="${4:-all}"

# Определяем URL цели через case (совместимо с Bash 3.2)
case "$TARGET_NAME" in
    "Juice Shop")
        FULL_URL="http://juice-shop:3000/rest/products/search?q=FUZZ"
        ;;
    "VulnAPI SQLi")
        FULL_URL="http://vulnapi:5035/sqli/search?id=FUZZ"
        ;;
    "VulnAPI XSS")
        FULL_URL="http://vulnapi:5035/search?query=FUZZ"
        ;;
    "VulnAPI PathTraversal")
        FULL_URL="http://vulnapi:5035/ptrav/read?file=FUZZ"
        ;;
    "VulnAPI CmdInjection")
        FULL_URL="http://vulnapi:5035/rce/ping?host=FUZZ"
        ;;
    "SpringVulny Search")
        FULL_URL="https://javaspringvulny:9000/search?query=FUZZ"
        ;;
    "PyGoat SQL")
        FULL_URL="http://pygoat:8000/sql?username=FUZZ"
        ;;
    *)
        echo "ERROR: неизвестная цель '$TARGET_NAME'"
        echo "Доступные цели:"
        echo "  - Juice Shop"
        echo "  - VulnAPI SQLi"
        echo "  - VulnAPI XSS"
        echo "  - VulnAPI PathTraversal"
        echo "  - VulnAPI CmdInjection"
        echo "  - SpringVulny Search"
        echo "  - PyGoat SQL"
        exit 1
        ;;
esac

echo "======================================"
echo " Эксперимент: $EXPERIMENT"
echo "======================================"
echo "  Цель:        $TARGET_NAME"
echo "  URL:         $FULL_URL"
echo "  Словарь:     $WORDLIST"
echo "  Инструмент:  $TOOL"
echo

# ---- ffuf ----
if [ "$TOOL" = "ffuf" ] || [ "$TOOL" = "all" ]; then
    echo "[ffuf] Запуск..."
    START=$(perl -MTime::HiRes=time -e 'printf "%.6f", time')
    docker exec ffuf ffuf \
        -u "$FULL_URL" \
        -w "$WORDLIST" \
        -mc all \
        -k \
        -o "/results/ffuf_${EXPERIMENT}.json" \
        -of json \
        -s
    END=$(perl -MTime::HiRes=time -e 'printf "%.6f", time')
    ELAPSED=$(perl -e "printf '%.3f', $END - $START")
    echo "[ffuf] DONE: ${ELAPSED}s"
    echo "$EXPERIMENT,ffuf,$TARGET_NAME,$WORDLIST,${ELAPSED}" >> "./results/timings.csv"
fi

# ---- wfuzz ----
if [ "$TOOL" = "wfuzz" ] || [ "$TOOL" = "all" ]; then
    echo
    echo "[wfuzz] Запуск..."
    START=$(perl -MTime::HiRes=time -e 'printf "%.6f", time')
    docker exec wfuzz wfuzz \
        -u "$FULL_URL" \
        -w "$WORDLIST" \
        -f "/results/wfuzz_${EXPERIMENT}.txt"
    END=$(perl -MTime::HiRes=time -e 'printf "%.6f", time')
    ELAPSED=$(perl -e "printf '%.3f', $END - $START")
    echo "[wfuzz] DONE: ${ELAPSED}s"
    echo "$EXPERIMENT,wfuzz,$TARGET_NAME,$WORDLIST,${ELAPSED}" >> "./results/timings.csv"
fi

echo
echo "======================================"
echo " Готово: $EXPERIMENT"
echo "======================================"
tail -3 "./results/timings.csv" 2>/dev/null || true