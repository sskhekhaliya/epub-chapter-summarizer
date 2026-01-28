
import subprocess
import sys

# Provide inputs for Resume?, Rating, Link
inputs = "n\n5\n\n"

process = subprocess.Popen(
    [sys.executable, "main.py", "--limit", "10"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    cwd=r"d:\Projects\Books Summary",
    bufsize=1
)

process.stdin.write(inputs)
process.stdin.flush()

# Redirect output to a file and console
with open('final_verify.log', 'w', encoding='utf-8') as f:
    for line in process.stdout:
        print(line, end='')
        f.write(line)
        f.flush()

process.wait()
