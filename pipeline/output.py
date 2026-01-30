import json
import uuid
import re
from datetime import date
from .utils import text_to_portable_text, has_meaningful_content

class JSONFormatter:
    @staticmethod
    def is_part(title, level=0, is_parent=False, semantic_type=None):
        """Heuristic to determine if a section is a Part or a Chapter."""
        # 0. Semantic EPUB detection (Best Force)
        if semantic_type:
            sem = semantic_type.lower()
            if 'part' in sem or 'division' in sem or 'volume' in sem or 'group' in sem:
                return True
        
        # 1. Structural indicator (Primary)
        # If the EPUB loader detected this is a parent container in the TOC, it's a Part.
        if is_parent:
            return True
        
        # 2. Title pattern detection for "Part I:", "Part II:", "Part One:", etc.
        if title:
            # Match patterns like: "Part I:", "Part II:", "Part 1:", "Part One:", etc.
            part_pattern = r'^Part\s+(?:[IVX]+|[0-9]+|One|Two|Three|Four|Five|Six|Seven|Eight|Nine|Ten)\s*[:\-]?\s*'
            if re.match(part_pattern, title, re.IGNORECASE):
                return True
            
        return False

    @staticmethod
    def build_structure(chapters):
        """
        Builds a 2-level book hierarchy (Part → Chapters) from flat chapter list.
        
        Logic based on depth:
        - Find items that are "Part candidates" (their children are leaves/deepest level)
        - Those become Parts, their children become Chapters
        - Everything above them becomes standalone Chapters
        """
        if not chapters:
            return []
        
        # Step 1: Analyze the structure to find which items should be Parts
        # An item is a Part if:
        # - It has children (is_parent=True)
        # - Its children do NOT have children (children are leaves)
        # - There's no sibling with is_parent=True that also has leaf children
        
        part_indices = set()
        
        for i, ch in enumerate(chapters):
            if not ch.get('is_parent', False):
                continue
            
            current_level = ch.get('level', 1)
            
            # Check if this item has actual children (items at level + 1)
            # AND those children are leaves (not parents themselves)
            has_direct_children = False
            all_children_are_leaves = True
            
            j = i + 1
            while j < len(chapters):
                next_ch = chapters[j]
                next_level = next_ch.get('level', 1)
                
                # Stop if we've moved back to same or higher level
                if next_level <= current_level:
                    break
                
                # If this is a direct child (level + 1)
                if next_level == current_level + 1:
                    has_direct_children = True
                    # If this child is also a parent, then our item is NOT a Part
                    if next_ch.get('is_parent', False):
                        all_children_are_leaves = False
                        break
                
                j += 1
            
            # Item is a Part if it has direct children AND all are leaves
            if has_direct_children and all_children_are_leaves:
                part_indices.add(i)
        
        # Step 2: Build the structure
        book_structure = []
        current_part = None
        current_part_level = None
        
        for i, ch in enumerate(chapters):
            title = ch.get('title', 'Untitled')
            summary_text = ch.get('summary', '')
            level = ch.get('level', 1)
            
            # Reset current_part if we're back to same or higher level than the part
            if current_part and current_part_level is not None and level <= current_part_level:
                current_part = None
                current_part_level = None
            
            if i in part_indices:
                # This item becomes a Part
                # Get the raw content to check if it has meaningful text
                raw_content = ch.get('content', '')
                
                current_part = {
                    "_type": "part",
                    "_key": str(uuid.uuid4()),
                    "partTitle": title,
                    "chapters": []
                }
                
                # Only add partDescription if the part has meaningful content (not just a heading)
                if has_meaningful_content(raw_content):
                    current_part["partDescription"] = text_to_portable_text(summary_text)
                
                current_part_level = level
                book_structure.append(current_part)
                
            elif current_part and level > current_part_level:
                # This is a child of the current Part → becomes a Chapter under Part
                chapter_obj = {
                    "_type": "chapter",
                    "_key": str(uuid.uuid4()),
                    "chapterTitle": title,
                    "chapterSummary": text_to_portable_text(summary_text)
                }
                current_part['chapters'].append(chapter_obj)
                
            else:
                # Standalone chapter (not under any Part)
                chapter_obj = {
                    "_type": "chapter",
                    "_key": str(uuid.uuid4()),
                    "chapterTitle": title,
                    "chapterSummary": text_to_portable_text(summary_text)
                }
                book_structure.append(chapter_obj)
        
        return book_structure


    @staticmethod
    def save(metadata, chapters, output_path, book_description=None, rating=0, affiliate_link=None):
        """
        Saves the summarized book data to a JSON file matching the Sanity schema.
        Supports 3-level hierarchy: Part → Chapter → Subchapter
        """
        
        # Build structure using extracted method
        book_structure = JSONFormatter.build_structure(chapters)

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
