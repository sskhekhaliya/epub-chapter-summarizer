import ebooklib
from ebooklib import epub
import os
from .utils import should_skip_chapter

class EpiubLoader:
    def __init__(self, file_path):
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        if not file_path.lower().endswith(".epub"):
            raise ValueError("Invalid file format. Only EPUB is supported.")
        self.file_path = file_path
        self.book = None

    def load(self):
        """Loads the EPUB file."""
        try:
            self.book = epub.read_epub(self.file_path)
            # print(f"DEBUG: Successfully loaded {self.file_path}")
        except Exception as e:
            raise RuntimeError(f"Failed to load EPUB: {e}")

    def get_metadata(self):
        """Extracts metadata."""
        if not self.book:
            return {}
        
        def get_meta(key):
            try:
                data = self.book.get_metadata('DC', key)
                if data:
                    return data[0][0]
                return "Unknown"
            except:
                return "Unknown"

        return {
            "title": get_meta('title'),
            "author": get_meta('creator'),
            "language": get_meta('language'),
        }

    def get_chapters(self):
        """Extracts chapters strictly following the TOC structure."""
        if not self.book:
            return []
        
        # 1. Linearize TOC to get the exact order and hierarchy
        toc_items = self._linearize_toc(self.book.toc)
        if not toc_items:
             # Fallback to spine if TOC is empty
             return self._process_spine()
             
        # 2. Group items by filename to minimize file parsing
        from bs4 import BeautifulSoup, Tag, NavigableString
        
        chapters = []
        
        # We need to process them in order.
        # But efficiently: we can cache soups.
        soup_cache = {} 
        
        # Pre-pass: Identify all anchors per file to define boundaries
        file_anchors = {} # filename -> list of (anchor_id, toc_index)
        for i, item in enumerate(toc_items):
            fname = item['filename']
            if fname not in file_anchors: file_anchors[fname] = []
            if item['anchor']:
                file_anchors[fname].append( (item['anchor'], i) )
        
        # Build set of TOC filenames for quick lookup
        toc_filenames = set(item['filename'] for item in toc_items)
        
        # Build ordered list of spine files
        spine_files = []
        for item in self.book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                spine_files.append(item.get_name())
        
        # Sort anchors isn't purely possible without parsing, 
        # but we rely on TOC order usually matching file order.
        # However, for robust slicing, we should find their true positions in DOM.
        
        for i, item in enumerate(toc_items):
            title = item['title']
            filename = item['filename']
            anchor = item['anchor']
            level = item['level']
            is_parent = item['is_parent'] # Derived from TOC tree
            
            # Load Content
            if filename not in soup_cache:
                item_obj = self.book.get_item_with_href(filename)
                if item_obj:
                    # Use lxml for speed if available, else html.parser
                    try:
                        soup_cache[filename] = BeautifulSoup(item_obj.get_content(), 'lxml')
                    except:
                        soup_cache[filename] = BeautifulSoup(item_obj.get_content(), 'html.parser')
                else:
                    soup_cache[filename] = None

            soup = soup_cache[filename]
            content = ""
            
            if soup:
                if not anchor:
                    # No anchor: Take content from start of file...
                    # ...UNTIL the first anchor that belongs to a *subsequent* chapter?
                    # Actually, if Part 1 is file.html, and Chap 1 is file.html#c1
                    # We want Part 1 to be Pre-C1.
                    
                    # Logic: Find the first element in this file that is targeted by ANY other TOC item
                    # that appears AFTER this current item.
                    # Or simpler: Just take the whole file? 
                    # If we take whole file, we duplicate content.
                    # BETTER: Define "Start Element".
                    # If no anchor, Start = Body (or first child).
                    
                    # If there are anchors in this file, we stop at the first one.
                    next_anchor_id = self._find_next_anchor_in_file(soup, file_anchors.get(filename, []), current_anchor=None)
                    content = self._extract_text_slice(soup, start_id=None, end_id=next_anchor_id)
                else:
                    # Check if anchor points to a container or a break point
                    target_el = soup.find(id=anchor)
                    if not target_el:
                        # Try name attribute
                        target_el = soup.find(attrs={"name": anchor})
                    
                    if target_el:
                         # Heuristic: Is it a Wrapper (div/section) with content?
                         # or a Header/Anchor expecting subsequent siblings?
                         
                         # If it's a section/div and has substantial text inside, use inner content.
                         # (Unless it has internal anchors used by other chapters? complex.)
                         # Let's assume Standard Ebook: Header ID -> Slice until next Header.
                         
                         next_anchor_id = self._find_next_anchor_in_file(soup, file_anchors.get(filename, []), current_anchor=anchor)
                         content = self._extract_text_slice(soup, start_id=anchor, end_id=next_anchor_id)
                    else:
                        # Anchor not found, fallback to full file or empty?
                        # Fallback to whole file is risky for duplicates.
                        # Let's log warning and take nothing? Or whole file?
                        # If a targeted Chapter anchor is missing, we might miss the chapter. 
                        # Better to take whole file or file-part.
                        content = str(soup) # Fallback
            
            # BLANK PAGE HANDLING: If content is very short, look ahead at next spine files
            # Some books start chapters with a blank page, but the actual content is in the next file
            cleaned_content_check = self._clean_text_for_length_check(content)
            if len(cleaned_content_check) < 100:
                # Find current file's position in spine
                try:
                    current_spine_idx = spine_files.index(filename)
                except ValueError:
                    current_spine_idx = -1
                
                if current_spine_idx >= 0:
                    # Determine next chapter's file to know where to stop
                    next_toc_filename = None
                    if i + 1 < len(toc_items):
                        next_toc_filename = toc_items[i + 1]['filename']
                    
                    # Look ahead at next 2 spine files
                    for look_ahead in range(1, 3):
                        next_spine_idx = current_spine_idx + look_ahead
                        if next_spine_idx >= len(spine_files):
                            break
                            
                        next_file = spine_files[next_spine_idx]
                        
                        # Stop if we've reached the next TOC entry's file
                        if next_file == next_toc_filename:
                            break
                        
                        # Skip if this file is a TOC entry (it's a chapter start)
                        if next_file in toc_filenames:
                            break
                        
                        # Load and extract content from this file
                        if next_file not in soup_cache:
                            item_obj = self.book.get_item_with_href(next_file)
                            if item_obj:
                                try:
                                    soup_cache[next_file] = BeautifulSoup(item_obj.get_content(), 'lxml')
                                except:
                                    soup_cache[next_file] = BeautifulSoup(item_obj.get_content(), 'html.parser')
                            else:
                                soup_cache[next_file] = None
                        
                        next_soup = soup_cache.get(next_file)
                        if next_soup:
                            next_content = self._extract_text_slice(next_soup, start_id=None, end_id=None)
                            if next_content:
                                content = content + "\n\n" + next_content if content else next_content
                                print(f"  - Merged blank page content for '{title}' from: {next_file}")
            
            chapters.append({
                'title': title,
                'content': content, 
                'level': level, 
                'is_parent': is_parent,
                'href': item['href'],
                'semantic_type': 'toc_entry'
            })
            
        return chapters
    
    def _clean_text_for_length_check(self, html_content):
        """Extracts plain text from HTML for length checking."""
        from bs4 import BeautifulSoup
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            return soup.get_text(strip=True)
        except:
            return html_content

    def _linearize_toc(self, toc_tree, level=1):
        """Flattens TOC to a list of dicts."""
        import re
        
        # Pattern to detect "Part X:" titles
        part_pattern = r'^Part\s+(?:[IVX]+|[0-9]+|One|Two|Three|Four|Five|Six|Seven|Eight|Nine|Ten)\s*[:\-]?\s*'
        
        items = []
        for node in toc_tree:
            if isinstance(node, tuple):
                section, children = node
                href = section.href
                parts = href.split('#')
                fname = parts[0]
                anchor = parts[1] if len(parts) > 1 else None
                
                title = section.title
                # Check if title matches Part pattern - these are always parents
                is_part_by_title = bool(re.match(part_pattern, title, re.IGNORECASE)) if title else False
                
                # is_parent is True if:
                # 1. Title matches "Part X:" pattern (logical parent), OR
                # 2. Has children in TOC tree (structural parent)
                items.append({
                    'title': title,
                    'filename': fname,
                    'anchor': anchor,
                    'href': href,
                    'level': level,
                    'is_parent': is_part_by_title or len(children) > 0
                })
                items.extend(self._linearize_toc(children, level + 1))
                
            elif isinstance(node, epub.Link):
                href = node.href
                parts = href.split('#')
                fname = parts[0]
                anchor = parts[1] if len(parts) > 1 else None
                
                title = node.title
                # Check if title matches Part pattern - these are always parents
                is_part_by_title = bool(re.match(part_pattern, title, re.IGNORECASE)) if title else False
                
                items.append({
                    'title': title,
                    'filename': fname,
                    'anchor': anchor,
                    'href': href,
                    'level': level,
                    'is_parent': is_part_by_title  # Only Part pattern, no children
                })
        return items

    def _find_next_anchor_in_file(self, soup, all_anchors, current_anchor):
        """Finds the ID of the next relevant anchor in the DOM order."""
        # This is the expensive/tricky part.
        # We need to sort 'all_anchors' based on their DOM position.
        # If we only do this once per file, it's okay.
        
        # 1. Find all elements for these anchors
        found_anchors = []
        for anc_id, idx in all_anchors:
            if anc_id == current_anchor: continue
            
            el = soup.find(id=anc_id) or soup.find(attrs={"name": anc_id})
            if el:
                found_anchors.append(el)
        
        # 2. Add the current anchor element to find relative pos
        current_el = None
        if current_anchor:
            current_el = soup.find(id=current_anchor) or soup.find(attrs={"name": current_anchor})
        
        # If we can't find current, we can't determine "next".
        if current_anchor and not current_el:
            return None
            
        # 3. We want the first anchor from 'found_anchors' that follows 'current_el'
        # Simple approach: Iterate all elements in soup, see which one we hit first.
        # Optimized: Just rely on document order if we could.
        
        # Let's iterate using soup.find_all() which guarantees document order.
        # We collect the IDs we care about.
        target_ids = set([a[0] for a in all_anchors])
        
        # We need to find "Next" relative to current.
        passed_current = False if current_anchor else True # If no current (start of file), we are already passed "start"
        
        # Iterate all tags with ID or Name
        for tag in soup.find_all(attrs={"id": True}):
            tid = tag['id']
            if tid == current_anchor:
                passed_current = True
                continue
            if passed_current and tid in target_ids:
                return tid
        
        # Also check 'name' attributes
        for tag in soup.find_all(attrs={"name": True}):
            tid = tag['name']
            if tid == current_anchor:
                passed_current = True
                continue
            if passed_current and tid in target_ids:
                return tid
                
        return None

    def _extract_text_slice(self, soup, start_id, end_id):
        """Extracts text/html between start_id and end_id."""
        # If start_id is None, start from Body/Top.
        # If end_id is None, go to End.
        
        # Strategy: Collect text from siblings.
        from bs4 import Tag, NavigableString
        
        content_parts = []
        
        start_el = None
        if start_id:
            start_el = soup.find(id=start_id) or soup.find(attrs={"name": start_id})
            
        # Heuristic: If start_el is a container (div/section) and we don't have an end_id (or end_id is outside),
        # check if it contains most of what we want. 
        # BUT, standard flow 'headers' approach is safer for flat structures.
        
        # We'll use a traversal.
        # Finds start element. Then traverse 'next_elements'.
        # Stop if we hit end_el (or any parent of end_el? No, end_el usually header).
        
        end_el = None
        if end_id:
            end_el = soup.find(id=end_id) or soup.find(attrs={"name": end_id})
        
        # Basic container check
        if start_el and start_el.name in ['div', 'section', 'article']:
             # If the end_el is NOT inside this container, this container might BE the chapter.
             # check if end_el is descendant
             if end_el and start_el.find(id=end_id):
                  # End is inside. So we must slice inside.
                  pass
             elif not end_el:
                  # No end, so take the whole container?
                  # Yes, likely.
                  return str(start_el)
        
        # Traversal Generator
        # Start: if start_el, start at current_el.next_sibling? Or start_el itself?
        # Usually we want the content AFTER the header.
        # But if the anchor is ON the content (e.g. <p id=1>), we want it.
        # If anchor is on header <h1>, we want header + content? Usually yes, to preserve title in content.
        
        walker = None
        if start_el:
            walker = start_el
            # Include start_el itself
            content_parts.append(str(walker))
            walker = walker.next_element # Go inside or next
        else:
             walker = soup.body.next_element if soup.body else soup.next_element
             
        while walker:
            if walker == end_el:
                break
            
            # Optimization: If walker contains end_el, don't just dump walker string.
            # But 'next_element' walks into children, so we shouldn't hit "container of end_el" before "end_el" 
            # unless we skip children.
            
            if isinstance(walker, NavigableString):
                content_parts.append(str(walker))
            elif isinstance(walker, Tag):
                # If this tag IS the end_el, stop.
                if walker == end_el: 
                    break
                # If this tag CONTAINS end_el, we must descend. "next_element" does descend.
                # So we don't append the whole tag string (which includes children), 
                # we just continue loop to hit children.
                pass
                
            walker = walker.next_element
            
        # Reconstruct HTML (messy) or just text? 
        # The prompt asked for "Structure", user is likely ok with text cleaning later.
        # But 'main.py' expects 'content' to be HTML-ish or Text.
        # We typically extract raw HTML and let 'cleaner' handle it.
        # Only concatenating NavigableStrings drops tags (formatting).
        # We want to keep <p>, <ul>, etc.
        
        # REVISED Traversal for HTML preservation:
        # It's hard to reconstruct valid HTML from stream of elements.
        # Better: Iterate Siblings at the highest level possible.
        
        collected_html = []
        
        current = start_el if start_el else (soup.body.contents[0] if soup.body and soup.body.contents else None)
        # If start_el, we usually want its siblings.
        # But if start_el has children, we already have them?
        
        # Simple extraction: Just TEXT is safer if we just want summary?
        # No, pipeline uses HTML structure.
        
        # Let's try: "Everything from Start EL to End EL" in source code.
        # Regex or string finding in soup.decode()?
        # Highly robust way:
        # str(soup) -> find index of str(start_el) -> find index of str(end_el).
        # Slice string.
        
        full_html = str(soup)
        start_idx = 0
        end_idx = len(full_html)
        
        if start_el:
             # This is tricky because str(start_el) might appear multiple times or vary.
             # but element objects are unique.
             pass 
             
        # FALLBACK: Just Text for now?
        # The main pipeline calls `cleaner.clean(content)`.
        # CleanText uses BeautifulSoup to get_text.
        # So providing Text is fine. Providing basic HTML is better.
        
        # Let's use the 'next_sibling' iteration at the start_el level.
        # If start_el is h1.
        # sibling 1 is p.
        # sibling 2 is h1 (end_el).
        # This works for flat.
        
        if start_el:
            curr = start_el.next_sibling
            collected_html.append(str(start_el)) # Keep the header/anchor
        else:
            curr = soup.body.contents[0] if soup.body else None
            
        while curr:
            if curr == end_el:
                break
            
            # Check if end_el is inside curr
            if isinstance(curr, Tag) and end_el and end_el in curr.descendants:
                 # It's inside. We need to go deeper??
                 # Or just stop here? If the next chapter starts INSIDE a div of this chapter...
                 # That's rare for structure. Usually chapters are siblings.
                 # If nested, usually outer is Part, inner is Chapter.
                 # If we are parsing Part, we WANT the inner chapters.
                 pass
            
            if isinstance(curr, Tag):
                collected_html.append(str(curr))
            elif isinstance(curr, NavigableString):
                collected_html.append(str(curr))
                
            curr = curr.next_sibling
            
        return "".join(collected_html)

    def _detect_title_from_content(self, html):
        from bs4 import BeautifulSoup
        try:
            soup = BeautifulSoup(html, 'html.parser')
            h1 = soup.find(['h1', 'h2', 'h3'])
            if h1:
                return h1.get_text().strip()
        except:
            pass
        return None

    def _process_toc(self, toc_tree, level=0):
        items = []
        for node in toc_tree:
            if isinstance(node, tuple):
                section, children = node
                
                # REFINEMENT: A parent is only a "Part" if it has narrative children.
                # We need to peek into children to see if any are NOT skipped.
                narrative_children = []
                for child_node in children:
                    c_title = ""
                    if isinstance(child_node, tuple):
                        c_title = child_node[0].title
                    elif hasattr(child_node, 'title'):
                        c_title = child_node.title
                    
                    if c_title and not should_skip_chapter(c_title):
                        narrative_children.append(child_node)
                
                if hasattr(section, 'href'):
                     item_content, anchor, header_level = self._get_item_content(section.href)
                     if item_content:
                         items.append({
                             'title': section.title, 
                             'content': item_content, 
                             'anchor': anchor,
                             'level': header_level if header_level else level,
                             'is_parent': len(narrative_children) > 0 # ONLY if it has narrative babies
                         })
                items.extend(self._process_toc(children, level + 1))
                
            elif isinstance(node, epub.Link):
                item_content, anchor, header_level = self._get_item_content(node.href)
                if item_content:
                    items.append({
                        'title': node.title, 
                        'content': item_content, 
                        'anchor': anchor,
                        'level': header_level if header_level else level,
                        'is_parent': False
                    })
            
            elif isinstance(node, epub.Section):
                if hasattr(node, 'href'):
                     item_content, anchor, header_level = self._get_item_content(node.href)
                     if item_content:
                         items.append({
                             'title': node.title, 
                             'content': item_content, 
                             'anchor': anchor,
                             'level': header_level if header_level else level,
                             'is_parent': False # Strict: only tuples with children are parents
                         })
        return items

    def _process_spine(self):
        items = []
        for item in self.book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                content = item.get_content().decode('utf-8')
                header_level = self._detect_header_level(content)
                items.append({
                    'title': item.get_name(), 
                    'content': content,
                    'anchor': None,
                    'level': header_level or 0
                })
        return items

    def _detect_header_level(self, html_content):
        """Detects the highest header level (h1, h2, etc.) in the content."""
        from bs4 import BeautifulSoup
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            for i in range(1, 4): # Check h1, h2, h3
                if soup.find(f'h{i}'):
                    return i
        except:
            pass
        return None

    def get_cover(self):
        """Extracts the cover image from the EPUB."""
        if not self.book:
            return None, None
        
        # Try to find cover image in metadata
        cover_id = None
        for item in self.book.get_metadata('OPF', 'cover'):
            if item:
                cover_id = item[1].get('content')
        
        if cover_id:
            cover_item = self.book.get_item_with_id(cover_id)
            if cover_item:
                return cover_item.get_content(), cover_item.media_type
        
        # Fallback: look for item with 'cover' in its name
        for item in self.book.get_items():
            if item.get_type() == ebooklib.ITEM_IMAGE:
                if 'cover' in item.get_name().lower():
                    return item.get_content(), item.media_type
        
        return None, None

    def _get_item_content(self, href):
        parts = href.split('#')
        file_href = parts[0]
        anchor = parts[1] if len(parts) > 1 else None
        
        item = self.book.get_item_with_href(file_href)
        if item:
            content = item.get_content().decode('utf-8')
            header_level = self._detect_header_level(content)
            return content, anchor, header_level
        return None, None, None


    def _clean_filename_title(self, filename):
        """Standardizes a filename to be a human-readable title."""
        if not filename:
            return "Unknown Chapter"
            
        # Remove extension
        name = os.path.splitext(filename)[0]
        
        # Replace common separators with spaces
        name = name.replace('_', ' ').replace('-', ' ')
        
        # Split camelCase (optional, but good for some files)
        # s1 = re.sub('(.)([A-Z][a-z]+)', r'\1 \2', name)
        # name = re.sub('([a-z0-9])([A-Z])', r'\1 \2', s1)
        
        return name.strip().title()

    def _detect_semantic_type(self, html_content):
        """Detects epub:type attribute in the content to identify structure."""
        from bs4 import BeautifulSoup
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            # Check body or first section/div for epub:type
            elements = soup.find_all(['body', 'section', 'div'], limit=3)
            for el in elements:
                if el.has_attr('epub:type'):
                    return el['epub:type'].lower()
                # Also check common class names if epub:type isn't there (fallback native-ish)
                if el.has_attr('class'):
                     classes = el['class'] if isinstance(el['class'], list) else el['class'].split()
                     if 'part' in classes or 'section' in classes:
                          return 'part_class'
            return None
        except:
            return None

