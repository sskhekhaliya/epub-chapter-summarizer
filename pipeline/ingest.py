import ebooklib
from ebooklib import epub
import os

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
        """Extracts chapters as a list of dicts: {'title': str, 'content': str, 'level': int}."""
        if not self.book:
            return []
        
        # Try processing TOC
        chapters = self._process_toc(self.book.toc)
        
        # If TOC is empty, fallback to spine (simple extraction)
        if not chapters:
            print("Warning: Empty TOC, falling back to spine.")
            chapters = self._process_spine()
            
        return chapters

    def _process_toc(self, toc_tree, level=0):
        items = []
        for node in toc_tree:
            if isinstance(node, tuple):
                section, children = node
                if hasattr(section, 'href'):
                     item_content, anchor, header_level = self._get_item_content(section.href)
                     if item_content:
                         items.append({
                             'title': section.title, 
                             'content': item_content, 
                             'anchor': anchor,
                             'level': header_level if header_level else level,
                             'is_parent': len(children) > 0
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
                             'is_parent': True # Section itself is a parent context
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

