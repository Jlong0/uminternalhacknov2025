import streamlit as st
from utils import JAMAI_PROJECT_ID, get_jam_ai_response
import uuid

# --- Streamlit Session State Initialization ---

# Initialize state variables
if 'is_staff' not in st.session_state:
    st.session_state['is_staff'] = False

# Initialize Session ID for JamAI logging
if 'session_id' not in st.session_state:
    st.session_state['session_id'] = str(uuid.uuid4())

# Initialize chat message histories (needed here for pages to access state on first run)
if 'staff_messages' not in st.session_state:
    st.session_state['staff_messages'] = [{"role": "ai", "content": "Hello Staff! How can I help you with your management queries today?"}]
if 'faq_messages' not in st.session_state:
    st.session_state['faq_messages'] = [{"role": "ai", "content": "Hello! I'm the FAQ bot. How can I help you with clinic services today?"}]
if 'gk_messages' not in st.session_state:
    st.session_state['gk_messages'] = [{"role": "ai", "content": "I can provide general knowledge on mild health topics. **Note: I am not a substitute for a doctor's advice.**"}]


# --- Main Application Page ---

st.set_page_config(
    page_title="Clinic Portal",
    layout="centered"
)

st.title("🏥 Clinic Web Application Portal")
st.subheader("Welcome! Please select your access type.")

st.markdown("---")

## 👥 Public Access (No Login)

st.write("Click below for direct access to our specialized public chatbots:")
col1, col2 = st.columns(2)

with col1:
    st.page_link("pages/public_faq_chat.py", label="📚 Clinic FAQs Chatbot", icon="📚", use_container_width=True)

with col2:
    st.page_link("pages/public_gk_chat.py", label="💊 General Health Chatbot", icon="💊", use_container_width=True)

st.markdown("---")

## 🧑‍⚕️ Clinic Staff Login

if st.session_state['is_staff']:
    st.success("You are currently logged in as Staff.")
    st.page_link("pages/staff_main.py", label="➡️ Go to Staff Main Portal", icon="🔐", use_container_width=True)
    if st.button("🚪 Logout"):
        st.session_state['is_staff'] = False
        st.rerun()

else:
    st.write("Enter mock credentials (staff/123) to access the Staff Portal.")
    
    username = st.text_input("Username", key="login_user")
    password = st.text_input("Password", type="password", key="login_pass")
    
    if st.button("Login", use_container_width=True):
        # Mock Validation
        if username == "staff" and password == "123":
            st.session_state['is_staff'] = True
            st.success("Login successful! Click the button above to proceed.")
            st.rerun()
        else:
            st.session_state['is_staff'] = False
            st.error("Invalid Username or Password. (Hint: staff/123)")

st.markdown("---")
st.caption("Application powered by Streamlit and JAM AI.")