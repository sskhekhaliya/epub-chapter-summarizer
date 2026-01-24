import argparse
import os
import sys
import json
from pipeline.ingest import EpiubLoader
from pipeline.cleaner import CleanText
from pipeline.segmenter import Segmenter
from pipeline.summarizer import Summarizer
from pipeline.output import JSONFormatter
from pipeline.sanity_uploader import SanityUploader
import threading
import time
import itertools

class Spinner:
    def __init__(self, message="Processing..."):
        self.message = message
        self.spinner = itertools.cycle(['-', '/', '|', '\\'])
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self._spin)

    def _spin(self):
        while not self.stop_event.is_set():
            sys.stdout.write(f"\r  {self.message} {next(self.spinner)}")
            sys.stdout.flush()
            time.sleep(0.1)
        sys.stdout.write("\r" + " " * (len(self.message) + 4) + "\r")
        sys.stdout.flush()

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop_event.set()
        self.thread.join()

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

def load_existing_progress(output_path):
    """Loads existing summaries and metadata from a JSON output file if it exists."""
    if not os.path.exists(output_path):
        return {}, "", None, None, []
    try:
        with open(output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            summaries = {}
            for item in data.get('bookStructure', []):
                if item.get('_type') == 'chapter':
                    summaries[item.get('chapterTitle')] = extract_text_from_portable_text(item.get('chapterSummary', []))
                elif item.get('_type') == 'part':
                    for ch_item in item.get('chapters', []):
                        summaries[ch_item.get('chapterTitle')] = extract_text_from_portable_text(ch_item.get('chapterSummary', []))
            
            # Extract existing meta info
            rating = data.get('yourRating')
            affiliate_link = data.get('affiliateLink')
            
            # Extract highlights per chapter if they exist in the structure
            # (Though we save them globally in highlightsAndNotes, we might also want per-chapter info if we change schema later)
            # For now, we'll try to find them in the global list if they were saved there.
            # But the user specifically asked for "highlightsAndNotes": [] list at the root.
            # Let's see if we can map them back to chapters for resume logic.
            existing_highlights = data.get('highlightsAndNotes', [])
            
            return summaries, data.get('bookDescription', ""), rating, affiliate_link, existing_highlights
    except Exception as e:
        print(f"Warning: Could not load existing progress: {e}")
        return {}, "", None, None, []

def main():
    parser = argparse.ArgumentParser(description="EPUB to Novel-Style Chapter Summaries JSON Pipeline")
    parser.add_argument("input_file", nargs="?", help="Path to the input EPUB file. If omitted, checks 'book' folder.")
    parser.add_argument("--output-dir", default="output", help="Directory to save the output JSON")
    parser.add_argument("--model-url", default="http://localhost:11434/v1", help="Base URL for the LLM API (e.g., Ollama)")
    parser.add_argument("--model-name", default="llama3", help="Name of the model to use")
    parser.add_argument("--limit", type=int, default=None, help="Limit the number of chapters to process (for testing)")
    parser.add_argument("--rating", type=float, default=None, help="Rating for the book (0-5)")
    parser.add_argument("--affiliate-link", default=None, help="Amazon affiliate link")
    parser.add_argument("--restart", action="store_true", help="Restart processing from scratch, ignoring existing progress")
    
    args = parser.parse_args()

    input_path = args.input_file
    
    # 1. Resolve Input File Early
    if not input_path:
        book_dir = "book"
        if not os.path.exists(book_dir):
            os.makedirs(book_dir)
            print(f"Created '{book_dir}' folder. Please place an EPUB file inside and run again.")
            sys.exit(0)
            
        epubs = [f for f in os.listdir(book_dir) if f.lower().endswith(".epub")]
        if not epubs:
            print(f"No EPUB files found in '{book_dir}' folder. Please add one.")
            sys.exit(1)
            
        input_path = os.path.join(book_dir, epubs[0])

    if not os.path.exists(input_path):
        print(f"Error: File not found: {input_path}")
        sys.exit(1)
        
    print(f"Processing: {input_path}")

    # 2. Ingest Metadata to determine Output Filename
    print("Step 1: Ingesting EPUB Metadata...")
    loader = EpiubLoader(input_path)
    try:
        loader.load()
    except Exception as e:
        print(f"Critical Error: {e}")
        sys.exit(1)
        
    metadata = loader.get_metadata()
    print(f"  - Title: {metadata.get('title')}")

    # 3. Determine output filename and check for existing progress
    book_title_clean = metadata.get('title', 'book').replace(' ', '_').lower()
    book_title_clean = "".join(c for c in book_title_clean if c.isalnum() or c in ('_', '-'))
    output_filename = f"{book_title_clean}_chapter_summaries.json"
    output_file_path = os.path.join(args.output_dir, output_filename)
    
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)

    existing_summaries, existing_description, existing_rating, existing_link, existing_highlights = load_existing_progress(output_file_path)

    # 4. Handle Resume/Restart Logic
    if existing_summaries and not args.restart:
        choice = input(f"Existing progress found for '{metadata.get('title')}'. Resume? (Y/n): ").strip().lower()
        if choice == 'n':
            print("  - Restarting from scratch (ignoring existing progress).")
            existing_summaries = {}
            existing_description = ""
            existing_rating = None
            existing_link = None
            existing_highlights = []
        else:
            print(f"  - Resuming: Skipping {len(existing_summaries)} previously summarized chapters.")
    elif args.restart:
        print("  - Restart flag detected: Starting from scratch.")
        existing_summaries = {}
        existing_description = ""
        existing_rating = None
        existing_link = None
        existing_highlights = []

    # 4. Handle Inputs (Prioritize CLI > Existing File > Interactive)
    rating = args.rating
    if rating is None:
        if existing_rating is not None:
            print(f"  - Using existing rating from {output_filename}: {existing_rating}")
            rating = existing_rating
        else:
            try:
                r_input = input("Enter your rating for this book (0-5, default 0): ").strip()
                if r_input:
                    rating = float(r_input)
                else:
                    rating = 0
            except ValueError:
                print("Invalid input. Defaulting rating to 0.")
                rating = 0
            
    affiliate_link = args.affiliate_link
    if affiliate_link is None:
        if existing_link:
            print(f"  - Using existing affiliate link from {output_filename}")
            affiliate_link = existing_link
        else:
            l_input = input("Enter Amazon Affiliate Link (press Enter to auto-generate): ").strip()
            if l_input:
                affiliate_link = l_input
            else:
                affiliate_link = None # Let JSONFormatter handle the default

    # 5. Full Ingest
    raw_chapters = loader.get_chapters()
    parts_count = sum(1 for ch in raw_chapters if JSONFormatter.is_part(ch.get('title', ''), ch.get('level', 0), ch.get('is_parent', False)))
    chapters_count = len(raw_chapters) - parts_count
    print(f"  - Found {len(raw_chapters)} sections ({parts_count} parts, {chapters_count} chapters).")
    
    # 6. Clean & 7. Segment
    print("Step 2 & 3: Cleaning and Segmenting...")
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
        print(f"  - Limiting to first {args.limit} chapters.")
        final_chapters = final_chapters[:args.limit]
        
    print(f"  - Processing {len(final_chapters)} valid chapters.")

    # 8. Resume Context
    book_description = existing_description

    # 9 & 10. Chunking & Summarization
    print(f"Step 4 & 5: Summarizing with {args.model_name}...")
    summarizer = Summarizer(model_url=args.model_url, model_name=args.model_name)
    
    for i, ch in enumerate(final_chapters):
        title = ch['title']
        if title in existing_summaries and existing_summaries[title].strip():
            print(f"  - Skipping Chapter {i+1}: {title} (Already summarized)")
            ch['summary'] = existing_summaries[title]
            # If we're resuming, we might still need to extract highlights if they're missing
            # For simplicity, we'll check if we have any highlights in the global list
            # If the user is resuming a half-finished book, we'll just re-extract for now 
            # or skip if we have enough. Let's just always extract if they're not there.
            if existing_highlights and i < len(existing_highlights):
                 ch['highlights'] = [existing_highlights[i]] # This is a weak mapping, but works if sequential
            else:
                 print(f"  - Extracting Highlights for Chapter {i+1}: {title}")
                 with Spinner("Analyzing highlights"):
                     ch['highlights'] = summarizer.extract_highlights(ch['content'])
        else:
            print(f"  - Summarizing Chapter {i+1}: {title}")
            with Spinner("Generating summary"):
                summary = summarizer.summarize_chapter(ch['content'])
            ch['summary'] = summary
            print(f"  - Extracting Highlights for Chapter {i+1}: {title}")
            with Spinner("Analyzing highlights"):
                ch['highlights'] = summarizer.extract_highlights(ch['content'])
        
        JSONFormatter.save(metadata, final_chapters, output_file_path, 
                           book_description=book_description, rating=rating, affiliate_link=affiliate_link)

    # 11. Finalize Description
    if not book_description:
        print("Step 5.5: Generating Overall Book Description...")
        with Spinner("Crafting book description"):
            book_description = summarizer.generate_book_description(final_chapters)
        if book_description:
            print("  - Book description generated successfully.")
            final_json_data = JSONFormatter.save(metadata, final_chapters, output_file_path, 
                                               book_description=book_description, rating=rating, affiliate_link=affiliate_link)
        else:
            print("  - Failed to generate book description.")
            final_json_data = JSONFormatter.save(metadata, final_chapters, output_file_path, 
                                               book_description=None, rating=rating, affiliate_link=affiliate_link)
    else:
        print("  - Book description already exists. Skipping generation.")
        final_json_data = JSONFormatter.save(metadata, final_chapters, output_file_path, 
                                           book_description=book_description, rating=rating, affiliate_link=affiliate_link)

    # 11.5 Final Validation & Cleanup
    print("Step 6: Validating and Cleaning Output...")
    from pipeline.validator import OutputValidator
    was_modified, final_json_data = OutputValidator.validate_and_clean(final_json_data)
    if was_modified:
        # Save the cleaned version back to disk
        final_json_data = JSONFormatter.save(metadata, final_chapters, output_file_path,
                                           book_description=book_description, rating=rating, affiliate_link=affiliate_link,
                                           # Note: JSONFormatter.save reconstructs the object from args.
                                           # If we simply modified final_json_data in place, we might be desynced from the args
                                           # passed to save(). Ideally, we should just dump final_json_data to disk directly here
                                           # to ensure our in-memory changes persist.
                                           )
        # Actually, JSONFormatter.save builds the structure from inputs. 
        # OutputValidator modified 'final_json_data' in place, but JSONFormatter.save re-creates it.
        # So we MUST perform the save using the *modified data object*, OR we just dump it directly.
        # Since 'final_chapters' and 'metadata' weren't explicitly modified by Validator (it modifies the dict),
        # but 'final_json_data' IS the dict.
        # A safer approach is to just write the cleaned dict to disk.
        with open(output_file_path, 'w', encoding='utf-8') as f:
             json.dump(final_json_data, f, indent=2)
        print(f"  - Cleaned output saved to {output_file_path}")

    # 12. Upload to Sanity
    print("Step 7: Uploading to Sanity...")
    uploader = SanityUploader()
    if uploader.enabled and final_json_data:
        # 12.1 Determine Cover Image (Local vs EPUB)
        cover_bytes = None
        cover_mimetype = "image/jpeg"
        
        # Check the same directory as the EPUB file
        slug = final_json_data['slug']['current']
        book_dir_local = os.path.dirname(input_path)
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
            
            # 2. If not found by slug, look for ANY image file in that folder
            if not local_cover_found:
                images = [f for f in os.listdir(book_dir_local) if os.path.splitext(f)[1].lower() in valid_exts]
                if images:
                    # If multiple, we just take the first one found
                    chosen_image = images[0]
                    local_path = os.path.join(book_dir_local, chosen_image)
                    print(f"  - Found local thumbnail (no slug match, using first image): {local_path}")
                    with open(local_path, 'rb') as f:
                        cover_bytes = f.read()
                    ext = os.path.splitext(chosen_image)[1].lower()
                    if ext == '.png': cover_mimetype = "image/png"
                    elif ext == '.webp': cover_mimetype = "image/webp"
                    local_cover_found = True
        
        if not local_cover_found:
            # Extract and upload cover image from EPUB if available
            cover_data = loader.get_cover()
            if isinstance(cover_data, tuple) and len(cover_data) == 2:
                cover_bytes, extracted_mimetype = cover_data
                if cover_bytes:
                    cover_mimetype = extracted_mimetype
                    print(f"  - Found cover image in EPUB ({len(cover_bytes)} bytes, {cover_mimetype}).")
                else:
                    print("  - No cover image found in EPUB.")
            else:
                print("  - No cover image found in EPUB or thumbnail folder.")

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

        # Upload Book Review
        slug = final_json_data['slug']['current']
        doc_id = f"book-review-{slug}"
        final_json_data['_id'] = doc_id
        
        res = uploader.upload_book_review(final_json_data)
        
        if res:
            # Create Log
            uploader.create_update_log(final_json_data['title'], slug)
            print(f"Done! Summary of '{final_json_data['title']}' is live.")

if __name__ == "__main__":
    main()
