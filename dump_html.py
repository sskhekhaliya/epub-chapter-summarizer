
import os
import sys

# Add current directory to path so we can import from pipeline
sys.path.append(os.getcwd())

from pipeline.ingest import EpiubLoader

file_path = r"d:\Projects\Books Summary\book\The Alchemist (Paulo Coelho).epub"

def dump_html(path):
    loader = EpiubLoader(path)
    loader.load()
    chapters = loader.get_chapters()
    
    for i, ch in enumerate(chapters):
        print(f"[{i:02}] Title: {repr(ch['title'])} | Raw Len: {len(ch['content'])}")

if __name__ == "__main__":
    dump_html(file_path)
