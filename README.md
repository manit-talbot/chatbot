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
- Improve the prompt (Line 54 in main.py) - improved the prompt to give more detailed response 
- Add chat-history in the rag-chain so that the LLM remembers the previously asked questions - added chat history using ConversationBufferMemory
- Improve the chunking and retreival strategies if needed - improved chunking size and search kwargs for rag to 4 to get top 4 related documents
- Switch LLMs and Embedding models if needed 
- In future maybe use a remotely hosted VectorDB like Pinecone, ChromaDB etc.
- Play around with input format if needed. Maybe structured format like .md can perform better.

# FAISS index:
- To rebuild faiss : `rm -r faiss_index/` then `streamlit run interface.py`
- Processed all md files 
- Create embeddings for all content
- Build a new FAISS index with both documents
- Save the index to faiss_index


1. Markdown File Processing: loaded using `UnstructuredMarkdownLoader`
2. Chunking: Both files are split into 1500-character chunks with 200-character overlap
3. Embedding: All chunks are converted to vector embeddings using OpenAI
4. Indexing: FAISS creates a searchable index from all embeddings
5. chatbot can now answer questions from both documents

To add more files in the future:

1. Place new `.md` files in the `docs-text/` directory
2. Run rebuild_index.py
3. Restart your chatbot

