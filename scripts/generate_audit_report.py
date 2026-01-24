
import json
import os

def main():
    file_path = r"d:\Projects\Books Summary\output\breaking_the_cycle_chapter_summaries.json"
    output_report = r"d:\Projects\Books Summary\audit_report.txt"
    
    if not os.path.exists(file_path):
        print("JSON file not found.")
        return

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    report_lines = []
    report_lines.append(f"AUDIT REPORT FOR: {data.get('title', 'Unknown Book')}")
    desc_preview = data.get('bookDescription', '')[:100].replace('\n', ' ')
    report_lines.append(f"Book Description Start: {desc_preview}...")
    report_lines.append("-" * 60)

    def extract_text_from_blocks(blocks):
        if not blocks: return ""
        text = []
        for block in blocks:
            if block.get("_type") == "block" and "children" in block:
                for child in block["children"]:
                    if "text" in child:
                        text.append(child["text"])
        return " ".join(text)

    # Traverse structure
    # The structure might be nested (Parts -> Chapters) or flat.
    # Based on main.py, it seems 'bookStructure' or just a list of chapters?
    # Let's check the schema in the file.
    
    # Actually, looking at main.py saved structure:
    # It saves `final_chapters`... wait, `JSONFormatter.save` structure:
    # { ..., "bookStructure": [ {chapter...}, {part...} ] }
    
    structure = data.get("bookStructure", [])
    
    for item in structure:
        if item.get("_type") == "part":
            title = item.get("partTitle", "Untitled Part")
            desc_blocks = item.get("partDescription", [])
            desc_text = extract_text_from_blocks(desc_blocks)
            report_lines.append(f"[PART] {title}")
            desc_text_clean = desc_text[:80].replace(chr(10), ' ')
            report_lines.append(f"  > Start: \"{desc_text_clean}...\"")
            
            # Parts might have chapters inside?
            if "chapters" in item:
                for ch in item["chapters"]:
                    ch_title = ch.get("chapterTitle", "Untitled Chapter")
                    ch_sum_blocks = ch.get("chapterSummary", [])
                    ch_text = extract_text_from_blocks(ch_sum_blocks)
                    ch_text_clean = ch_text[:80].replace(chr(10), ' ')
                    report_lines.append(f"  [CHAPTER] {ch_title}")
                    report_lines.append(f"    > Start: \"{ch_text_clean}...\"")
                    
        elif item.get("_type") == "chapter":
            title = item.get("chapterTitle", "Untitled Chapter")
            sum_blocks = item.get("chapterSummary", [])
            text = extract_text_from_blocks(sum_blocks)
            text_clean = text[:80].replace(chr(10), ' ')
            report_lines.append(f"[CHAPTER] {title}")
            report_lines.append(f"  > Start: \"{text_clean}...\"")

    with open(output_report, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))

    print(f"Audit report generated at: {output_report}")

if __name__ == "__main__":
    main()
