import re

class Segmenter:
    # Patterns to detect if a title represents a new chapter or part
    CHAPTER_PATTERN = re.compile(
        r'^(Chapter|Part|Section|Book|Volume|Preface|Foreword|Introduction|Prologue|Epilogue|Afterword|Conclusion|Appendix)\s*[:\-]?\s*',
        re.IGNORECASE
    )
    # Roman numeral pattern for parts/chapters like "I:", "II:", "III:", etc.
    ROMAN_NUMERAL_PATTERN = re.compile(
        r'^[IVXLCDM]+\s*[:.\-]',
        re.IGNORECASE
    )
    # Numeric pattern for chapters starting with numbers like "1.", "1 -", "1 Title", etc.
    # Updated to allow:
    # 1. Digits followed by punctuation (:, ., -) with optional space
    # 2. Digits followed by at least one space (for "1 Title")
    NUMERIC_PATTERN = re.compile(
        r'^\d+(\s*[:.\-]|\s+)',
        re.IGNORECASE
    )
    
    def __init__(self):
        pass

    def _is_new_chapter_or_part(self, title):
        """Check if a title indicates a new chapter or part."""
        if not title:
            return False
        title_clean = title.strip()
        return (bool(self.CHAPTER_PATTERN.match(title_clean)) or 
                bool(self.ROMAN_NUMERAL_PATTERN.match(title_clean)) or 
                bool(self.NUMERIC_PATTERN.match(title_clean)))

    def segment(self, chapters):
        """
        Refines chapter segmentation by merging sequential markers with their content.
        Input: list of chapters [{'title', 'content', 'level', 'is_parent'}]
        Output: list of dicts {'title', 'content', ...}
        """
        if not chapters:
            return []

        merged = []
        skip_indices = set()

        for i in range(len(chapters)):
            if i in skip_indices:
                continue

            current = chapters[i].copy()
            current_content = current.get('content', '').strip()
            current_content_len = len(current_content)
            
            # Join sequential segments with the identical title or look ahead for content
            for look_ahead in range(1, 3):
                next_idx = i + look_ahead
                if next_idx >= len(chapters):
                    break
                
                next_ch = chapters[next_idx]
                
                # Case 1: Identical titles - reassemble split chapters/parts
                if next_ch['title'].lower() == current['title'].lower():
                    next_content = next_ch.get('content', '').strip()
                    
                    if current_content and next_content and current_content != next_content:
                        current['content'] = current_content + "\n\n" + next_content
                        current_content = current['content']  # Update for potential next merge
                    elif next_content:
                        current['content'] = next_content
                        current_content = next_content
                    
                    # Consolidate parent status
                    current['is_parent'] = current.get('is_parent', False) or next_ch.get('is_parent', False)
                    skip_indices.add(next_idx)
                    continue

                # Case 2: Current is effectively empty, look for near-match title
                if not current_content and look_ahead == 1:
                     # If next title contains current title or vice versa
                     curr_t = current['title'].lower()
                     next_t = next_ch['title'].lower()
                     if (curr_t in next_t or next_t in curr_t) and len(next_ch.get('content', '')) > 50:
                          current['title'] = next_ch['title']
                          current['content'] = next_ch['content']
                          current_content = current['content']
                          current['is_parent'] = current.get('is_parent', False) or next_ch.get('is_parent', False)
                          skip_indices.add(next_idx)
                          break
                
                # Case 3: Current chapter has blank/very little content (< 100 chars)
                # Look ahead and merge content from next items if they don't start a new chapter/part
                if current_content_len < 100:
                    next_title = next_ch.get('title', '').strip()
                    next_content = next_ch.get('content', '').strip()
                    
                    # Only merge if:
                    # 1. Next item is NOT a new chapter/part (based on title pattern)
                    # 2. Next item has content
                    # 3. Next item is not already in the skip list
                    if next_content and next_idx not in skip_indices:
                        if not self._is_new_chapter_or_part(next_title):
                            # This looks like continuation content, merge it
                            if current_content:
                                current['content'] = current_content + "\n\n" + next_content
                            else:
                                current['content'] = next_content
                            current_content = current['content']
                            current_content_len = len(current_content)
                            skip_indices.add(next_idx)
                            print(f"  - Merged blank page content: {current['title']} <- {next_title}")
                            continue

            merged.append(current)

        return merged
