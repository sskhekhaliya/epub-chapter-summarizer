
import json
import os
from collections import Counter

def find_summary_phrases(data, phrases):
    if isinstance(data, dict):
        for key, value in data.items():
            if key == "chapterSummary" and isinstance(value, list):
                for block in value:
                    if block.get("_type") == "block" and "children" in block:
                        for child in block["children"]:
                            if "text" in child:
                                text = child["text"].strip()
                                if text.lower().startswith("here is a summary"):
                                    phrases.append(text)
            else:
                find_summary_phrases(value, phrases)
    elif isinstance(data, list):
        for item in data:
            find_summary_phrases(item, phrases)

def main():
    file_path = r"d:\Projects\Books Summary\output\breaking_the_cycle_chapter_summaries.json"
    output_file = r"d:\Projects\Books Summary\phrases_report.txt"
    
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading JSON: {e}")
        return

    phrases = []
    find_summary_phrases(data, phrases)

    result_lines = []
    result_lines.append(f"Total occurrences found: {len(phrases)}")
    result_lines.append("-" * 40)
    
    counts = Counter(phrases)
    for phrase, count in counts.most_common():
        result_lines.append(f"Count: {count} | Phrase: {phrase}")
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(result_lines))
    
    print(f"Report written to {output_file}")

if __name__ == "__main__":
    main()
