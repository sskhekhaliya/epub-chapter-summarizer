
import json
import os
import glob

def clear_part_summaries():
    # Find all json files in output/
    files = glob.glob(os.path.join("output", "*_chapter_summaries.json"))
    
    for file_path in files:
        print(f"Processing {file_path}...")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            modified = False
            
            # Iterate structure
            # The structure might be nested or flat depending on how it's saved?
            # main.py saves 'bookStructure' which is flat-ish but might contain nested chapters?
            # Let's check 'bookStructure' list.
            
            if 'bookStructure' in data:
                for item in data['bookStructure']:
                    if item.get('_type') == 'part':
                        # Clear summary
                        if item.get('chapterSummary'):
                            print(f"  - Clearing summary for Part: {item.get('partTitle', 'Unknown')}")
                            item['chapterSummary'] = [] 
                            modified = True
                        
                        # Also check if chapters are nested inside?
                        # In the output JSON, typically Parts contain 'chapters' list?
                        # inspect_structure output showed nesting.
                        # json_formatter.py usually nests.
                        
                        if 'chapters' in item:
                            # We DON'T want to clear valid chapter summaries, only the Part itself.
                            pass
                            
            if modified:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                print("  - Saved changes.")
            else:
                print("  - No Part summaries found to clear.")
                
        except Exception as e:
            print(f"Error processing {file_path}: {e}")

if __name__ == "__main__":
    clear_part_summaries()
