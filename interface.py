import streamlit as st

# Initialize session state for bot
if "bot" not in st.session_state:
    try:
        from main import ChatBot
        st.session_state.bot = ChatBot()
    except Exception as e:
        st.error(f"Failed to initialize ChatBot: {str(e)}")
        st.stop()

bot = st.session_state.bot

st.set_page_config(page_title="Handbook & Manual Bot")
with st.sidebar:
    st.title('Handbook & Manual Bot')
    
    # Add a clear conversation button
    if st.button("Clear Conversation"):
        bot.clear_memory()
        st.session_state.messages = [{"role": "assistant", "content": "Conversation cleared. How can I assist you today?"}]
        st.rerun()
    
    # Add toggle for showing sources
    st.markdown("---")
    st.markdown("**Settings:**")
    show_sources = st.checkbox("Show relevant sources", value=True, help="Display the source documents used to generate each response")

# Function for generating LLM response using the optimized chat method
def generate_response(input_text):
    try:
        # chat method is used to generate the response 
        # rag_chain.invoke can raise errors if inputs are missing or misformatted
        result = bot.chat(input_text)
        return result
    except Exception as e:
        return {"response": f"Sorry, I encountered an error: {str(e)}", "relevant_docs": []}

# Store LLM generated responses
if "messages" not in st.session_state.keys():
    st.session_state.messages = [{"role": "assistant", "content": "Welcome, how can I assist you today?"}]

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# User-provided prompt
if input_text := st.chat_input():
    st.session_state.messages.append({"role": "user", "content": input_text})
    with st.chat_message("user"):
        st.write(input_text)

# Generate a new response if last message is not from assistant
if st.session_state.messages[-1]["role"] != "assistant":
    with st.chat_message("assistant"):
        with st.spinner("Getting your answer from documents.."):
            result = generate_response(input_text)
            
            # Handle both old string format and new dict format for backward compatibility
            if isinstance(result, dict):
                response = result["response"]
                relevant_docs = result.get("relevant_docs", [])
            else:
                response = result
                relevant_docs = []
            
            st.write(response)
            
            # Display relevant documents if available and toggle is enabled
            if relevant_docs and show_sources:
                st.markdown("---")
                st.markdown("**📚 Relevant Sources:**")
                
                # Format and display relevant documents
                docs_info = bot.get_relevant_docs_info(relevant_docs)
                
                # Show a summary of sources first
                source_files = list(set([doc_info['filename'] for doc_info in docs_info]))
                st.info(f"Found {len(relevant_docs)} relevant chunks from: {', '.join(source_files)}")
                
                for doc_info in docs_info:
                    with st.expander(f"📄 {doc_info['filename']} (Source {doc_info['number']})"):
                        st.markdown(f"**Content Preview:**")
                        st.text(doc_info['content_preview'])
                        st.markdown(f"**Full Content:**")
                        st.text(doc_info['full_content'])
                        st.markdown(f"**Source:** `{doc_info['source']}`")
                       # if doc_info['similarity_score'] != 'N/A':
                        #    st.markdown(f"**Relevance Score:** {doc_info['similarity_score']:.3f}")
    
    # Store the response text in messages (not the full result dict)
    if isinstance(result, dict):
        message_content = result["response"]
    else:
        message_content = result
    
    message = {"role": "assistant", "content": message_content}
    st.session_state.messages.append(message)