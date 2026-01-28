
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup

def inspect_epub(file_path):
    book = epub.read_epub(file_path)
    
    # 1. Map href to TOC titles
    def get_toc_map(toc_tree, level=0, toc_map=None):
        if toc_map is None: toc_map = {}
        for node in toc_tree:
            if isinstance(node, tuple):
                section, children = node
                href = section.href.split('#')[0]
                toc_map[href] = {'title': section.title, 'level': level}
                get_toc_map(children, level + 1, toc_map)
            elif isinstance(node, epub.Link):
                href = node.href.split('#')[0]
                toc_map[href] = {'title': node.title, 'level': level}
        return toc_map

    toc_map = get_toc_map(book.toc)
    
    print(f"{'HREF':<30} | {'TOC TITLE':<30} | {'H1/H2'} | {'CHARS'}")
    print("-" * 100)
    
    last_title = None
    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            href = item.get_name()
            content = item.get_content().decode('utf-8')
            soup = BeautifulSoup(content, 'html.parser')
            h1 = soup.find(['h1', 'h2', 'h3'])
            h1_text = h1.get_text().strip() if h1 else "None"
            
            toc_info = toc_map.get(href)
            title = toc_info['title'] if toc_info else f"(Orphan: {last_title})"
            if toc_info:
                last_title = title
            
            print(f"{href:<30} | {title:<30} | {h1_text[:20]:<20} | {len(content)}")

if __name__ == "__main__":
    import sys
    epub_path = "book/the-alchemist.epub" # Assuming the name based on the slug
    # Find the actual epub in the book folder
    import os
    if os.path.exists("book"):
        epubs = [f for f in os.listdir("book") if f.lower().endswith(".epub")]
        if epubs:
            epub_path = os.path.join("book", epubs[0])
            inspect_epub(epub_path)
        else:
            print("No EPUB found in 'book' folder.")
    else:
        print("'book' folder not found.")
