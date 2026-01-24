
import json
import os

def main():
    file_path = r"d:\Projects\Books Summary\output\breaking_the_cycle_chapter_summaries.json"
    
    keywords = [
        "voice is distinct",
        "voice is distinctive",
        "mimic",
        "attempt at summarizing",
        "here is a summary",
        "here's a summary",
        "here is the summary",
        "summary of the chapter",
        "summary that captures"
    ]
    
    print(f"Scanning for keywords: {keywords}")
    
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    found_count = 0
    
    def scan_recursive(obj, path=""):
        nonlocal found_count
        if isinstance(obj, dict):
            for k, v in obj.items():
                scan_recursive(v, path + f".{k}")
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                scan_recursive(item, path + f"[{i}]")
        elif isinstance(obj, str):
            # Check for keywords
            lower_text = obj.lower()
            for kw in keywords:
                if kw in lower_text:
                    # Filter out short snippets if they are just the key itself (unlikely in this structure)
                    # Use a length check to avoid noise if needed, but for now print all.
                    print(f"MATCH ({kw}) in {path}:")
                    print(f"  {obj.strip()[:150]}...") 
                    print("-" * 20)
                    found_count += 1
                    break # One match per text block is enough to report

    scan_recursive(data)
    print(f"Total matches found: {found_count}")

if __name__ == "__main__":
    main()
