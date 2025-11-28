# Clinic Web Application Portal

A Streamlit-based web application for a clinic, featuring specialized AI chatbots for public inquiries, general health advice, and internal staff management. Powered by [JamAI Base](https://www.jamaibase.com/).

## Features

- **Public Access**:
    - **Clinic FAQs Chatbot**: Answers questions about clinic hours, appointments, and services.
    - **General Health Chatbot**: Provides general information on mild health topics and medication.
- **Staff Access**:
    - **Staff Main Portal**: Secure area for clinic staff.
    - **Staff Management Chatbot**: Assists with internal HR, scheduling, and policy queries.
- **AI Integration**:
    - Connected to JamAI Base for intelligent responses.
    - Real-time chat logging to JamAI Tables with session tracking and user role metadata.

## Prerequisites

- Python 3.8+
- A JamAI Base account with a Project ID and API Key (Personal Access Token).
- A JamAI Chat Table configured (Default ID: `Multilingual_Frontline_Agent`).

## Installation

1.  **Clone the repository** (if applicable) or navigate to the project folder:
    ```bash
    cd UMHACKATHONINTERNAL
    ```

2.  **Create and activate a virtual environment** (optional but recommended):
    ```bash
    python -m venv .venv
    # Windows
    .venv\Scripts\activate
    # Mac/Linux
    source .venv/bin/activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

1.  **API Keys**:
    The application requires your JamAI API Key and Project ID.
    
    *Current Setup*: Credentials are configured in `utils.py`.
    
    *Production Recommendation*: Use Streamlit Secrets.
    - Create a file `.streamlit/secrets.toml`.
    - Add your credentials:
      ```toml
      JAMAI_API_KEY = "your_api_key_here"
      JAMAI_PROJECT_ID = "your_project_id_here"
      ```
    - Update `utils.py` to use `st.secrets["JAMAI_API_KEY"]`.

2.  **JamAI Table Setup**:
    Ensure your JamAI Table (`Multilingual_Frontline_Agent`) has the following columns for logging:
    - `User` (Input)
    - `AI` (Output)
    - `Session ID` (Text)
    - `User Role` (Text)

## Usage

Run the Streamlit application:

```bash
streamlit run app.py
```

The application will open in your default web browser at `http://localhost:8501`.

## Project Structure

```
UMHACKATHONINTERNAL/
├── app.py                  # Main application entry point & navigation
├── utils.py                # Shared utilities & JamAI integration logic
├── requirements.txt        # Python dependencies
├── pages/                  # Streamlit pages
│   ├── public_faq_chat.py  # FAQ Chatbot page
│   ├── public_GK_chat.py   # General Health Chatbot page
│   └── staff_main.py       # Staff Portal & Chatbot page
└── static/                 # Static assets (HTML/CSS/JS)
```
