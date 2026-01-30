
import os
import sys

# Add current directory to path
sys.path.append(os.getcwd())

from pipeline.ingest import EpiubLoader

def debug_part_content():
    epub_path = r"book\Carnegie, Dale - How to Win Friends and Influence People (2010, Simon & Schuster) - libgen.li.epub"
    if not os.path.exists(epub_path):
        print("EPUB not found")
        return

    loader = EpiubLoader(epub_path)
    loader.load()
    chapters = loader.get_chapters()
    
    print("\n=== DEBUG PART CONTENT ===")
    for ch in chapters:
        if "PART ONE" in ch['title'].upper():
            print(f"Title: {ch['title']}")
            content = ch['content']
            print(f"Content Length: {len(content)}")
            print(f"Content Preview (First 500 chars):\n{content[:500]}")
            print("-" * 40)
            
            # Check for Chapter 1 overlap
            if "Gather Honey" in content:
                print("CRITICAL: 'Gather Honey' (Chapter 1 title) FOUND in Part One content!")
            else:
                 print("PASS: 'Gather Honey' NOT found in Part One content.")
            break

if __name__ == "__main__":
    debug_part_content()
