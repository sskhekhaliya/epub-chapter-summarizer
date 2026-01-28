import json
import os
import sys

def inspect_json(path):
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return

    print(f"Inspecting: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    structure = data.get('bookStructure', [])
    print(f"Total Top-Level Items: {len(structure)}")
    
    for item in structure:
        if item.get('_type') == 'part':
            print(f"[PART] {item.get('partTitle')} (Contains {len(item.get('chapters', []))} chapters)")
            for ch in item.get('chapters', []):
                print(f"  - [CHAPTER] {ch.get('chapterTitle')}")
        else:
            print(f"[CHAPTER] {item.get('chapterTitle')}")

if __name__ == "__main__":
    output_dir = "output"
    files = [f for f in os.listdir(output_dir) if f.endswith('.json')]
    if files:
        # Sort by mtime
        files.sort(key=lambda x: os.path.getmtime(os.path.join(output_dir, x)), reverse=True)
        inspect_json(os.path.join(output_dir, files[0]))
    else:
        print("No JSON output found.")
