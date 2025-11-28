import streamlit as st
from utils import check_staff_login, get_jam_ai_response, JAMAI_PROJECT_ID

# 1. Security Check: Stop execution if not logged in
check_staff_login()

st.title("🧑‍⚕️ Staff Main Portal")
st.info("Welcome, Staff! Your access is confirmed. Use the specialized chatbot below.")

st.subheader("🤖 Staff Management Chatbot")
st.write("This chatbot assists with internal staff management queries (e.g., HR, scheduling, policy).")

# --- Staff Chat Interface ---

# Display chat history
for message in st.session_state["staff_messages"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User input
if user_input := st.chat_input("Ask a question about staff handling..."):
    # Add user message to history
    st.session_state["staff_messages"].append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)
    
    # Get AI response
    with st.chat_message("ai"):
        with st.spinner('Contacting JAM AI...'):
            # Call shared mock AI function with the 'Staff Management' context
            ai_response = get_jam_ai_response(JAMAI_PROJECT_ID, user_input, "Staff Management")
            st.markdown(ai_response)
            
        # Add AI response to history
        st.session_state["staff_messages"].append({"role": "ai", "content": ai_response})
        st.rerun() # Rerun to update chat history instantly

st.markdown("---")
st.page_link("app.py", label="🏠 Back to Main Page (Logout)", icon="🚪")