
from pipeline.ingest import EpiubLoader
from pipeline.cleaner import CleanText
import os

def dump_part_one(epub_path):
    loader = EpiubLoader(epub_path)
    loader.load()
    chapters = loader.get_chapters()
    cleaner = CleanText()
    
    for ch in chapters:
        if ch['title'] == 'Part One':
            cleaned = cleaner.clean(ch['content'])
            with open("part_one_cleaned.txt", "a", encoding="utf-8") as f:
                f.write(f"--- HREF: {ch['href']} ---\n")
                f.write(cleaned)
                f.write("\n\n")
            # Also dump raw HTML for one of them to check for image junk
            if len(ch['content']) > 1000:
                with open("part_one_raw.html", "w", encoding="utf-8") as f:
                    f.write(ch['content'])

if __name__ == "__main__":
    if os.path.exists("book"):
        epubs = [f for f in os.listdir("book") if f.lower().endswith(".epub")]
        if epubs:
            epub_path = os.path.join("book", epubs[0])
            if os.path.exists("part_one_cleaned.txt"): os.remove("part_one_cleaned.txt")
            dump_part_one(epub_path)
            print("Done dumping Part One.")
