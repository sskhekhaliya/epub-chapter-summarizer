
import json
import re

json_path = r"d:\Projects\Books Summary\output\atomic_habits_chapter_summaries.json"

def clean_json():
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        description = data.get("bookDescription", "")
        # The specific pattern seen in the user's file is:
        # "Here's a compelling, high-level book description suitable for a back-cover blurb:\n"
        
        # We can use a regex to be safe, or just split.
        pattern = re.compile(r"Here's a compelling, high-level book description suitable for a back-cover blurb:\s*", re.IGNORECASE)
        
        if pattern.match(description):
            print("Found unwanted preamble. Removing...")
            new_description = pattern.sub("", description)
            # Should also strip quotes if the LLM wrapped it in quotes
            new_description = new_description.strip().strip('"')
            data["bookDescription"] = new_description
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            print("Successfully updated JSON.")
        else:
            print("Preamble not found or already clean.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    clean_json()
