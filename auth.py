import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
print(f"DEBUG: Current CWD: {os.getcwd()}")
load_dotenv()

# Initialize Supabase Client
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

# Staff Supabase Client
staff_url: str = os.environ.get("SUPABASE_STAFF_URL")
staff_key: str = os.environ.get("SUPABASE_STAFF_KEY")

print(f"DEBUG: SUPABASE_URL from env: {url}")
print(f"DEBUG: SUPABASE_KEY from env: {'Found' if key else 'Not Found'}")
print(f"DEBUG: SUPABASE_STAFF_URL from env: {staff_url}")

supabase: Client = None
supabase_staff: Client = None

if url and key and "your-project" not in url:
    try:
        supabase = create_client(url, key)
        print("DEBUG: Supabase client (Patient) initialized successfully.")
    except Exception as e:
        print(f"Failed to initialize Supabase client (Patient): {e}")
else:
    print("DEBUG: Supabase config (Patient) missing or invalid.")

if staff_url and staff_key:
    try:
        supabase_staff = create_client(staff_url, staff_key)
        print("DEBUG: Supabase client (Staff) initialized successfully.")
    except Exception as e:
        print(f"Failed to initialize Supabase client (Staff): {e}")
else:
    print("DEBUG: Supabase config (Staff) missing.")

def login_user(email, password, role):
    """
    Verifies user credentials using Supabase Auth.
    """
    # Select the correct client based on role
    client = supabase_staff if role == 'staff' else supabase
    
    if not client:
        return {"success": False, "message": f"Supabase not configured for {role}."}

    try:
        # Sign in with Supabase Auth
        response = client.auth.sign_in_with_password({
            "email": email, 
            "password": password
        })
        
        user = response.user
        session = response.session
        
        if user:
            # Optional: Check role if you have it stored in user_metadata or a separate table
            # For now, we'll assume if they can log in, they are valid.
            # You could add a check like: if user.user_metadata.get('role') != role: ...
            
            return {
                "success": True, 
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "role": role, # Returning the requested role for now
                    "access_token": session.access_token
                }
            }
        else:
            return {"success": False, "message": "Login failed"}

    except Exception as e:
        return {"success": False, "message": str(e)}

def sign_up_user(email, password, role):
    """
    Registers a new user.
    """
    # Select the correct client based on role
    client = supabase_staff if role == 'staff' else supabase

    if not client:
        return {"success": False, "message": f"Supabase not configured for {role}."}
        
    try:
        response = client.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": {
                    "role": role
                }
            }
        })
        
        if response.user:
             return {"success": True, "message": "User created. Please check email for confirmation."}
        return {"success": False, "message": "Signup failed"}
        
    except Exception as e:
        return {"success": False, "message": str(e)}
