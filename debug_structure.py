from pipeline.ingest import EpiubLoader
from pipeline.output import JSONFormatter
import os

file_path = 'book/Breaking the cycle_ free yourself from sex addiction, porn obsession, and shame.epub'
if not os.path.exists(file_path):
    print(f"File not found: {file_path}")
    exit(1)

loader = EpiubLoader(file_path)
loader.load()
raw = loader.get_chapters()

totals = {'Parts': 0, 'Chapters': 0}
for i, ch in enumerate(raw[:20]):
    is_p = JSONFormatter.is_part(ch['title'], ch.get('level', 0), ch.get('is_parent', False))
    p_status = 'PART' if is_p else 'CHAPTER'
    print(f"{i+1:3} | {p_status:8} | Parent: {str(ch.get('is_parent', False)):5} | {ch['title'][:50]}")
    totals['Parts' if is_p else 'Chapters'] += 1

print("-" * 40)
print(f"Totals: {totals}")
