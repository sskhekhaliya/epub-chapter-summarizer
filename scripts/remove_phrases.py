
import json
import os

def remove_summary_phrases(data):
    count = 0
    if isinstance(data, dict):
        keys = list(data.keys())
        for key in keys:
            value = data[key]
            if key == "chapterSummary" and isinstance(value, list):
                # Identify blocks to remove
                indices_to_remove = []
                for i, block in enumerate(value):
                    if block.get("_type") == "block" and "children" in block:
                        should_remove = False
                        for child in block["children"]:
                            if "text" in child:
                                text = child["text"].strip()
                                if text.lower().startswith("here is a summary"):
                                    should_remove = True
                                    break
                        if should_remove:
                            indices_to_remove.append(i)
                
                # Remove blocks in reverse order manually to avoid index shifting issues
                if indices_to_remove:
                    for i in sorted(indices_to_remove, reverse=True):
                        del value[i]
                        count += 1
            else:
                count += remove_summary_phrases(value)
    elif isinstance(data, list):
        for item in data:
            count += remove_summary_phrases(item)
    return count

def main():
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

    removed_count = remove_summary_phrases(data)

    if removed_count > 0:
        # Create a backup just in case
        backup_path = file_path + ".bak"
        import shutil
        shutil.copy2(file_path, backup_path)
        print(f"Backup created at {backup_path}")

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"Successfully removed {removed_count} blocks containing unwanted phrases.")
    else:
        print("No unwanted phrases found to remove.")

if __name__ == "__main__":
    main()
