import os
import sys
import argparse
import re
# Add parent directory to sys.path to allow importing the pipeline package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline.ingest import EpiubLoader
from pipeline.cleaner import CleanText
from pipeline.segmenter import Segmenter
from pipeline.summarizer import Summarizer
from pipeline.sanity_uploader import SanityUploader

def main():
    parser = argparse.ArgumentParser(description="Extract highlights from EPUB and update Sanity.")
    parser.add_argument("slug", help="Slug of the book in Sanity (e.g., siddhartha-a-new-directions-paperback)")
    parser.add_argument("--model-url", default="http://localhost:11434/v1", help="Base URL for the LLM API")
    parser.add_argument("--model-name", default="llama3", help="Name of the model to use")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of chapters to process")
    
    args = parser.parse_args()
    
    # 1. Find the EPUB file
    book_dir = "book"
    if not os.path.exists(book_dir):
        print(f"Error: '{book_dir}' folder not found.")
        sys.exit(1)
        
    epubs = [f for f in os.listdir(book_dir) if f.lower().endswith(".epub")]
    if not epubs:
        print(f"No EPUB files found in '{book_dir}' folder.")
        sys.exit(1)
        
    # Heuristic: Try to find an EPUB that matches the slug
    input_path = None
    slug_parts = set(args.slug.split('-'))
    
    best_match = None
    max_overlap = 0
    
    for epub in epubs:
        epub_parts = set(re.split(r'[^a-zA-Z0-9]', epub.lower()))
        overlap = len(slug_parts.intersection(epub_parts))
        if overlap > max_overlap:
            max_overlap = overlap
            best_match = epub
            
    if best_match:
        input_path = os.path.join(book_dir, best_match)
        print(f"Found matching EPUB: {input_path}")
    else:
        # Fallback to the first one if no clear match
        input_path = os.path.join(book_dir, epubs[0])
        print(f"Using first available EPUB: {input_path}")

    # 2. Extract Highlights
    print(f"Step 1: Ingesting EPUB...")
    loader = EpiubLoader(input_path)
    try:
        loader.load()
    except Exception as e:
        print(f"Critical Error loading EPUB: {e}")
        sys.exit(1)
        
    raw_chapters = loader.get_chapters()
    cleaner = CleanText()
    segmenter = Segmenter()
    
    cleaned_chapters = []
    for ch in raw_chapters:
        text = cleaner.clean(ch['content'])
        if text:
            ch['content'] = text
            cleaned_chapters.append(ch)
            
    final_chapters = segmenter.segment(cleaned_chapters)
    
    if args.limit:
        print(f"Limiting to first {args.limit} chapters.")
        final_chapters = final_chapters[:args.limit]
        
    print(f"Step 2: Extracting highlights with {args.model_name}...")
    summarizer = Summarizer(model_url=args.model_url, model_name=args.model_name)
    
    all_highlights = []
    for i, ch in enumerate(final_chapters):
        print(f"  - Extracting Highlights for Chapter {i+1}: {ch['title']}")
        highlights = summarizer.extract_highlights(ch['content'])
        if highlights:
            all_highlights.extend(highlights)
            
    if not all_highlights:
        print("No highlights extracted.")
        sys.exit(0)
        
    print(f"Total highlights extracted: {len(all_highlights)}")

    # 3. Update Sanity
    print(f"Step 3: Connecting to Sanity...")
    uploader = SanityUploader()
    if not uploader.enabled:
        print("Error: Sanity uploader is not enabled.")
        sys.exit(1)

    print(f"Searching for book with slug: {args.slug}...")
    doc = uploader.get_document_by_slug(args.slug)
    
    if not doc:
        print(f"Error: Could not find document with slug '{args.slug}' in Sanity.")
        sys.exit(1)
        
    doc_id = doc['_id']
    print(f"Found document: {doc.get('title')} (ID: {doc_id})")
    
    print(f"Updating highlightsAndNotes field...")
    res = uploader.patch_document(doc_id, {"highlightsAndNotes": all_highlights})
    
    if res:
        print(f"Successfully updated highlights for '{doc.get('title')}'!")
        uploader.create_update_log(
            doc.get('title'), 
            args.slug, 
            log_title=f"Updated highlights: {doc.get('title')}",
            log_message=f"Re-extracted and updated highlights for {doc.get('title')}.",
            log_type="HIGHLIGHTS_UPDATE"
        )
        
        # 4. Sync with Local JSON
        print(f"Step 4: Syncing with local JSON file...")
        output_dir = "output"
        if os.path.exists(output_dir):
            # Look for a JSON file that matches the slug
            json_files = [f for f in os.listdir(output_dir) if f.lower().endswith(".json")]
            target_json = None
            for jf in json_files:
                if args.slug.replace('-', '_') in jf.lower().replace('-', '_'):
                    target_json = jf
                    break
            
            if target_json:
                json_path = os.path.join(output_dir, target_json)
                try:
                    import json
                    with open(json_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    data['highlightsAndNotes'] = all_highlights
                    
                    with open(json_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                    print(f"  - Successfully updated local JSON: {json_path}")
                except Exception as e:
                    print(f"  - Warning: Failed to update local JSON: {e}")
            else:
                print(f"  - No matching local JSON found in '{output_dir}' to sync.")
    else:
        print("Failed to update highlights.")

if __name__ == "__main__":
    main()
