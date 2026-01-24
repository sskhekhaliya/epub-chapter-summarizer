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
        
        # Simple whitespace cleanup: collapse multiple newlines (>2) to 2
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = text.strip()
        
        return text
