#!/bin/bash
set -e

WORDLIST="${1:?Использование: ./run_ffuf.sh <wordlist> <experiment> <target>}"
EXPERIMENT="${2:?Укажите название эксперимента}"
TARGET_NAME="${3:?Укажите цель}"

./fuzz.sh "$WORDLIST" "$EXPERIMENT" "$TARGET_NAME" ffuf