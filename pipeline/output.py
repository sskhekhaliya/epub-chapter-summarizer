import json
import uuid
import re
from datetime import date
from .utils import text_to_portable_text

class JSONFormatter:
    @staticmethod
    def is_part(title, level=0, is_parent=False):
        """Heuristic to determine if a section is a Part or a Chapter."""
        # 1. Structural indicator (Strongest)
        if is_parent:
            return True
            
        # 2. Text-based detection (Fallback)
        # Match "Part 1", "Part I", "Section 1", "PART ONE", etc.
        # Allow optional colons or dashes after the number.
        part_pattern = r'^(Part|P\s*A\s*R\s*T|Section|Book)\s+([IVX0-9]+|\w+)(\s*[:\-\.])?'
        is_part_by_text = bool(re.match(part_pattern, title, re.IGNORECASE))
        
        # Heuristic: Treat as Part if structural level is explicitly 1 (often used for top-level titles)
        # BUT only if it's not a leaf node (is_parent would have caught it if it were a container)
        # Actually, if it's level 1, it might be a Part even without TOC children if the book is poorly structured.
        # We'll stick to text-based and is_parent as the primary drivers.
        return is_part_by_text

    @staticmethod
    def save(metadata, chapters, output_path, book_description=None, rating=0, affiliate_link=None):
        """
        Saves the summarized book data to a JSON file matching the Sanity schema.
        """
        
        # 2. Logic to build structure (Parts vs Chapters)
        book_structure = []
        current_part = None

        for ch in chapters:
            title = ch.get('title', 'Untitled')
            summary_text = ch.get('summary', '')
            
            # 1. Structural Detection (Primary)
            # Level 1 or h1-detected items are usually Parts
            # Level 2+ or h2/h3-detected items are usually Chapters
            level = ch.get('level', 0)
            
            # Use the static method for detection
            is_part = JSONFormatter.is_part(title, level, ch.get('is_parent', False))
            
            if is_part:
                # Create a new part object
                current_part = {
                    "_type": "part",
                    "_key": str(uuid.uuid4()),
                    "partTitle": title,
                    "partDescription": text_to_portable_text(summary_text),
                    "chapters": []
                }
                book_structure.append(current_part)
            else:
                # It's a chapter
                chapter_obj = {
                    "_type": "chapter",
                    "_key": str(uuid.uuid4()),
                    "chapterTitle": title,
                    "chapterSummary": text_to_portable_text(summary_text)
                }
                
                if current_part:
                    current_part['chapters'].append(chapter_obj)
                else:
                    # Top level chapter (e.g. Foreword)
                    book_structure.append(chapter_obj)

        # 3. Slugify title
        slug = metadata.get("title", "unknown").lower().replace(' ', '-')
        slug = re.sub(r'[^a-z0-9-]', '', slug) # Remove special chars

        # Default affiliate link logic if not provided
        if not affiliate_link:
            affiliate_link = f"https://www.amazon.com/s?k={metadata.get('title', '').replace(' ', '+')}&tag=sskhekhaliy06-21"

        # 4. Construct Final JSON
        all_highlights = []
        for ch in chapters:
            if 'highlights' in ch and ch['highlights']:
                all_highlights.extend(ch['highlights'])

        final_data = {
            "_type": "bookReview",
            "title": metadata.get("title", "Unknown"),
            "slug": {
                "_type": "slug",
                "current": slug
            },
            "author": metadata.get("author", "Unknown"),
            "bookDescription": book_description or "",
            "yourRating": float(rating),
            "affiliateLink": affiliate_link,
            "yourReview": [],
            "highlightsAndNotes": all_highlights,
            "bookStructure": book_structure
        }
            
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(final_data, f, indent=2, ensure_ascii=False)
            print(f"Successfully saved output to {output_path}")
        except Exception as e:
            print(f"Error saving JSON: {e}")
            
        return final_data
