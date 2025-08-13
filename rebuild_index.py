#!/usr/bin/env python3
"""
Script to rebuild the FAISS index with all documents in the docs-text directory
"""
from langchain_community.document_loaders import TextLoader, UnstructuredMarkdownLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
import os
import sys
from dotenv import load_dotenv

def rebuild_faiss_index():
    """
    Rebuild the FAISS index with all documents in docs-text directory
    """
    load_dotenv()
    
    # Initialize embeddings
    embeddings = OpenAIEmbeddings()
    
    # Define paths
    docs_directory = "docs-text"
    faiss_index_path = "faiss_index"
    
    # Get all text and markdown files in the directory
    text_files = [f for f in os.listdir(docs_directory) if f.endswith('.txt')]
    markdown_files = [f for f in os.listdir(docs_directory) if f.endswith('.md')]
    all_files = text_files + markdown_files
    
    if not all_files:
        print(f"No text or markdown files found in {docs_directory}")
        return False
    
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
        return False
    
    print(f"Total chunks to index: {len(all_docs)}")
    
    # Create FAISS index
    try:
        docsearch = FAISS.from_documents(all_docs, embeddings)
        
        # Save the index
        docsearch.save_local(faiss_index_path)
        print(f"FAISS index successfully created and saved to {faiss_index_path}")
        
        return True
        
    except Exception as e:
        print(f"Error creating FAISS index: {str(e)}")
        return False

if __name__ == "__main__":
    print("Rebuilding FAISS index with all documents...")
    success = rebuild_faiss_index()
    
    if success:
        print("FAISS index rebuilt successfully!")
        print("You can now start your chatbot with: streamlit run interface.py")
    else:
        print("Failed to rebuild FAISS index")
        sys.exit(1)