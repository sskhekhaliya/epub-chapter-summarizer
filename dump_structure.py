
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import os

def inspect_epub(file_path, output_file):
    book = epub.read_epub(file_path)
    
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
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f"{'HREF':<30} | {'TOC TITLE':<40} | {'H1/H2':<30} | {'CHARS'}\n")
        f.write("-" * 120 + "\n")
        
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
                
                f.write(f"{href:<30} | {title:<40} | {h1_text[:30]:<30} | {len(content)}\n")

if __name__ == "__main__":
    import os
    if os.path.exists("book"):
        epubs = [f for f in os.listdir("book") if f.lower().endswith(".epub")]
        if epubs:
            epub_path = os.path.join("book", epubs[0])
            inspect_epub(epub_path, "structure_full.txt")
            print("Full structure saved to structure_full.txt")
