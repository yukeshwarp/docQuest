import streamlit as st
from utils.pdf_processing import process_pdf_pages
from utils.llm_interaction import ask_question

# Initialize session state variables to avoid reloading and reprocessing
if 'document_data' not in st.session_state:
    st.session_state.document_data = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'question_input' not in st.session_state:
    st.session_state.question_input = ""

# Function to handle user question and get the answer
def handle_question(question):
    if question:
        # Use the cached document data for the query
        answer = ask_question(st.session_state.document_data, question)
        # Add the question-answer pair to the chat history
        st.session_state.chat_history.append({"question": question, "answer": answer})
        # Clear the input field after sending
        st.session_state.question_input = ""
        # Ensure the chat history updates correctly
        st.rerun()

# Streamlit application title
st.title("docQuest")

# Sidebar for file upload and document information
with st.sidebar:
    st.subheader("docQuest")
    
    # File uploader
    uploaded_file = st.file_uploader("Upload and manage files here", type=["pdf"])
    
    # Process the PDF if uploaded and not already processed
    if uploaded_file and st.session_state.document_data is None:
        with st.spinner('Processing PDF...'):
            st.session_state.document_data = process_pdf_pages(uploaded_file)
        st.success("PDF processed successfully! Let's explore your document.")
        st.rerun()  # Reload to reflect changes

# Main page for chat interaction
if st.session_state.document_data:
    st.subheader("Hi! Let's know more about your document..")
    
    # Display chat history in a chat-like format
    if st.session_state.chat_history:
        st.subheader("Chats", divider="orange")
        for chat in st.session_state.chat_history:
            st.markdown(f"\n")
            st.markdown(f"**Quest:** {chat['question']}")
            st.markdown(f"**Finds:** {chat['answer']}")

    # Input for user questions
    question = st.text_input("What would you like to know about the document?", value=st.session_state.question_input, key="question_input")
    if st.button("Send"):
        handle_question(question)
