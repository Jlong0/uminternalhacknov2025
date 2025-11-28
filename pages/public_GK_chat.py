import streamlit as st
from utils import get_jam_ai_response, JAMAI_PROJECT_ID

st.title("💊 General Health Chatbot")
st.write("Ask about **general medication usage or mild disease information** (e.g., flu, headache).")
st.warning("⚠️ **Disclaimer:** This chatbot provides general information only and is NOT a substitute for professional medical advice. Always consult a healthcare professional for specific medical guidance.")

# --- General Knowledge Chat Interface ---

# Display chat history
for message in st.session_state["gk_messages"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User input
if user_input := st.chat_input("Ask a question about medication or a mild illness..."):
    st.session_state["gk_messages"].append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)
    
    # Get AI response
    with st.chat_message("ai"):
        with st.spinner('Contacting JAM AI...'):
            # Call shared mock AI function with the 'General Knowledge' context
            ai_response = get_jam_ai_response(JAMAI_PROJECT_ID, user_input, "General Knowledge")
            st.markdown(ai_response)
            
        st.session_state["gk_messages"].append({"role": "ai", "content": ai_response})
        st.rerun() # Rerun to update chat history instantly
        
st.markdown("---")
st.page_link("app.py", label="🏠 Back to Main Menu", icon="🏠")