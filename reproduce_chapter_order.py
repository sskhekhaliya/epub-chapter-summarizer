import os
import sys

# Add current directory to path so we can import 'pipeline'
sys.path.append(r"d:\Projects\Books Summary")

from pipeline.ingest import EpiubLoader

def check_structure():
    book_dir = r"d:\Projects\Books Summary\book"
    if not os.path.exists(book_dir):
        print("No book dir")
        return

    epubs = [f for f in os.listdir(book_dir) if f.lower().endswith(".epub")]
    if not epubs:
        print("No epubs")
        return

    epub_path = os.path.join(book_dir, epubs[0])
    print(f"Checking structure for: {epub_path}")

    loader = EpiubLoader(epub_path)
    loader.load()
    chapters = loader.get_chapters()

    print(f"\nFound {len(chapters)} chapters/sections.")
    print("-" * 50)
    for i, ch in enumerate(chapters):
        print(f"[{i}] {ch.get('title')}")

if __name__ == "__main__":
    check_structure()
