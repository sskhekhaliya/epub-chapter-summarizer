from langchain_text_splitters import RecursiveCharacterTextSplitter

class Chunker:
    def __init__(self, chunk_size=24000, chunk_overlap=200):
        # Mistral-7B has a context of 8k or 32k usually. Safe limit 4096 chars or tokens.
        # Recursive splitter counts characters by default. 1 token ~ 4 chars.
        # So 4096 chars is ~1000 tokens. Safe.
        # User goal: "If chapter is longer than model safe input window".
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""]
        )

    def chunk(self, text):
        """Splits text into chunks."""
        if not text:
            return []
        return self.splitter.split_text(text)
