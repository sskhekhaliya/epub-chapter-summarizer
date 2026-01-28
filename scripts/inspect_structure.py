
import os
import sys

# Add current directory to path so we can import from pipeline
sys.path.append(os.getcwd())

from pipeline.ingest import EpiubLoader
from pipeline.output import JSONFormatter

def analyze_epub(path):
    print(f"Analyzing: {path}")
    loader = EpiubLoader(path)
    loader.load()
    chapters = loader.get_chapters()
    
    print(f"\n=== RAW TOC Structure ===")
    print(f"Total sections: {len(chapters)}")
    for i, ch in enumerate(chapters[:10]): # Show first 10 only to save space
         title = ch.get('title', 'Unknown')
         level = ch.get('level', 0)
         is_parent = ch.get('is_parent', False)
         indent = "  " * level
         print(f"{indent}L{level}: {title} (Parent: {is_parent})")
    print("... (rest of raw structure omitted) ...\n")

    print(f"=== DETECTED HIERARCHY (Output Logic) ===")
    # Use the shared logic from output.py
    book_structure = JSONFormatter.build_structure(chapters)
    
    for item in book_structure:
        if item['_type'] == 'part':
            print(f"PART: {item['partTitle']}")
            for ch in item.get('chapters', []):
                print(f"  CHAPTER: {ch['chapterTitle']}")
        elif item['_type'] == 'chapter':
            print(f"CHAPTER: {item['chapterTitle']}")
         

if __name__ == "__main__":
    import argparse
    # Default fallback
    default_file_path = r"d:\Projects\Books Summary\book\Eric Jorgenson - The Almanack of Naval Ravikant_ A Guide to Wealth and Happiness (2020, Magrathea Publishing) - libgen.li.epub"
    
    parser = argparse.ArgumentParser(description="Inspect EPUB structure.")
    parser.add_argument("file", nargs="?", default=default_file_path, help="Path to EPUB file.")
    args = parser.parse_args()
    
    if os.path.exists(args.file):
        analyze_epub(args.file)
    elif os.path.exists(default_file_path):
         # Just use default if arg provided but not found? No, better warn.
         print(f"File not found: {args.file}")
    else:
        # Search for any epub in book/
        import glob
        epubs = glob.glob("book/*.epub")
        if epubs:
            print(f"Using found epub: {epubs[0]}")
            analyze_epub(epubs[0])
        else:
            print("No EPUB file found to analyze.")
