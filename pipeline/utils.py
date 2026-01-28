
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

def should_skip_chapter(title):
    """Determines if a chapter should be skipped based on its title."""
    title_lower = title.lower()
    
    # Narrative sections we definitely want to KEEP
    keep_keywords = ['introduction', 'foreword', 'prologue', 'epilogue', 'afterword', 'preface']
    if any(k in title_lower for k in keep_keywords):
        return False
        
    # Non-narrative sections we want to SKIP
    skip_keywords = [
        'contents', 'copyright', 'about the author', 'also by', 'back ads', 
        'advance praise', 'praise for', 'title page', 'acknowledgments',
        'dedication', 'other books', 'praise', 'backads', 'acclaim', 'cover',
        'production', 'version',
    ]
    if any(k in title_lower for k in skip_keywords):
        return True
        
    return False

def has_meaningful_content(content, min_chars=150):
    """
    Checks if the content has meaningful text worth summarizing.
    Returns False if content is essentially empty or just a heading.
    
    Args:
        content: The text content to check
        min_chars: Minimum character count for meaningful content (default 150)
    """
    if not content:
        return False
    
    # Strip whitespace and check length
    cleaned = content.strip()
    if len(cleaned) < min_chars:
        return False
    
    # Check if it's mostly just whitespace or punctuation
    import re
    # Remove all whitespace and count actual content
    alphanumeric = re.sub(r'[^a-zA-Z0-9]', '', cleaned)
    if len(alphanumeric) < min_chars // 2:
        return False
    
    return True
