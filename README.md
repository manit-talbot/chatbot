# RAG Chatbot for Docs
This is a simple RAG Chatbot with a streamlit interface present in the interface.py and the main.py has the class Chatbot which actually carries out the main functionality.

# File Strcuture
- docs folder contain the actual file
- docs-text folder contain the text file converted from the actual files present in docs folder
- faiss-index folder has the actual FAISS vectordb made from the .txt file (handbook docs)

# Info about the Chatbot
- We are using OpenAI Embeddings
- We are using locally set up FAISS Vector DB
- We are using OpenAI LLMs

# What we aim to work on currently
- Improve the prompt (Line 54 in main.py)
- Add chat-history in the rag-chain so that the LLM remembers the previously asked questions
- Improve the chunking and retreival strategies if needed
- Switch LLMs and Embedding models if needed
- In future maybe use a remotely hosted VectorDB like Pinecone, ChromaDB etc.
- Play around with input format if needed. Maybe structured format like .md can perform better.
