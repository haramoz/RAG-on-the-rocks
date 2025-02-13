
#!/bin/env python3
from langchain_core.globals import set_verbose, set_debug
from langchain_community.vectorstores import Chroma
from langchain_community.chat_models import ChatOllama
from langchain_community.embeddings import FastEmbedEmbeddings
from langchain.schema.output_parser import StrOutputParser
from langchain_community.document_loaders import PyPDFLoader
#from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema.runnable import RunnablePassthrough
from langchain_community.vectorstores.utils import filter_complex_metadata
from langchain_core.prompts import ChatPromptTemplate
from backend.chunking_strategy import TextChunker, RecursiveChunkingStrategy, SemanticChunkingStrategy
from langchain.docstore.document import Document




set_debug(True)
set_verbose(True)


class ProcessPDF:
    vector_store = None
    retriever = None
    chain = None

    def __init__(self, llm_model: str = "llama3.2"):
        self.model = ChatOllama(model=llm_model)
        """self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1024, chunk_overlap=100
        )"""

        #recursive_strategy = RecursiveChunkingStrategy(chunk_size=1024, chunk_overlap=100)
        #chunker = TextChunker(strategy=recursive_strategy)

        # To use semantic chunking
        semantic_strategy = SemanticChunkingStrategy(model='en_core_web_sm', chunk_size=1024)
        #chunker.set_strategy(semantic_strategy)
        chunker = TextChunker(strategy=semantic_strategy)

        text = "Your long text goes here..."
        chunks = chunker.chunk_text(text)
        print(chunks)

        self.prompt = ChatPromptTemplate(
            [
                (
                    "system",
                    "You are a helpful assistant that can answer questions about the PDF document that uploaded by the user. ",
                ),
                (
                    "human",
                    "Here is the document pieces: {context}\nQuestion: {question}",
                ),
            ]
        )

        self.vector_store = None
        self.retriever = None
        self.chain = None

    def ingest(self, pdf_file_path: str):
        docs = PyPDFLoader(file_path=pdf_file_path).load()
        #chunks = self.text_splitter.split_documents(docs)
        #chunks = filter_complex_metadata(chunks)

        chunker = TextChunker(RecursiveChunkingStrategy(chunk_size=1024, chunk_overlap=100))


        all_chunks = []
        for doc in docs:
            text_chunks = chunker.chunk_text(doc.page_content)
            # Create a new Document for each chunk, preserving the original metadata.
            for chunk in text_chunks:
                new_doc = Document(page_content=chunk, metadata=doc.metadata)
                all_chunks.append(new_doc)
    
        #all_chunks = filter_complex_metadata(all_chunks)
        
        self.vector_store = Chroma.from_documents(
            documents=all_chunks,
            embedding=FastEmbedEmbeddings(),
            persist_directory="chroma_db",
        )
        
        # embeddings = OpenAIEmbeddings()
        # embeddings = HuggingFaceInstructEmbeddings(model_name="hkunlp/instructor-xl")
        # vectorstore = FAISS.from_texts(texts=text_chunks, embedding=embeddings)


    def ask(self, query: str):

        ### Try Catch
        ### Proper logging
        ### Guard rails
        if not self.vector_store:
            self.vector_store = Chroma(
                persist_directory="chroma_db", embedding=FastEmbedEmbeddings()
            )
        else:
            print("logging, I am here!")

        self.retriever = self.vector_store.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={"k": 10, "score_threshold": 0.0},
        )

        self.retriever.invoke(query)

        self.chain = (
            {"context": self.retriever, "question": RunnablePassthrough()}
            | self.prompt
            | self.model
            | StrOutputParser()
        )

        if not self.chain:
            return "Please, add a PDF document first."

        return self.chain.invoke(query)

    def clear(self):
        self.vector_store = None
        self.retriever = None
        self.chain = None

