import json
import os
import sys

# Mocking the load_existing_progress behavior
def extract_text_from_portable_text(blocks):
    return "some text"

def load_existing_progress(output_path):
    if not os.path.exists(output_path):
        return {}, "", None, None, []
    try:
        with open(output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            summaries = {}
            for item in data.get('bookStructure', []):
                if item.get('_type') == 'chapter':
                    summaries[item.get('chapterTitle')] = "summary"
                elif item.get('_type') == 'part':
                    for ch_item in item.get('chapters', []):
                        summaries[ch_item.get('chapterTitle')] = "summary"
            
            rating = data.get('yourRating')
            affiliate_link = data.get('affiliateLink')
            existing_highlights = data.get('highlightsAndNotes', [])
            
            return summaries, data.get('bookDescription', ""), rating, affiliate_link, existing_highlights
    except Exception as e:
        print(f"Error: {e}")
        return {}, "", None, None, []

output_path = 'output/breaking_the_cycle_chapter_summaries.json'
res = load_existing_progress(output_path)
print(f"Summaries: {len(res[0])}")
print(f"Rating: {res[2]}")
print(f"Link: {res[3]}")
