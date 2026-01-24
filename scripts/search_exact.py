
import sys
import os

def main():
    file_path = r"d:\Projects\Books Summary\output\breaking_the_cycle_chapter_summaries.json"
    search_term = "Here is a summary of the chapter text in the same voice and sentence structure as the original"
    
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return
        
    output_file = r"d:\Projects\Books Summary\search_report.txt"
    lines_found = []
    
    print(f"Searching for: '{search_term}'")
    
    found = False
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for i, line in enumerate(f, 1):
                if search_term.lower() in line.lower():
                    msg = f"Found on line {i}: {line.strip()}"
                    print(msg)
                    lines_found.append(msg)
                    found = True
    except Exception as e:
        print(f"Error reading file: {e}")
        return

    with open(output_file, "w", encoding="utf-8") as f:
        if found:
            f.write("\n".join(lines_found))
        else:
            f.write("Not found")

    if not found:
        print("Phrase NOT found in the file.")
    else:
        print("-" * 40)
        print(f"Phrase found! Details in {output_file}")

if __name__ == "__main__":
    main()
