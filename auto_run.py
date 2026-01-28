
import subprocess
import sys

# Provide inputs for Resume?, Rating, Link
inputs = "n\n0\n\n"

process = subprocess.Popen(
    [sys.executable, "main.py", "--limit", "6"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    cwd=r"d:\Projects\Books Summary",
    bufsize=1
)

process.stdin.write(inputs)
process.stdin.flush()

with open('trace.txt', 'w', encoding='utf-8') as f:
    for line in process.stdout:
        f.write(line)
        f.flush()

process.wait()
