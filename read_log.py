
import sys
try:
    with open('debug_run.txt', 'r', encoding='utf-16', errors='ignore') as f:
        for i, line in enumerate(f):
            if i > 50: break
            print(line.strip())
except Exception as e:
    print(f"Error: {e}")
