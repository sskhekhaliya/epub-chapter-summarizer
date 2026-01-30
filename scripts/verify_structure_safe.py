
import os
import sys

# Add current directory to path
sys.path.append(os.getcwd())

from pipeline.ingest import EpiubLoader
from pipeline.output import JSONFormatter

def safe_print(s):
    try:
        print(s.encode('utf-8', 'ignore').decode('utf-8'))
    except:
        print(repr(s))

def analyze_epub(path):
    print(f"Analyzing: {path}")
    loader = EpiubLoader(path)
    loader.load()
    chapters = loader.get_chapters()
    
    book_structure = JSONFormatter.build_structure(chapters)
    

    with open('structure_report.txt', 'w', encoding='utf-8') as f:
        f.write("\n=== SAFE STRUCTURE OUTPUT ===\n")
        for item in book_structure:
            if item['_type'] == 'part':
                f.write(f"PART: {item['partTitle']}\n")
                for ch in item.get('chapters', []):
                    f.write(f"  CHAPTER: {ch['chapterTitle']}\n")
            elif item['_type'] == 'chapter':
                f.write(f"CHAPTER: {item['chapterTitle']}\n")
    print("Report generated: structure_report.txt")

if __name__ == "__main__":
    epub_path = r"book\Carnegie, Dale - How to Win Friends and Influence People (2010, Simon & Schuster) - libgen.li.epub"
    if os.path.exists(epub_path):
        analyze_epub(epub_path)
    else:
        print("EPUB not found")
