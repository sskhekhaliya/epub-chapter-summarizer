
import argparse
import os
import sys
import json
import difflib

# Ensure we can import from pipeline
sys.path.append(os.getcwd())

from pipeline.sanity_uploader import SanityUploader
from pipeline.ingest import EpiubLoader

def find_matching_epub(book_dir, book_title):
    if not os.path.exists(book_dir):
        return None
        
    epubs = [f for f in os.listdir(book_dir) if f.lower().endswith('.epub')]
    if not epubs:
        return None
        
    # If only one, assume it's the one
    if len(epubs) == 1:
        return os.path.join(book_dir, epubs[0])

    # If multiple, try to match title
    best_match = None
    best_ratio = 0.0
    
    print("  - Multiple EPUBs found. Searching for match...")
    for epub in epubs:
        path = os.path.join(book_dir, epub)
        try:
            loader = EpiubLoader(path)
            loader.load() 
            meta = loader.get_metadata()
            epub_title = meta.get('title', '')
            
            ratio = difflib.SequenceMatcher(None, book_title.lower(), epub_title.lower()).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_match = path
        except:
            continue
            
    if best_match and best_ratio > 0.5:
        return best_match
        
    # Fallback: fuzzy match filename?
    return os.path.join(book_dir, epubs[0]) # Default to first if all else fails

def main():
    parser = argparse.ArgumentParser(description="Upload JSON Summary and Cover to Sanity")
    parser.add_argument("json_path", help="Path to the output JSON summary file")
    args = parser.parse_args()

    json_path = args.json_path
    
    if not os.path.exists(json_path):
        print(f"Error: JSON file not found at {json_path}")
        sys.exit(1)

    print(f"Loading {json_path}...")
    with open(json_path, "r", encoding="utf-8") as f:
        final_json_data = json.load(f)

    print("Step 7: Uploading to Sanity (Manual Run)...")
    uploader = SanityUploader()
    if uploader.enabled and final_json_data:
        # Determine Cover Image (Local vs EPUB)
        cover_bytes = None
        cover_mimetype = "image/jpeg"
        
        slug = final_json_data.get('slug', {}).get('current')
        title = final_json_data.get('title')
        
        if not slug:
            print("Error: JSON missing slug.")
            return

        # 1. Check Local Images in book/ folder
        book_dir_local = "book" 
        local_cover_found = False
        valid_exts = ['.jpg', '.jpeg', '.png', '.webp']
        
        if os.path.exists(book_dir_local):
            # A. Look for slug.jpg, slug.png, etc.
            for ext in valid_exts:
                local_path = os.path.join(book_dir_local, f"{slug}{ext}")
                if os.path.exists(local_path):
                    print(f"  - Found local thumbnail matching slug: {local_path}")
                    with open(local_path, 'rb') as f:
                        cover_bytes = f.read()
                    if ext == '.png': cover_mimetype = "image/png"
                    elif ext == '.webp': cover_mimetype = "image/webp"
                    local_cover_found = True
                    break
            
            # B. If not found by slug, look for ANY image file in that folder (if only one present?)
            if not local_cover_found:
                 # Logic similar to main.py
                 pass
        
        # 2. Extract from EPUB if no local cover
        if not local_cover_found:
            epub_path = find_matching_epub(book_dir_local, title)
            if epub_path:
                print(f"  - Attempting to extract cover from EPUB: {epub_path}")
                try:
                    loader = EpiubLoader(epub_path)
                    loader.load() # We need to load it to get the cover
                    cover_data = loader.get_cover()
                    
                    if isinstance(cover_data, tuple) and len(cover_data) == 2:
                        c_bytes, c_mime = cover_data
                        if c_bytes:
                            cover_bytes = c_bytes
                            cover_mimetype = c_mime
                            print(f"  - extracted cover from EPUB ({len(cover_bytes)} bytes).")
                            local_cover_found = True
                        else:
                            print("  - No cover found inside EPUB.")
                except Exception as e:
                    print(f"  - Error processing EPUB: {e}")
            else:
                 print("  - No valid EPUB found to extract cover from.")

        if cover_bytes:
            print(f"  - Uploading cover image to Sanity...")
            asset_doc = uploader.upload_image_asset(cover_bytes, mimetype=cover_mimetype)
            if asset_doc:
                print(f"  - Cover uploaded successfully: {asset_doc['_id']}")
                final_json_data['coverImage'] = {
                    "_type": "image",
                    "asset": {
                        "_type": "reference",
                        "_ref": asset_doc['_id']
                    }
                }
            else:
                print("  - Failed to upload cover image.")
        else:
             print("  - No cover image found (Skipping cover upload).")

        # Upload Book Review
        doc_id = f"book-review-{slug}"
        final_json_data['_id'] = doc_id
        
        res = uploader.upload_book_review(final_json_data)
        
        if res:
            # Create Log
            uploader.create_update_log(final_json_data['title'], slug)
            print(f"Done! Summary of '{final_json_data['title']}' is live.")
    else:
        print("Sanity Uploader not enabled or no data.")

if __name__ == "__main__":
    main()
