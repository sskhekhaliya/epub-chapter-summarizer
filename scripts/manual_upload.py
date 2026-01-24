
import os
import sys
import json

# Ensure we can import from pipeline
sys.path.append(os.getcwd())

from pipeline.sanity_uploader import SanityUploader

def main():
    json_path = r"d:\Projects\Books Summary\output\breaking_the_cycle_chapter_summaries.json"
    
    if not os.path.exists(json_path):
        print(f"Error: JSON file not found at {json_path}")
        return

    print(f"Loading {json_path}...")
    with open(json_path, "r", encoding="utf-8") as f:
        final_json_data = json.load(f)

    print("Step 7: Uploading to Sanity (Manual Run)...")
    uploader = SanityUploader()
    if uploader.enabled and final_json_data:
        # Determine Cover Image (Local vs EPUB)
        cover_bytes = None
        cover_mimetype = "image/jpeg"
        
        # Check the same directory as the EPUB file (book folder)
        # We assume the input path was likely "book/something.epub" originally,
        # so we check "book/" for images.
        slug = final_json_data['slug']['current']
        book_dir_local = "book" 
        local_cover_found = False
        valid_exts = ['.jpg', '.jpeg', '.png', '.webp']
        
        if os.path.exists(book_dir_local):
            # 1. Look for slug.jpg, slug.png, etc.
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
            
            # 2. If not found by slug, look for ANY image file in that folder if it seems unique enough
            # But let's stick to the slug match or just whatever image is there if only one.
            if not local_cover_found:
                images = [f for f in os.listdir(book_dir_local) if os.path.splitext(f)[1].lower() in valid_exts]
                # Filter out those that might belong to other books? Assuming book folder has multiple epubs, this is risky.
                # Use strict logic: only if the image name contains the slug or something.
                # Or just grab the first one if we assume single-book mode.
                pass 
        
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
             print("  - No local cover image found (skipped EPUB extraction for manual run).")

        # Upload Book Review
        slug = final_json_data['slug']['current']
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
