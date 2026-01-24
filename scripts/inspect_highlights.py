
import json
import os
import ast

def inspect_highlights():
    file_path = r"d:\Projects\Books Summary\output\breaking_the_cycle_chapter_summaries.json"
    
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading JSON: {e}")
        return

    if "highlightsAndNotes" not in data:
        print("No highlightsAndNotes found.")
        return

    output_file = r"d:\Projects\Books Summary\highlights_report.txt"
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading JSON: {e}")
        return

    if "highlightsAndNotes" not in data:
        print("No highlightsAndNotes found.")
        return

    highlights = data["highlightsAndNotes"]

    # Collect output strings
    lines = []
    lines.append(f"Total highlights: {len(highlights)}")
    lines.append("-" * 40)

    stats = {
        "simple_string": 0,
        "dict_string": 0,
        "other": 0
    }
    
    dict_keys = set()

    for item in highlights:
        if not isinstance(item, str):
            stats["other"] += 1
            lines.append(f"Non-string item detected: {type(item)}")
            continue

        item = item.strip()
        if item.startswith("{") and item.endswith("}"):
            stats["dict_string"] += 1
            try:
                parsed = ast.literal_eval(item)
                if isinstance(parsed, dict):
                    dict_keys.update(parsed.keys())
                    lines.append(f"Parsed keys: {list(parsed.keys())} | Original: {item}")
            except Exception as e:
                lines.append(f"Failed to parse potential dict string: {item[:50]}... Error: {e}")
        else:
            stats["simple_string"] += 1

    lines.append("-" * 40)
    lines.append(f"Stats: {stats}")
    lines.append(f"All dictionary keys found: {sorted(list(dict_keys))}")
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Report written to {output_file}")

if __name__ == "__main__":
    inspect_highlights()
