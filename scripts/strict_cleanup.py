
import json
import os
import sys

# Ensure we can find the pipeline module
sys.path.append(os.getcwd())

from pipeline.validator import OutputValidator

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

    print("Checking for additional cleanup (junk highlights, etc.)...")
    was_modified, cleaned_data = OutputValidator.validate_and_clean(data)
    
    if was_modified:
        print("Corrections found.")
        
        # Create a backup
        backup_path = file_path + ".bak_final_cleanup"
        import shutil
        shutil.copy2(file_path, backup_path)
        print(f"Backup created at {backup_path}")

        # Save changes
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(cleaned_data, f, indent=2)
        print("Successfully saved cleaned JSON with strict filtering.")
    else:
        print("No additional cleanup needed.")

if __name__ == "__main__":
    main()
