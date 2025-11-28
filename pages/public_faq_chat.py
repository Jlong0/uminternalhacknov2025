import streamlit as st
from utils import get_jam_ai_response, JAMAI_PROJECT_ID

st.title("📚 Clinic FAQs Chatbot")
st.write("Ask questions about **clinic hours, appointments, or services**.")
st.caption("This chatbot is specialized to answer only clinic-specific administrative questions.")

# --- FAQ Chat Interface ---

# Display chat history
for message in st.session_state["faq_messages"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User input
if user_input := st.chat_input("Ask a question about the clinic..."):
    st.session_state["faq_messages"].append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)
    
    # Get AI response
    with st.chat_message("ai"):
        with st.spinner('Contacting JAM AI...'):
            # Call shared mock AI function with the 'FAQ Chatbot' context
            ai_response = get_jam_ai_response(JAMAI_PROJECT_ID, user_input, "FAQ Chatbot")
            st.markdown(ai_response)
            
        st.session_state["faq_messages"].append({"role": "ai", "content": ai_response})
        st.rerun() # Rerun to update chat history instantly

st.markdown("---")
st.page_link("app.py", label="🏠 Back to Main Menu", icon="🏠")