
import uuid

def text_to_portable_text(text):
    """
    Standard conversion of plain text (with \n\n for paragraphs) 
    to Sanity Portable Text blocks.
    Ensures consistent styles, keys, and structure.
    """
    blocks = []
    if not text:
        return blocks
    
    # Split by double newlines for paragraphs
    # Handle both \n\n and \r\n\r\n
    paragraphs = text.replace('\r\n', '\n').split('\n\n')
    
    for p in paragraphs:
        p = p.strip()
        if not p:
            continue
        blocks.append({
            "_type": "block",
            "_key": str(uuid.uuid4()),
            "style": "normal",
            "markDefs": [],
            "children": [
                {
                    "_type": "span",
                    "_key": str(uuid.uuid4()),
                    "text": p,
                    "marks": []
                }
            ]
        })
    return blocks
