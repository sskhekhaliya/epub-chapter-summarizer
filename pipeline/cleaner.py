from bs4 import BeautifulSoup
import re

class CleanText:
    @staticmethod
    def clean(html_content):
        """Cleans HTML content to plain text."""
        if not html_content:
            return ""
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove unwanted tags
        for script in soup(["script", "style", "header", "footer", "nav", "meta", "noscript"]):
            script.decompose()

        # Get text
        # separator='\n\n' preserves paragraph breaks better
        text = soup.get_text(separator='\n\n')
        
        
        # 1. Collapse multiple newlines (>2) to 2
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # 2. Fix fragmented lines (e.g. "word\n." -> "word.")
        # Finds a distinct newline followed by a single punctuation char
        text = re.sub(r'\n\s*([.,;:])', r'\1', text)
        
        # 3. Join evidently broken lines where a lowercase follows a newline?
        # Use caution here, but usually in novels, newlines start with Upper or Quote.
        # Strict approach: just general cleanup for now.
        
        text = text.strip()
        
        return text
