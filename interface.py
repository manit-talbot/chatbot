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

# Function for generating LLM response using the optimized chat method
def generate_response(input_text):
    try:
        # chat method is used to generate the response 
        # rag_chain.invoke can raise errors if inputs are missing or misformatted
        result = bot.chat(input_text)
        return result
    except Exception as e:
        return f"Sorry, I encountered an error: {str(e)}"

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
            response = generate_response(input_text)
            st.write(response)
    message = {"role": "assistant", "content": response}
    st.session_state.messages.append(message)