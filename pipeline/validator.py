
import ast

class OutputValidator:
    """
    Validates and cleans book summary data before final output/upload.
    """
    
    @staticmethod
    def clean_summary_phrases(data):
        """
        Recursively remove blocks starting with specific summary phrases using Regex.
        Matches patterns like:
        - "Here is a summary..."
        - "The author's voice is distinct... Here is a summary..."
        Returns the number of removed/modified blocks.
        """
        import re
        
        # Regex to catch "Here is a summary..." and preceding meta-talk
        # We look for lines containing "Here is/Here's a summary" or "attempt at summarizing" 
        # optionally preceded by sentences about "voice", "structure", "mimic".
        # We want to remove the *introductory portion*.
        
        # Strategy:
        # 1. Inspect text blocks.
        # 2. If a block starts with meta-talk, remove the meta-talk part.
        # 3. If the whole block is meta-talk, remove the block.

        # Patterns to identify meta-talk SENTENCES.
        # We will split text by newlines. If a paragraph (line) matches these patterns heavily, we drop it.
        
        bad_patterns = [
            r"here\s+is\s+(?:a|the)\s+summary",
            r"here's\s+(?:a|the)\s+summary",
            r"attempt\s+at\s+summarizing",
            r"summary\s+of\s+the\s+chapter",
            r"summary\s+that\s+captures",
            r"author's\s+voice\s+is",
            r"voice\s+and\s+sentence\s+structure",
            r"mimic\s+it",
            r"mimic\s+the",
            r"in\s+the\s+same\s+voice",
            r"here\s+it\s+is"
        ]
        
        combined_pattern = re.compile("|".join(bad_patterns), re.IGNORECASE)
        
        count = 0
        if isinstance(data, dict):
            keys = list(data.keys())
            for key in keys:
                value = data[key]
                # Target specific fields where this happens
                if key in ["chapterSummary", "partDescription"] and isinstance(value, list):
                    indices_to_remove = []
                    for i, block in enumerate(value):
                        if block.get("_type") == "block" and "children" in block:
                            # We might need to modify the children text IN PLACE
                            # or remove the block if it's empty after cleanup.
                            
                            new_children = []
                            block_modified = False
                            
                            for child in block["children"]:
                                if "text" in child:
                                    text = child["text"]
                                    # Check if the text matches our bad patterns
                                    if combined_pattern.search(text):
                                        # It matches. Now does it match specific lines?
                                        lines = text.split('\n')
                                        valid_lines = []
                                        for line in lines:
                                            # If a line has a strong match, we skip it.
                                            # "Strong match" = contains "Here is..." OR contains "voice is..."
                                            if combined_pattern.search(line):
                                                # If it ends with a colon, it's definitely an intro.
                                                # If it's a short sentence about voice, it's meta.
                                                # Let's assume ANY line matching these specific keywords is meta-talk 
                                                # because they are not part of the book narrative.
                                                block_modified = True
                                                continue
                                            valid_lines.append(line)
                                        
                                        if block_modified:
                                            new_text = "\n".join(valid_lines).strip()
                                            if new_text:
                                                child["text"] = new_text
                                                new_children.append(child)
                                            else:
                                                # Child became empty, don't add it
                                                pass
                                        else:
                                            new_children.append(child)
                                    else:
                                        new_children.append(child)
                                else:
                                    new_children.append(child)
                            
                            if block_modified:
                                count += 1
                                if not new_children:
                                    # Block is now empty
                                    indices_to_remove.append(i)
                                else:
                                    block["children"] = new_children

                    # Remove blocks that became empty
                    if indices_to_remove:
                        for i in sorted(indices_to_remove, reverse=True):
                            del value[i]
                else:
                    count += OutputValidator.clean_summary_phrases(value)
        elif isinstance(data, list):
            for item in data:
                count += OutputValidator.clean_summary_phrases(item)
        return count

    @staticmethod
    def clean_highlights(data):
        """
        Parses, cleans, and filters highlightsAndNotes.
        Returns the number of modified (fixed or removed) highlights.
        """
        if "highlightsAndNotes" not in data:
            return 0

        highlights = data["highlightsAndNotes"]
        original_len = len(highlights)
        
        # Priority keys for extraction
        target_keys = ["quote", "key takeaway", "insight", "text", "Text", "highlight"]
        
        cleaned_highlights = []
        modified_count = 0
        
        import re
        
        for item in highlights:
            text_value = item
            was_complex = False

            # 1. Handle stringified dicts
            if isinstance(item, str):
                item_stripped = item.strip()
                if item_stripped.startswith("{") and item_stripped.endswith("}"):
                    try:
                        parsed = ast.literal_eval(item_stripped)
                        if isinstance(parsed, dict):
                            # Find the first matching key
                            extracted = None
                            for key in target_keys:
                                if key in parsed and parsed[key]:
                                    extracted = str(parsed[key])
                                    break
                            
                            if extracted:
                                text_value = extracted
                                was_complex = True
                            else:
                                # Dictionary but no valid text (e.g. empty quote) -> Mark for skip
                                text_value = ""
                                was_complex = True
                    except Exception:
                        pass # Treat as normal string if parse fails

            # 2. Filter Junk
            # Ensure text_value is string
            if not isinstance(text_value, str):
                text_value = str(text_value)
            
            text_value = text_value.strip()
            
            # Filtering Rules
            if not text_value:
                modified_count += 1
                continue # Skip empty
                
            # Skip numbers (e.g. "-1.0", "1", "1.0")
            # Regex for float/int
            if re.match(r'^-?\d+(\.\d+)?$', text_value):
                modified_count += 1
                continue
                
            # Skip references like "[1]", "[12]"
            if re.match(r'^\[\d+\]$', text_value):
                modified_count += 1
                continue
            
            if was_complex or text_value != item:
                 modified_count += 1
                 
            cleaned_highlights.append(text_value)
            
        # Update the list in place (or replace content)
        # We need to replace the contents of the original list object if possible
        # or update the dictionary reference.
        # Since 'highlights' is a reference to data["highlightsAndNotes"], modifying it *in place* works via slice assignment
        # providing it's a list.
        
        if len(cleaned_highlights) != original_len:
             modified_count += (original_len - len(cleaned_highlights))

        data["highlightsAndNotes"][:] = cleaned_highlights
        
        return modified_count

    @staticmethod
    def clean_description(data):
        """
        Removes introductory phrases from the book description.
        Returns 1 if modified, 0 otherwise.
        """
        if "bookDescription" not in data or not isinstance(data["bookDescription"], str):
            return 0
            
        desc = data["bookDescription"]
        
        # Phrases specifically for descriptions
        bad_starts = [
            "here is a compelling book description",
            "here is a book description",
            "here is a summary",
            "here is a description",
            "sure, here",
            "compelling book description suitable for"
        ]
        
        # Simple check for the specific pattern seen
        # "Here is a compelling book description suitable for a back-cover summary:\n\n"
        
        lower_desc = desc.lower().strip()
        
        for bad in bad_starts:
            if lower_desc.startswith(bad):
                # Try to find the first double newline or colon
                # Usually it's "Here is ... summary:\n\nActual content"
                
                # Split by newline
                lines = desc.split('\n')
                start_idx = 0
                
                # Skip the first line if it contains the bad phrase
                if lines[0].lower().startswith(bad):
                    start_idx = 1
                    # Skip empty lines after valid removal
                    while start_idx < len(lines) and not lines[start_idx].strip():
                        start_idx += 1
                        
                    if start_idx < len(lines):
                        data["bookDescription"] = "\n".join(lines[start_idx:]).strip()
                        return 1
                        
        return 0

    @staticmethod
    def validate_and_clean(data):
        """
        Runs all cleanup tasks on the data object.
        Returns (is_clean, cleaned_data) - though data is modified in place.
        """
        phrases_removed = OutputValidator.clean_summary_phrases(data)
        highlights_fixed = OutputValidator.clean_highlights(data)
        description_cleaned = OutputValidator.clean_description(data)
        
        was_modified = phrases_removed > 0 or highlights_fixed > 0 or description_cleaned > 0
        if was_modified:
            print(f"  [Validator] Cleanup performed: Removed {phrases_removed} summary phrases, Fixed {highlights_fixed} highlights, Cleaned description: {description_cleaned}.")
            
        return was_modified, data
