"""Test script to check if blank page handling works."""
import os
import sys
import io
import warnings
warnings.filterwarnings("ignore")

# Capture stdout during ingestion
from pipeline.ingest import EpiubLoader
from pipeline.cleaner import CleanText

# Find the EPUB file
book_dir = "book"
epubs = [f for f in os.listdir(book_dir) if f.lower().endswith(".epub")]
if not epubs:
    print("No EPUB files found")
    exit(1)

input_path = os.path.join(book_dir, epubs[0])

# Capture debug output during loading
old_stdout = sys.stdout
sys.stdout = captured = io.StringIO()

# Load the book
loader = EpiubLoader(input_path)
loader.load()

# Get chapters
chapters = loader.get_chapters()

# Restore stdout
sys.stdout = old_stdout

# Get captured debug output
debug_output = captured.getvalue()

# Now print results
cleaner = CleanText()

print(f"Testing with: {input_path}")
print(f"Book: {loader.get_metadata().get('title')}")
print("=" * 80)
print(f"\nTotal chapters found: {len(chapters)}")

# Print any merge messages from debug output
merge_messages = [line for line in debug_output.split('\n') if 'Merged' in line]
if merge_messages:
    print(f"\n[BLANK PAGE MERGES DETECTED]:")
    for msg in merge_messages:
        print(f"  {msg.strip()}")
print()

# Check specific chapters that might have blank pages
for i, ch in enumerate(chapters):
    title = ch['title']
    content = ch.get('content', '')
    cleaned = cleaner.clean(content)
    content_len = len(cleaned)
    
    # Print all chapters briefly
    print(f"{i+1:2}. {title:<50} | {content_len:>6} chars")
    
    # Print more details for "I:" or "II:" chapters
    if title.startswith("I:") or title.startswith("II:"):
        preview = cleaned[:300].replace('\n', ' ')
        print(f"     Preview: {preview}...")
        print()
