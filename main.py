from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser
from langchain.memory import ConversationBufferMemory
from langchain.schema.runnable import RunnableLambda
from langchain_community.document_loaders import UnstructuredMarkdownLoader
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
            # Load and process all documents from docs-text directory
            self._create_faiss_index_from_directory()

        # Initialize LLM with better configuration for longer responses
        self.llm = ChatOpenAI(
            model="gpt-4o",
            max_tokens=2000,
            timeout=60,
            temperature=0.1,
            max_retries=2,
            api_key=os.getenv("OPENAI_API_KEY")
        )
             # Increase timeout for longer response)
        
    def _create_faiss_index_from_directory(self, docs_directory="docs-text"):
        """
        Create FAISS index from all text and markdown files in the specified directory
        """
        # Get all text and markdown files in the directory
        text_files = [f for f in os.listdir(docs_directory) if f.endswith('.txt')]
        markdown_files = [f for f in os.listdir(docs_directory) if f.endswith('.md')]
        all_files = text_files + markdown_files
        
        if not all_files:
            print(f"No text or markdown files found in {docs_directory}")
            # Create empty index as fallback
            self.docsearch = FAISS.from_documents([], self.embeddings)
            self.docsearch.save_local(self.faiss_index_path)
            return
        
        print(f"Found {len(text_files)} text files and {len(markdown_files)} markdown files to process")
        
        # Load and combine all documents
        all_docs = []
        text_splitter = CharacterTextSplitter(
            chunk_size=1500,
            chunk_overlap=200,
            separator = "\n\n"
            )
        
        # Process text files
        for text_file in text_files:
            file_path = os.path.join(docs_directory, text_file)
            print(f"Processing text file: {text_file}...")
            
            try:
                loader = TextLoader(file_path)
                documents = loader.load()
                
                # Split documents
                split_docs = text_splitter.split_documents(documents)
                all_docs.extend(split_docs)
                
                print(f"Added {len(split_docs)} chunks from {text_file}")
                
            except Exception as e:
                print(f"Error processing {text_file}: {str(e)}")
        
        # Process markdown files
        for markdown_file in markdown_files:
            file_path = os.path.join(docs_directory, markdown_file)
            print(f"Processing markdown file: {markdown_file}...")
            
            try:
                loader = UnstructuredMarkdownLoader(file_path)
                documents = loader.load()
                
                # Split documents
                split_docs = text_splitter.split_documents(documents)
                all_docs.extend(split_docs)
                
                print(f"Added {len(split_docs)} chunks from {markdown_file}")
                
            except Exception as e:
                print(f"Error processing {markdown_file}: {str(e)}")
        
        if not all_docs:
            print("No documents were successfully loaded")
            # Create empty index as fallback
            self.docsearch = FAISS.from_documents([], self.embeddings)
        else:
            print(f"Total chunks to index: {len(all_docs)}")
            # Create FAISS vector store from documents
            self.docsearch = FAISS.from_documents(all_docs, self.embeddings)
        
        # Save the FAISS index locally
        self.docsearch.save_local(self.faiss_index_path)
        print(f"FAISS index saved to {self.faiss_index_path}")
        
    def _setup_memory(self):
        """Initialize conversation memory"""
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            input_key="question",
            output_key="output",
            k=8 # Keep more context 
        )
        # Track if this is the first interaction to avoid unnecessary memory loading
        self._has_interaction_history = False

    def _setup_rag_chain(self):
        #prompt for accuracy and detail
        template = """
        You are a knowledgeable HR assistant specializing in company policies and procedures. 
        When answering questions, provide comprehensive, detailed information including:
        - Exact policy requirements and procedures
        - Specific deadlines, timeframes, and important dates
        - Required forms, documents, or steps
        - Contact information or responsible parties
        - Any conditions, exceptions, or special circumstances
        - Policy section references when available.
        
        IMPORTANT: For health-related policies, always prioritize accuracy and completeness over brevity.
        If the context doesn't contain enough information to answer completely, say so clearly.
        Always be thorough and precise in your responses.
        
        {chat_history_section}
        
        Context: {context}
        Question: {question}
        
        Detailed Answer:
        """
        #prompt template for the rag chain
        self.prompt = PromptTemplate(
            template=template,
            input_variables=["context", "question", "chat_history_section"])

        #rag chain retreives top 4 relevant documents from the FAISS index
        #runnablelambda is used to add the chat history section to the input
        self.rag_chain = (
            RunnableLambda(lambda x: {
                            "context": "\n\n".join([doc.page_content for doc in self.docsearch.as_retriever(search_kwargs={"k": 5}).invoke(x["question"])]),
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
            # If a specific document is provided, check if it's in docs-text directory
            if os.path.exists(new_documents_path):
                print(f"Document {new_documents_path} found. Rebuilding index with all documents...")
                self._create_faiss_index_from_directory()
                print(f"FAISS index updated and saved to {self.faiss_index_path}")
            else:
                print(f"Document {new_documents_path} not found. Please place it in the docs-text directory.")
        else:
            # Rebuild index from all documents in docs-text directory
            self._create_faiss_index_from_directory()
            print(f"FAISS index updated and saved to {self.faiss_index_path}")

    def chat(self, question):
        """Chat method that maintains conversation history"""
        # Retrieve chat history as messages
        chat_history = self.memory.load_memory_variables({}).get("chat_history", [])
        if chat_history:
            # Format history as readable string
            chat_history_section = ""
            for msg in chat_history:
                # Handle different message types from ChatOpenAI
                if hasattr(msg, "type"):
                    if msg.type == "human":
                        chat_history_section += f"User: {msg.content}\n"
                    elif msg.type == "ai":
                        chat_history_section += f"Assistant: {msg.content}\n"
                    else:
                        chat_history_section += f"{msg.content}\n"
                elif hasattr(msg, "role"):
                    # Handle ChatMessage format
                    if msg.role == "user":
                        chat_history_section += f"User: {msg.content}\n"
                    elif msg.role == "assistant":
                        chat_history_section += f"Assistant: {msg.content}\n"
                    else:
                        chat_history_section += f"{msg.content}\n"
                else:
                    # Fallback for other message formats
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