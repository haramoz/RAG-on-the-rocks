# chunking_strategy.py

from abc import ABC, abstractmethod
import spacy
from langchain.text_splitter import RecursiveCharacterTextSplitter

class ChunkingStrategy(ABC):
    """
    Abstract base class for text chunking strategies.
    """
    @abstractmethod
    def chunk_text(self, text: str) -> list[str]:
        """Chunk the input text and return a list of chunks."""
        pass

class RecursiveChunkingStrategy(ChunkingStrategy):
    """
    Implements text chunking using a recursive character splitter.
    """
    def __init__(self, chunk_size: int = 1024, chunk_overlap: int = 100):
        self.splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    
    def chunk_text(self, text: str) -> list[str]:
        return self.splitter.split_text(text)

class SemanticChunkingStrategy(ChunkingStrategy):
    """
    Implements semantic text chunking using spaCy. This strategy processes the text
    into sentences and groups them into chunks based on a maximum chunk size.
    """
    def __init__(self, model: str = 'en_core_web_sm', chunk_size: int = 1024):
        self.nlp = spacy.load(model)
        self.chunk_size = chunk_size

    def chunk_text(self, text: str) -> list[str]:
        # Process the text to obtain sentence boundaries
        doc = self.nlp(text)
        chunks = []
        current_chunk = ""
        for sent in doc.sents:
            # Check if adding the current sentence would exceed the chunk size
            if len(current_chunk) + len(sent.text) > self.chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = sent.text
                else:
                    # If the sentence itself exceeds the chunk size, add it on its own
                    chunks.append(sent.text)
                    current_chunk = ""
            else:
                # Append the sentence to the current chunk
                current_chunk += " " + sent.text if current_chunk else sent.text
        if current_chunk:
            chunks.append(current_chunk.strip())
        return chunks

class TextChunker:
    """
    Context class that uses a chunking strategy. You can change the strategy at runtime.
    """
    def __init__(self, strategy: ChunkingStrategy):
        self.strategy = strategy

    def set_strategy(self, strategy: ChunkingStrategy):
        self.strategy = strategy

    def chunk_text(self, text: str) -> list[str]:
        return self.strategy.chunk_text(text)
