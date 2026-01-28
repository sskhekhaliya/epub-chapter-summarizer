"""Check the output JSON for chapter content lengths."""
import json

with open('output/mans_search_for_meaning_chapter_summaries.json', encoding='utf-8') as f:
    data = json.load(f)

print("=" * 80)
print("Chapter Summary Status in Output File:")
print("=" * 80)

total_chapters = 0
completed_chapters = 0

for item in data.get('bookStructure', []):
    if item.get('_type') == 'chapter':
        total_chapters += 1
        title = item.get('chapterTitle', 'Unknown')
        summary = item.get('chapterSummary', [])
        
        # Extract text from portable text format
        text = ""
        for block in summary:
            if block.get('_type') == 'block':
                for child in block.get('children', []):
                    if child.get('_type') == 'span':
                        text += child.get('text', '')
        
        text_len = len(text)
        
        # Determine status
        if not summary or len(summary) == 0:
            status = "[PENDING]"
        elif "Please provide" in text or "chapter text" in text.lower():
            status = "[PLACEHOLDER]"
        else:
            status = "[OK]"
            completed_chapters += 1
        
        print(f"{status:15} {title:<50} | {text_len:>5} chars")
        
        # Print preview for main chapters (I:, II:) or if there's content
        if ("I:" in title or "II:" in title) and text_len > 0:
            preview = text[:200].replace('\n', ' ')
            print(f"               Preview: {preview}...")
            print()

print("=" * 80)
print(f"Summary: {completed_chapters}/{total_chapters} chapters completed")
