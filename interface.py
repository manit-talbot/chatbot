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

st.set_page_config(page_title="Handbook Bot")
with st.sidebar:
    st.title('Handbook Bot')

# Function for generating LLM response
def generate_response(input_text):
    try:
        result = bot.rag_chain.invoke(input_text)
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
        with st.spinner("Getting your answer from handbook.."):
            response = generate_response(input_text)
            st.write(response)
    message = {"role": "assistant", "content": response}
    st.session_state.messages.append(message)