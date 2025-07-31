from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAI
from langchain.prompts import PromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser
from dotenv import load_dotenv
import os

class ChatBot:
    def __init__(self):
        load_dotenv()
        self._initialize_components()
        self._setup_rag_chain()

    def _initialize_components(self):
        # Initialize embeddings with OpenAI
        self.embeddings = OpenAIEmbeddings()

        # Define the path for the FAISS index
        self.faiss_index_path = "faiss_index"

        # Check if FAISS index already exists locally
        if os.path.exists(self.faiss_index_path):
            print("Loading existing FAISS index...")
            # Load the existing FAISS index
            self.docsearch = FAISS.load_local(
                self.faiss_index_path,
                self.embeddings,
                allow_dangerous_deserialization=True
            )
        else:
            print("Creating new FAISS index...")
            # Load and process documents
            loader = TextLoader('docs-text/handbook.txt')
            documents = loader.load()
            text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=4)
            self.docs = text_splitter.split_documents(documents)

            # Create FAISS vector store from documents
            self.docsearch = FAISS.from_documents(self.docs, self.embeddings)

            # Save the FAISS index locally
            self.docsearch.save_local(self.faiss_index_path)
            print(f"FAISS index saved to {self.faiss_index_path}")

        # Initialize LLM
        self.llm = OpenAI()

    def _setup_rag_chain(self):
        template = """
        You are a helpful assistant that answers questions based on the provided context.

        Context: {context}
        Question: {question}
        Answer:
        """

        self.prompt = PromptTemplate(template=template, input_variables=["context", "question"])

        self.rag_chain = (
            {"context": self.docsearch.as_retriever(), "question": RunnablePassthrough()}
            | self.prompt
            | self.llm
            | StrOutputParser()
        )

    def update_documents(self, new_documents_path=None):
        """
        Method to update the FAISS index when documents change
        """
        if new_documents_path:
            loader = TextLoader(new_documents_path)
        else:
            loader = TextLoader('handbook.txt')

        documents = loader.load()
        text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=4)
        docs = text_splitter.split_documents(documents)

        # Recreate the FAISS index
        self.docsearch = FAISS.from_documents(docs, self.embeddings)

        # Save the updated index
        self.docsearch.save_local(self.faiss_index_path)
        print(f"FAISS index updated and saved to {self.faiss_index_path}")