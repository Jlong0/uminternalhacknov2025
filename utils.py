import streamlit as st
import requests
from jamaibase import JamAI, protocol
from auth import supabase_staff
import os
import tempfile
import json, uuid
import re
from datetime import datetime, timedelta

# --- Configuration & Mock JAM AI Integration ---

# WARNING: In a production environment, NEVER expose API keys directly in client-side code.
# Use environment variables (st.secrets) and a secure backend for actual API calls.
JAMAI_API_KEY_PUBLIC = "jamai_pat_0b56222ffbb0652e9f0d94e251b5764fa3235afdb2300455"
JAMAI_PROJECT_ID_PUBLIC = "proj_61fc83a49e0b5b9d0a328a0c"

JAMAI_API_KEY_BOOKING = "jamai_pat_9a59c8a18706c2ece413173bad6e972ed66505b90d9c3e90"
JAMAI_PROJECT_ID_BOOKING = "proj_06f08ce75d8309594310ba5b"

JAMAI_API_KEY_STAFF = "jamai_pat_62ed5e0b58887133f89adf908674e8a3c6bfa022613ecdde"
JAMAI_PROJECT_ID_STAFF = "proj_f53f079883ae56c0170ab5dd"

#JAMAI_TABLE_ID = "SOP_action_V3" # The ID of your JamAI Action Table
#JAMAI_KNOWLEDGE_TABLE_ID = "SOP Medical Assistant In Primary Health Care Part 3" # The ID of your JamAI Knowledge Table

# Initialize JamAI client
# Note: The SDK uses 'token' instead of 'api_key' in newer versions, but we'll use what works.
# Based on inspection, it seems 'token' is the correct argument name for the init.
jamai_client_public = JamAI(token=JAMAI_API_KEY_PUBLIC, project_id=JAMAI_PROJECT_ID_PUBLIC)
jamai_client_booking = JamAI(token=JAMAI_API_KEY_BOOKING, project_id=JAMAI_PROJECT_ID_BOOKING)
jamai_client_staff = JamAI(token=JAMAI_API_KEY_STAFF, project_id=JAMAI_PROJECT_ID_STAFF)

def get_duty_list_context():
    """Fetches and formats the duty list from Supabase."""
    if not supabase_staff:
        return ""
    try:
        response = supabase_staff.table('DutyList').select("*").execute()
        if not response.data:
            return ""
        
        context = "\n\n--- CURRENT CLINIC DUTY LIST ---\n"
        for row in response.data:
            # Format each row as a readable string
            # e.g. {'doctor_name': 'Dr. Smith', 'day': 'Monday'} -> "doctor_name: Dr. Smith, day: Monday"
            row_str = ", ".join([f"{k}: {v}" for k, v in row.items()])
            context += f"- {row_str}\n"
        context += "--------------------------------\n"
        return context
    except Exception as e:
        print(f"Error fetching duty list: {e}")
        return ""

def get_booking_list_context(role="Public", user_email=None):
    """Fetches and formats the booking list from Supabase."""
    if not supabase_staff:
        return ""
    try:
        # Fetch bookings
        # For Staff: Fetch all upcoming bookings
        # For Public: Fetch only their bookings if email is provided
        
        query = supabase_staff.table('Booking').select("*")
        
        # Filter for upcoming bookings (today onwards)
        today = datetime.now().strftime('%Y-%m-%d')
        query = query.gte('Date', today)
        
        if role == "Public" and user_email:
            # Filter by patient email/name
            # Note: The column is 'patient_name' but we store email there in book_endpoint
            query = query.eq('patient_name', user_email)
        elif role == "Public" and not user_email:
            # If public and no email, return nothing to avoid leaking info
            return ""
            
        response = query.execute()
        
        if not response.data:
            return ""
        
        context = "\n\n--- UPCOMING BOOKINGS ---\n"
        for row in response.data:
            # Format: Date: YYYY-MM-DD, Time: HH:MM, Doctor: Name, Patient: Name (if staff)
            row_str = f"Date: {row.get('Date')}, Time: {row.get('appoinment_time')}, Doctor: {row.get('doctor_name')}"
            if role == "Staff":
                row_str += f", Patient: {row.get('patient_name')}"
            context += f"- {row_str}\n"
        context += "-------------------------\n"
        return context
    except Exception as e:
        print(f"Error fetching booking list: {e}")
        return ""

def create_booking(doctor_name, date, time, patient_email):
    """Creates a new booking in the Supabase database."""
    if not supabase_staff:
        return {'success': False, 'message': 'Database connection not available.'}
    
    try:
        # Basic validation
        if not doctor_name or not date or not time:
            return {'success': False, 'message': 'Missing required booking details.'}

        booking_data = {
            "doctor_name": doctor_name,
            "patient_name": patient_email or "Guest",
            "appoinment_time": time,
            "Date": date
        }
        response = supabase_staff.table('Booking').insert(booking_data).execute()
        return {'success': True, 'data': response.data}
    except Exception as e:
        print(f"Create Booking Error: {e}")
        return {'success': False, 'message': str(e)}

def cancel_booking(doctor_name, date, time, patient_email):
    """Cancels a booking in the Supabase database."""
    if not supabase_staff:
        return {'success': False, 'message': 'Database connection not available.'}
    
    try:
        # Basic validation
        if not doctor_name or not date or not time:
            return {'success': False, 'message': 'Missing required booking details to identify the appointment.'}

        # Delete the booking matching the criteria
        # Note: We use patient_email to ensure users can only cancel their own bookings (if provided)
        query = supabase_staff.table('Booking').delete().eq('doctor_name', doctor_name).eq('Date', date).eq('appoinment_time', time)
        
        if patient_email:
            query = query.eq('patient_name', patient_email)
            
        response = query.execute()
        
        # Check if any row was actually deleted
        if response.data and len(response.data) > 0:
            return {'success': True, 'data': response.data}
        else:
            return {'success': False, 'message': 'No matching booking found to cancel.'}
            
    except Exception as e:
        print(f"Cancel Booking Error: {e}")
        return {'success': False, 'message': str(e)}

def upload_file_to_jamai(file_path):
    try:
        response = jamai_client_public.file.upload_file(
            file_path=file_path,
        )
        return response.uri
    except Exception as e:
        print(f"Error embedding file: {e}")
        raise e

def upload_doc(url):
    try:
        completion = jamai_client_public.table.add_table_rows(
            table_type="action",
            request=protocol.MultiRowAddRequest(
                table_id="FAQ",
                data=[{"doc_input": url}],
                stream=False  # We wait for the full response for simplicity in this Streamlit app
            )
        )

        # The response structure for add_table_rows (non-streaming) contains the rows.
        # We need to extract the AI's response from the output column.
        # Assuming the output column is named 'AI' based on standard JamAI chat tables.

        if completion.rows and len(completion.rows) > 0:
            # Get the first row's columns
            row_columns = completion.rows[0].columns

            # Debugging: Print received columns to console
            print(f"DEBUG: Received columns from JamAI: {list(row_columns.keys())}")

            # Find the 'AI' column or the last column which usually contains the response
            if "user_output" in row_columns:

                ai_response = row_columns["user_output"].text
            else:
                # Fallback: return the text of the last column
                ai_response = list(row_columns.values())[-1].text

            return f"User: {url}\n Action Table: {ai_response}"

    except Exception as e:
        return f"Error connecting to JamAI: {str(e)}"


def get_jam_ai_response(user_message, model_context, ai_type, session_id=None, user_email=None):
    """
    Function to call the JAM AI API using the Table interface.
    This ensures we use the specific project/table configuration (models, prompts) you built in JamAI.
    """
    try:
        # We use the 'add_table_rows' method to send the user message to the table.
        # This triggers the AI column generation based on your table's configuration.
        
        # Retrieve session_id from Streamlit state if available and not provided
        if session_id is None:
            try:
                session_id = st.session_state.get('session_id', 'unknown_session')
            except:
                session_id = 'external_session'
        
        # Determine User Role based on context or state
        user_role = "Public"
        if "staff" in model_context.lower():
            user_role = "Staff"
        
        # Fetch Duty List Context
        duty_context = get_duty_list_context()
        
        # Fetch Booking List Context
        booking_context = get_booking_list_context(user_role, user_email)
        
        # Combine User Message with Context
        # We append it so the AI sees it. 
        # Note: This will appear in the 'User' column of your JamAI table.
        full_message = user_message + (duty_context or "") + (booking_context or "") + """
            SYSTEM INSTRUCTION:
            You have the ability to book and cancel appointments directly in the database.

            1. BOOKING:
            If the user explicitly asks to book an appointment and provides ALL the following details:
            - Doctor Name
            - Date (YYYY-MM-DD format preferred, convert if necessary)
            - Time (HH:MM format)

            Then, output a JSON block EXACTLY like this:
            ```json
            {
                "action": "book_appointment",
                "doctor_name": "Dr. Name",
                "date": "YYYY-MM-DD",
                "time": "HH:MM"
            }
            ```

            2. CANCELLATION:
            If the user explicitly asks to CANCEL an appointment and provides ALL the following details:
            - Doctor Name
            - Date (YYYY-MM-DD format preferred)
            - Time (HH:MM format)

            Then, output a JSON block EXACTLY like this:
            ```json
            {
                "action": "cancel_appointment",
                "doctor_name": "Dr. Name",
                "date": "YYYY-MM-DD",
                "time": "HH:MM"
            }
            ```

            If any detail is missing for either action, ask the user for it. Do not output the JSON until you have all 3 details.
            """

        # Prepare row data with metadata for logging
        row_data = {
            "User": full_message,
            "Session ID": session_id,
            "User Role": user_role
        }

        # Add User Email if provided
        if user_email:
            row_data["User Email"] = user_email
        
        # Debugging: Print data being sent
        # print(f"DEBUG: Sending row data to JamAI: {row_data}")

        if ai_type == "public":
            completion = jamai_client_public.table.add_table_rows(
                table_type="action",
                request=protocol.MultiRowAddRequest(
                    table_id="FAQ",
                    data=[{"usr_input": user_message}],
                    stream=False  # We wait for the full response for simplicity in this Streamlit app
                )
            )

            # The response structure for add_table_rows (non-streaming) contains the rows.
            # We need to extract the AI's response from the output column.
            # Assuming the output column is named 'AI' based on standard JamAI chat tables.

            if completion.rows and len(completion.rows) > 0:
                # Get the first row's columns
                row_columns = completion.rows[0].columns

                # Debugging: Print received columns to console
                print(f"DEBUG: Received columns from JamAI: {list(row_columns.keys())}")

                # Find the 'AI' column or the last column which usually contains the response
                if "user_output" in row_columns:

                    ai_response = row_columns["user_output"].text
                else:
                    # Fallback: return the text of the last column
                    ai_response = list(row_columns.values())[-1].text

                # # --- ACTION PARSING LOGIC ---
                # # Check if the AI wants to perform an action (Book Appointment)
                # json_match = re.search(r'```json\s*({.*?})\s*```', ai_response, re.DOTALL)
                # if json_match:
                #     try:
                #         data = json.loads(json_match.group(1))
                #         action = data.get('action')
                #
                #         if action == 'book_appointment':
                #             print(f"DEBUG: AI triggered booking action: {data}")
                #
                #             # Execute the booking
                #             result = create_booking(
                #                 doctor_name=data.get('doctor_name'),
                #                 date=data.get('date'),
                #                 time=data.get('time'),
                #                 patient_email=user_email
                #             )
                #
                #             if result['success']:
                #                 return f"✅ Success! I have booked your appointment with **{data.get('doctor_name')}** on **{data.get('date')}** at **{data.get('time')}**."
                #             else:
                #                 return f"❌ I tried to book that for you, but the system returned an error: {result['message']}"
                #
                #         elif action == 'cancel_appointment':
                #             print(f"DEBUG: AI triggered cancellation action: {data}")
                #
                #             # Execute the cancellation
                #             result = cancel_booking(
                #                 doctor_name=data.get('doctor_name'),
                #                 date=data.get('date'),
                #                 time=data.get('time'),
                #                 patient_email=user_email
                #             )
                #
                #             if result['success']:
                #                 return f"✅ Success! I have cancelled your appointment with **{data.get('doctor_name')}** on **{data.get('date')}** at **{data.get('time')}**."
                #             else:
                #                 return f"❌ I tried to cancel that for you, but I couldn't find a matching booking or an error occurred: {result['message']}"
                #
                #     except Exception as e:
                #         print(f"Error parsing AI action: {e}")
                #         # If parsing fails, just return the original text (maybe the AI messed up the JSON)
                #         return ai_response

                print(ai_response)
                return f"User: {user_message}\n Action Table: {ai_response}"
        elif ai_type == "booking":

            completion = jamai_client_booking.table.add_table_rows(
                table_type="chat",
                request=protocol.MultiRowAddRequest(
                    table_id="test2",
                    data=[{"User": full_message}],
                    stream=False  # We wait for the full response for simplicity in this Streamlit app
                )
            )

            if completion.rows and len(completion.rows) > 0:
                # Get the first row's columns
                row_columns = completion.rows[0].columns

                # Debugging: Print received columns to console
                print(f"DEBUG: Received columns from JamAI: {list(row_columns.keys())}")

                # Find the 'AI' column or the last column which usually contains the response
                if "AI" in row_columns:
                    ai_response = row_columns["AI"].text
                else:
                    # Fallback: return the text of the last column
                    ai_response = list(row_columns.values())[-1].text


                # --- ACTION PARSING LOGIC ---
                # Check if the AI wants to perform an action (Book Appointment)
                json_match = re.search(r'```json\s*({.*?})\s*```', ai_response, re.DOTALL)
                if json_match:
                    try:
                        data = json.loads(json_match.group(1))
                        action = data.get('action')

                        if action == 'book_appointment':
                            print(f"DEBUG: AI triggered booking action: {data}")

                            # Execute the booking
                            result = create_booking(
                                doctor_name=data.get('doctor_name'),
                                date=data.get('date'),
                                time=data.get('time'),
                                patient_email=user_email
                            )

                            if result['success']:
                                return f"✅ Success! I have booked your appointment with **{data.get('doctor_name')}** on **{data.get('date')}** at **{data.get('time')}**."
                            else:
                                return f"❌ I tried to book that for you, but the system returned an error: {result['message']}"

                        elif action == 'cancel_appointment':
                            print(f"DEBUG: AI triggered cancellation action: {data}")

                            # Execute the cancellation
                            result = cancel_booking(
                                doctor_name=data.get('doctor_name'),
                                date=data.get('date'),
                                time=data.get('time'),
                                patient_email=user_email
                            )

                            if result['success']:
                                return f"✅ Success! I have cancelled your appointment with **{data.get('doctor_name')}** on **{data.get('date')}** at **{data.get('time')}**."
                            else:
                                return f"❌ I tried to cancel that for you, but I couldn't find a matching booking or an error occurred: {result['message']}"

                    except Exception as e:
                        print(f"Error parsing AI action: {e}")
                        # If parsing fails, just return the original text (maybe the AI messed up the JSON)
                        return ai_response

                return ai_response

        elif ai_type == "staff":
            completion = jamai_client_staff.table.add_table_rows(
                table_type="action",
                request=protocol.MultiRowAddRequest(
                    table_id="SOP_action_V3",
                    data=[{"User": user_message}],
                    stream=False  # We wait for the full response for simplicity in this Streamlit app
                )
            )

            if completion.rows and len(completion.rows) > 0:
                # Get the first row's columns
                row_columns = completion.rows[0].columns

                # Debugging: Print received columns to console
                print(f"DEBUG: Received columns from JamAI: {list(row_columns.keys())}")

                # Find the 'AI' column or the last column which usually contains the response
                if "Final_OUTPUT" in row_columns:
                    ai_response = row_columns["Final_OUTPUT"].text
                else:
                    # Fallback: return the text of the last column
                    ai_response = list(row_columns.values())[-1].text

                return f"User: {user_message}\n Action Table: {ai_response}"

        else:
            return "Error: No response received from JamAI Table."

    except Exception as e:
        return f"Error connecting to JamAI: {str(e)}"

def post_chat_table(user_message, user, table_id):

    try:

        # # Determine User Role based on context or state
        # user_role = "Public"
        # if "staff" in model_context.lower():
        #     user_role = "Staff"

        # # Prepare row data with metadata for logging
        # row_data = {
        #     "User": user_message,
        #     "Session ID": session_id,
        #     "User Role": user_role
        # }

        # Debugging: Print data being sent
        print(f"DEBUG chat: Sending row data to JamAI: {user_message}")

        completion = None

        if user == "staff":
            completion = jamai_client_staff.table.add_table_rows(
                table_type="chat",
                request=protocol.MultiRowAddRequest(
                    table_id=table_id,
                    data=[{"User": user_message}],
                    stream=False  # We wait for the full response for simplicity in this Streamlit app
                )
            )
        elif user == "public":
            completion = jamai_client_public.table.add_table_rows(
                table_type="chat",
                request=protocol.MultiRowAddRequest(
                    table_id=table_id,
                    data=[{"User": user_message}],
                    stream=False  # We wait for the full response for simplicity in this Streamlit app
                )
            )

        # The response structure for add_table_rows (non-streaming) contains the rows.
        # We need to extract the AI's response from the output column.
        # Assuming the output column is named 'AI' based on standard JamAI chat tables.

        if completion.rows and len(completion.rows) > 0:
            # Get the first row's columns
            row_columns = completion.rows[0].columns

            # Debugging: Print received columns to console
            print(f"DEBUG: Received columns from JamAI: {list(row_columns.keys())}")

            # Find the 'AI' column or the last column which usually contains the response
            if "AI" in row_columns:
                return list(row_columns.values())[0].text
            else:
                # Fallback: return the text of the last column
                return list(row_columns.values())[-1].text
        else:
            return "Error: No response received from JamAI Table."

    except Exception as e:
        return f"Error connecting to JamAI: {str(e)}"

def create_new_chat_table(table_id_src, user):
    new_table_id = f"chat_{str(uuid.uuid4())[:8]}"

    try:
        if user == "staff":
            jamai_client_staff.table.duplicate_table(
                table_type="chat",
                table_id_src=table_id_src,  # Your base agent ID
                table_id_dst=new_table_id,
                include_data=True,
                create_as_child=True
            )
        elif user == "public":
            jamai_client_public.table.duplicate_table(
                table_type="chat",
                table_id_src=table_id_src,  # Your base agent ID
                table_id_dst=new_table_id,
                include_data=True,
                create_as_child=True
            )
        return new_table_id
    except Exception as e:
        print(f"Error creating new chat: {str(e)}")
        return None

def delete_table(table_type, table_id, user):
    try:
        if user == "staff":
            jamai_client_staff.table.delete_table(
                table_type=table_type,
                table_id=table_id,
            )
            return True
        elif user == "public":
            jamai_client_public.table.delete_table(
                table_type=table_type,
                table_id=table_id,
            )
            return True
        else:
            print("unable to delete")
            return False
    except Exception as e:
        print(f"Error deleting chat: {str(e)}")
        return False


def check_staff_login():
    """Checks if the user is logged in as staff and redirects if not."""
    if 'is_staff' not in st.session_state or not st.session_state['is_staff']:
        st.warning("Please log in as a staff member on the main page to access this portal.")
        # Streamlit multi-page structure handles the "redirection" by just showing the warning 
        # and stopping the rest of the page from executing.
        st.stop()

def get_chat_history(current_session):
    """
    Fetches chat history for a specific session from the JamAI Table.
    """
    try:
        session_id = current_session.get("id")
        table_id = current_session.get("table_id")
        user = current_session.get("user")
        print(f"DEBUG: Fetching history for session_id: '{session_id}'")
        
        all_items = []
        offset = 0
        limit = 100
        max_pages = 30 # Fetch up to 3000 rows

        if user == "staff":
            for _ in range(max_pages):
                response = jamai_client_staff.table.list_table_rows(
                    table_type="chat",
                    table_id=table_id,
                    limit=limit,
                    offset=offset
                )

                if not response.items:
                    break

                all_items.extend(response.items)

                if len(response.items) < limit:
                    break

                offset += limit
        elif user == "public":
            for _ in range(max_pages):
                response = jamai_client_public.table.list_table_rows(
                    table_type="chat",
                    table_id=table_id,
                    limit=limit,
                    offset=offset
                )

                if not response.items:
                    break

                all_items.extend(response.items)

                if len(response.items) < limit:
                    break

                offset += limit
        
        history = []
        if all_items:
            print(f"DEBUG: Found {len(all_items)} total rows in table.")
            
            for row in all_items:
                print(row)
                # Handle row being a dict (newer SDK) or object (older SDK)
                if isinstance(row, dict):
                    columns = row
                    # Helper to get text value from column dict
                    def get_text(col_name):
                        if col_name in columns:
                            col_data = columns[col_name]
                            if isinstance(col_data, dict) and 'value' in col_data:
                                return col_data['value']
                            return str(col_data)
                        return ""

                    def extract_user_message(text):
                        """
                        Extracts the part between 'User:' and 'Action Table:' and strips whitespace/brackets.
                        """
                        match = re.search(r'User:\s*(.*?)\s*Action Table:', text)
                        if match:
                            return match.group(1).strip()
                        return text  # fallback to full text if pattern not found

                    # Safe timestamp extraction for dict
                    def get_timestamp():
                        if 'Updated at' in row:
                            return str(row['Updated at'])
                        if 'Created at' in row:
                            return str(row['Created at'])
                        return "Unknown Time"

                else:
                    columns = row.columns
                    def get_text(col_name):
                        if col_name in columns:
                            return columns[col_name].text
                        return ""
                    
                    # Safe timestamp extraction for object
                    def get_timestamp():
                        if hasattr(row, 'updated_at') and row.updated_at:
                            return str(row.updated_at)
                        if hasattr(row, 'created_at') and row.created_at:
                            return str(row.created_at)
                        return "Unknown Time"

                # Check if 'Session ID' column exists
                # For dicts, we check keys. For objects, we check .columns keys
                # has_session_id = "Session ID" in columns if isinstance(columns, dict) else "Session ID" in columns
                
                #if has_session_id:
                #    row_session_id = get_text("Session ID")
                #
                #    # Strict string comparison with stripping
                #    if row_session_id and str(row_session_id).strip() == str(session_id).strip():
                raw_text = get_text("User")
                user_text = extract_user_message(raw_text)
                ai_text = get_text("AI")
                timestamp = get_timestamp()

                # Add User Message
                if user_text:
                    history.append({
                        "role": "user",
                        "content": user_text,
                        "timestamp": timestamp
                    })
                # Add AI Message
                if ai_text:
                    history.append({
                        "role": "assistant",
                        "content": ai_text,
                        "timestamp": timestamp
                    })
            
            # Sort by timestamp to ensure correct order (oldest first)
            history.sort(key=lambda x: x['timestamp'])
            print(f"DEBUG: Found {len(history)} messages for this session.")
            
        return history

    except Exception as e:
        print(f"Error fetching history: {e}")
        # Return a system error message so the user knows something went wrong
        return [{
            "role": "assistant",
            "content": f"⚠️ **Connection Error**: Could not load chat history. The server returned: *{str(e)}*. Please check your API key or internet connection.",
            "timestamp": "System"
        }]

def embed_file_in_jamai(file_path, selected_upload_mode):
    """
    Embeds a file into a JamAI table.
    """
    try:
        response = None
        if selected_upload_mode == "staff":
            response = jamai_client_staff.table.embed_file(
                file_path=file_path,
                table_id="Uploaded",
            )
        elif selected_upload_mode == "public":
            response = jamai_client_public.table.embed_file(
                file_path=file_path,
                table_id="Uploaded",
            )
        return response
    except Exception as e:
        print(f"Error embedding file: {e}")
        raise e