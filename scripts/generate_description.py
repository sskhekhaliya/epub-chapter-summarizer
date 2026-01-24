import json
import os
import sys
import argparse
# Add parent directory to sys.path to allow importing the pipeline package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline.summarizer import Summarizer
from pipeline.sanity_uploader import SanityUploader

def extract_text_from_portable_text(blocks):
    """Simple extractor for Sanity Portable Text to plain text."""
    text_parts = []
    if not isinstance(blocks, list):
        return ""
        
    for block in blocks:
        if block.get('_type') == 'block' and 'children' in block:
            for child in block['children']:
                if child.get('_type') == 'span' and 'text' in child:
                    text_parts.append(child['text'])
    return "\n\n".join(text_parts)

def main():
    parser = argparse.ArgumentParser(description="Generate Book Description for an existing JSON summary file.")
    parser.add_argument("json_file", help="Path to the JSON file in the output directory")
    parser.add_argument("--model-url", default="http://localhost:11434/v1", help="Base URL for the LLM API")
    parser.add_argument("--model-name", default="llama3", help="Name of the model to use")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.json_file):
        print(f"Error: File not found: {args.json_file}")
        sys.exit(1)
        
    print(f"Reading {args.json_file}...")
    with open(args.json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    if data.get('_type') != 'bookReview':
        print("Error: Invalid JSON format. Expected a 'bookReview' type.")
        sys.exit(1)
        
    # Check if description already exists and ask user or just proceed
    if data.get('bookDescription'):
        print(f"Warning: 'bookDescription' already exists. It will be overwritten.")

    # 1. Extract chapter summaries
    print("Extracting chapter summaries...")
    chapter_summaries = []
    
    # Traverse bookStructure
    for item in data.get('bookStructure', []):
        if item.get('_type') == 'chapter':
            text = extract_text_from_portable_text(item.get('chapterSummary', []))
            chapter_summaries.append({
                'title': item.get('chapterTitle'),
                'summary': text
            })
        elif item.get('_type') == 'part':
            for ch in item.get('chapters', []):
                text = extract_text_from_portable_text(ch.get('chapterSummary', []))
                chapter_summaries.append({
                    'title': ch.get('chapterTitle'),
                    'summary': text
                })
                
    if not chapter_summaries:
        print("Error: No chapter summaries found in the JSON file.")
        sys.exit(1)
        
    print(f"Found {len(chapter_summaries)} summaries.")

    # 2. Generate Description
    print(f"Generating overall description using {args.model_name}...")
    summarizer = Summarizer(model_url=args.model_url, model_name=args.model_name)
    description = summarizer.generate_book_description(chapter_summaries)
    
    if not description:
        print("Error: Failed to generate book description.")
        sys.exit(1)
        
    print("Description generated successfully.")
    data['bookDescription'] = description

    # 3. Save updated JSON
    print(f"Updating {args.json_file}...")
    with open(args.json_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    # 4. Re-upload to Sanity
    print("Uploading updated document to Sanity...")
    uploader = SanityUploader()
    if uploader.enabled:
        res = uploader.upload_book_review(data)
        if res:
            slug = data['slug']['current']
            uploader.create_update_log(data['title'], slug)
            print(f"Done! Updated summary of '{data['title']}' is live.")
    else:
        print("Sanity upload skipped (uploader disabled or no credentials).")

if __name__ == "__main__":
    main()
