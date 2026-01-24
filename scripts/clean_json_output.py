
import json
import os
import ast

def clean_summary_phrases(data):
    """
    Recursively remove blocks starting with specific summary phrases.
    Returns the number of removed blocks.
    """
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
                
                # Remove blocks in reverse order
                if indices_to_remove:
                    for i in sorted(indices_to_remove, reverse=True):
                        del value[i]
                        count += 1
            else:
                count += clean_summary_phrases(value)
    elif isinstance(data, list):
        for item in data:
            count += clean_summary_phrases(item)
    return count

def clean_highlights(data):
    """
    Parses and fixes stringified dictionaries in highlightsAndNotes.
    Returns the number of fixed highlights.
    """
    if "highlightsAndNotes" not in data:
        return 0

    highlights = data["highlightsAndNotes"]
    fixed_count = 0
    
    # Priority keys for extraction
    target_keys = ["quote", "key takeaway", "insight", "text", "Text"]
    
    for i, item in enumerate(highlights):
        if isinstance(item, str):
            item_stripped = item.strip()
            if item_stripped.startswith("{") and item_stripped.endswith("}"):
                try:
                    parsed = ast.literal_eval(item_stripped)
                    if isinstance(parsed, dict):
                        # Find the first matching key
                        extracted_text = None
                        for key in target_keys:
                            if key in parsed:
                                extracted_text = parsed[key]
                                break
                        
                        if extracted_text is not None:
                            highlights[i] = extracted_text
                            fixed_count += 1
                        else:
                            print(f"Warning: Could not extract text from dict highlight: {item_stripped}")
                except Exception as e:
                    print(f"Warning: Failed to parse highlight string: {item_stripped[:50]}... Error: {e}")

    return fixed_count

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

    print("Starting cleanup...")
    
    # Pass 1: Remove summary phrases
    removed_phrases = clean_summary_phrases(data)
    print(f"Removed {removed_phrases} summary phrase blocks.")

    # Pass 2: Clean highlights
    fixed_highlights = clean_highlights(data)
    print(f"Fixed {fixed_highlights} complex highlight strings.")

    if removed_phrases > 0 or fixed_highlights > 0:
        # Create a backup
        backup_path = file_path + ".bak_cleanup"
        import shutil
        shutil.copy2(file_path, backup_path)
        print(f"Backup created at {backup_path}")

        # Save changes
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print("Successfully saved cleaned JSON.")
    else:
        print("No changes needed.")

if __name__ == "__main__":
    main()
