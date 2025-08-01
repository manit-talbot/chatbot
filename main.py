from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAI
from langchain.prompts import PromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser
from langchain.memory import ConversationBufferMemory
from langchain.schema.runnable import RunnableLambda
from dotenv import load_dotenv
import os

#ChatBot class is used to initialize the components and setup the memory and rag chain
class ChatBot:
    def __init__(self):
        load_dotenv()
        self._initialize_components()
        self._setup_memory()
        self._setup_rag_chain()

    def _initialize_components(self):
        """ 
        Initialize the components and setup the memory and rag chain
        """
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
            # Split the documents into 2000 character chunks with 200 character overlap
            text_splitter = CharacterTextSplitter(chunk_size=2000, chunk_overlap=200)
            self.docs = text_splitter.split_documents(documents)

            # Create FAISS vector store from documents
            self.docsearch = FAISS.from_documents(self.docs, self.embeddings)

            # Save the FAISS index locally
            self.docsearch.save_local(self.faiss_index_path)
            print(f"FAISS index saved to {self.faiss_index_path}")

        # Initialize LLM
        self.llm = OpenAI()
        
    def _setup_memory(self):
        """Initialize conversation memory"""
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            input_key="question"
        )
        # Track if this is the first interaction to avoid unnecessary memory loading
        self._has_interaction_history = False

    def _setup_rag_chain(self):
        #prompt for accuracy and detail
        template = """
        You are a knowledgeable HR assistant specializing in company policies and procedures. 
        When answering questions, provide detailed, specific information including:
        - Exact policy requirements and procedures
        - Specific deadlines, timeframes, and important dates
        - Required forms, documents, or steps
        - Contact information or responsible parties
        - Any conditions, exceptions, or special circumstances
        - Policy section references when available
        
        If the context doesn't contain enough information to answer completely, say so clearly.
        Always be thorough and precise in your responses.
        
        {chat_history_section}
        
        Context: {context}
        Question: {question}
        
        Detailed Answer:
        """
        #prompt template for the rag chain
        self.prompt = PromptTemplate(template=template, input_variables=["context", "question", "chat_history_section"])

        #rag chain retreives top 4 relevant documents from the FAISS index
        #runnablelambda is used to add the chat history section to the input
        self.rag_chain = (
            RunnableLambda(lambda x: {
                            "context": self.docsearch.as_retriever(search_kwargs={"k": 4}).invoke(x["question"]),
                            "question": x["question"],
                            "chat_history_section": x["chat_history_section"]
                            })
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
        text_splitter = CharacterTextSplitter(chunk_size=2000, chunk_overlap=200)
        docs = text_splitter.split_documents(documents)

        # Recreate the FAISS index
        self.docsearch = FAISS.from_documents(docs, self.embeddings)

        # Save the updated index
        self.docsearch.save_local(self.faiss_index_path)
        print(f"FAISS index updated and saved to {self.faiss_index_path}")

    def chat(self, question):
        """Chat method that maintains conversation history"""
        # Retrieve chat history as messages
        chat_history = self.memory.load_memory_variables({}).get("chat_history", [])
        if chat_history:
            # Format history as readable string
            chat_history_section = ""
            for msg in chat_history:
                if hasattr(msg, "type") and msg.type == "human":
                    chat_history_section += f"User: {msg.content}\n"
                elif hasattr(msg, "type") and msg.type == "ai":
                    chat_history_section += f"Assistant: {msg.content}\n"
                else:
                    chat_history_section += f"{msg.content}\n"
            chat_history_section = f"Previous conversation:\n{chat_history_section}"
        else:
            chat_history_section = "This is the first question in our conversation."

        # Prepare input for the RAG chain
        inputs = {
            "question": question,
            "chat_history_section": chat_history_section
        }

        # Get response
        response = self.rag_chain.invoke(inputs)

        # Save the new exchange to memory
        self.memory.save_context({"question": question}, {"output": response})

        return response
         
    def clear_memory(self):
        """Clear conversation memory"""
        self.memory.clear()
        # Reset the interaction history flag
        self._has_interaction_history = False