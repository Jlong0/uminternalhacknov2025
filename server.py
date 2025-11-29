from flask import Flask, request, jsonify, send_from_directory
from utils import delete_table, create_new_chat_table, post_chat_table, get_jam_ai_response, get_chat_history, embed_file_in_jamai
from auth import login_user, sign_up_user, supabase_staff
import os
import json
import tempfile
from datetime import datetime, timedelta

app = Flask(__name__, static_url_path='', static_folder='static')

CONFIG_FILE = 'site_config.json'

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {"banner": {"text": "", "active": False}, "clinic_info": {}}

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

@app.route('/')
def root():
    return send_from_directory('static', 'main_page.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

@app.route('/api/login', methods=['POST'])
def login_endpoint():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    role = data.get('role') # 'patient' or 'staff'

    if not email or not password or not role:
        return jsonify({'success': False, 'message': 'Missing credentials'}), 400

    result = login_user(email, password, role)
    
    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 401

@app.route('/api/signup', methods=['POST'])
def signup_endpoint():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    role = data.get('role') # 'patient' or 'staff'

    if not email or not password or not role:
        return jsonify({'success': False, 'message': 'Missing credentials'}), 400

    result = sign_up_user(email, password, role)
    
    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 400

@app.route('/api/chat', methods=['POST'])
def chat_endpoint():
    data = request.json
    user_message = data.get('message')
    table_id = data.get('table_id')
    ai_type = data.get("ai_type")
    print(ai_type)
    # Context determines if it's 'General Knowledge' (Patient) or 'Staff'
    context = data.get('context', 'General Knowledge') 
    user_email = data.get('userEmail') # Get user email from request
    
    if not user_message:
        return jsonify({'error': 'Message is required'}), 400

    try:
        # Call the existing utility function
        # Generate a simple session ID for Flask requests or use one from the client if sent
        session_id = data.get('sessionId', 'flask_session')
        action_ai_response = get_jam_ai_response(user_message, context, ai_type, session_id=session_id, user_email=user_email)
        if ai_type == "public":
            ai_response = post_chat_table(action_ai_response, ai_type, table_id)
            print(ai_response)
            return jsonify({'response': ai_response})
        elif ai_type == "booking":
            print(action_ai_response)
            return jsonify({'response': action_ai_response})
        elif ai_type == "staff":
            ai_response = post_chat_table(action_ai_response, ai_type, table_id)
            print(ai_response)
            return jsonify({'response': ai_response})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/history', methods=['POST'])
def history_endpoint():
    data = request.json
    current_session = data.get("session")
    print(current_session)

    if not current_session:
        return jsonify({'error': 'Session ID is required'}), 400

    try:
        history = get_chat_history(current_session)
        return jsonify({'history': history})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/api/newChatTable", methods=["POST"])
def new_chat_table_endpoint():
    data = request.json
    base_table_id = data.get("base_table_id")
    user = data.get("user")

    if not base_table_id:
        return {"error": "Missing base_table_id"}, 400

    new_table_id = create_new_chat_table(base_table_id, user)
    print(new_table_id)

    if new_table_id is None:
        return {"error": "Failed to create chat table"}, 500

    return {"table_id": new_table_id, "user": user}


@app.route("/api/deleteChatTable", methods=["DELETE"])
def delete_chat_endpoint():
    data = request.json
    current_session = data.get('session')
    user = current_session.get('user')
    table_id = current_session.get('table_id')

    if not table_id:
        return {"error": "Missing table_id"}, 400

    try:
        success = delete_table("chat", table_id, user)  # Your function to delete the table
        if not success:
            return {"error": "Failed to delete chat table"}, 500

        return {"message": f"Chat table {table_id} deleted successfully."}, 200

    except Exception as e:
        return {"error": f"Exception occurred: {str(e)}"}, 500


@app.route('/api/config', methods=['GET', 'POST'])
def config_endpoint():
    if request.method == 'GET':
        return jsonify(load_config())
    
    elif request.method == 'POST':
        new_config = request.json
        current_config = load_config()
        
        # Update only provided keys
        if 'clinic_name' in new_config:
            current_config['clinic_name'] = new_config['clinic_name']
        if 'banner' in new_config:
            current_config['banner'] = new_config['banner']
        if 'clinic_info' in new_config:
            current_config['clinic_info'] = new_config['clinic_info']
        if 'hero' in new_config:
            current_config['hero'] = new_config['hero']
        if 'value_props' in new_config:
            current_config['value_props'] = new_config['value_props']
            
        save_config(current_config)
        return jsonify({'success': True, 'config': current_config})

@app.route('/api/bookings', methods=['GET'])
def get_bookings_endpoint():
    date = request.args.get('date')
    if not date:
        return jsonify({'success': False, 'message': 'Date is required'}), 400
    
    try:
        # Fetch bookings for the specific date
        if supabase_staff:
            response = supabase_staff.table('Booking').select('appoinment_time').eq('Date', date).execute()
            booked_times = [item['appoinment_time'] for item in response.data]
            return jsonify({'success': True, 'bookedTimes': booked_times})
        else:
             return jsonify({'success': False, 'message': 'Database not configured'}), 500
    except Exception as e:
        print(f"Fetch Bookings Error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/book', methods=['POST'])
def book_endpoint():
    data = request.json
    doctor_name = data.get('doctorName')
    date = data.get('date')
    time = data.get('time')
    patient_email = data.get('patientEmail')
    reason = data.get('reason')

    if not doctor_name or not date or not time:
        return jsonify({'success': False, 'message': 'Missing booking details'}), 400

    try:
        # Prepare data for Supabase
        # Columns based on user input: appoinment_id, appoinment_time, patient_name, doctor_name, Date
        booking_data = {
            "doctor_name": doctor_name,
            "patient_name": patient_email, # Using email as name
            "appoinment_time": time,
            "Date": date # Assuming the column name is 'Date' as specified
        }
        
        # Try to insert
        if supabase_staff:
            response = supabase_staff.table('Booking').insert(booking_data).execute()
            return jsonify({'success': True, 'data': response.data})
        else:
            return jsonify({'success': False, 'message': 'Database not configured'}), 500

    except Exception as e:
        print(f"Booking Error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    selected_upload_mode = request.form.get('selectedUploadMode')
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    if file:
        try:
            # Create a temporary file to save the uploaded content
            # We need to preserve the extension for JamAI to know the file type
            suffix = os.path.splitext(file.filename)[1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                file.save(tmp.name)
                tmp_path = tmp.name
                
            # Embed the file
            # Note: You might want to use different tables for staff vs patient if needed
            # We use the 'Uploaded' Knowledge Table for file storage
            response = embed_file_in_jamai(tmp_path, selected_upload_mode)
            
            # Clean up the temp file
            os.unlink(tmp_path)
            
            return jsonify({'success': True, 'message': f'File {file.filename} uploaded and embedded successfully.'})
            
        except Exception as e:
            # Clean up if something fails
            if 'tmp_path' in locals() and os.path.exists(tmp_path):
                os.unlink(tmp_path)
            return jsonify({'error': str(e)}), 500

@app.route('/api/doctors', methods=['GET', 'POST'])
def doctors_endpoint():
    if request.method == 'GET':
        if not supabase_staff:
            return jsonify({'success': False, 'message': 'Database not configured'}), 500
        try:
            response = supabase_staff.table('DutyList').select("*").execute()
            return jsonify({'success': True, 'doctors': response.data})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    elif request.method == 'POST':
        data = request.json
        doctor_name = data.get('doctorName')
        specialty = data.get('specialty')
        date = data.get('date')
        start_time = data.get('startTime')
        end_time = data.get('endTime')
        
        if not doctor_name or not date or not start_time or not end_time:
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400
            
        try:
            # Insert into DutyList
            # Columns: doctor_name, date, time_start, time_end
            
            # Append specialty to name if provided, as there is no column for it
            final_name = doctor_name
            if specialty:
                final_name = f"{doctor_name} ({specialty})"

            new_doctor = {
                "doctor_name": final_name,
                "date": date,
                "time_start": start_time,
                "time_end": end_time
            }
            
            if supabase_staff:
                response = supabase_staff.table('DutyList').insert(new_doctor).execute()
                return jsonify({'success': True, 'data': response.data})
            else:
                return jsonify({'success': False, 'message': 'Database not configured'}), 500
                
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/dashboard', methods=['GET'])
def dashboard_endpoint():
    if not supabase_staff:
        return jsonify({'success': False, 'message': 'Database not configured'}), 500
    
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        
        # 1. Fetch Today's Appointments
        # We need full details for the list
        response_today = supabase_staff.table('Booking').select("*").eq('Date', today).execute()
        today_appointments = response_today.data
        
        # 2. Calculate Stats
        
        # Stat: Today's Appointments Count
        count_today = len(today_appointments)
        
        # Stat: Patients This Week
        # Calculate start of week (Monday)
        dt_today = datetime.now()
        start_of_week = (dt_today - timedelta(days=dt_today.weekday())).strftime('%Y-%m-%d')
        end_of_week = (dt_today + timedelta(days=6-dt_today.weekday())).strftime('%Y-%m-%d')
        
        # Fetch bookings for this week to count unique patients
        # Note: Supabase 'gte' and 'lte' for date range
        response_week = supabase_staff.table('Booking').select("patient_name").gte('Date', start_of_week).lte('Date', end_of_week).execute()
        
        unique_patients = set()
        for booking in response_week.data:
            if booking.get('patient_name'):
                unique_patients.add(booking['patient_name'])
        
        count_patients_week = len(unique_patients)
        
        # Stat: Average Wait Time (Mocked for now as we don't have arrival times)
        # In a real app, you'd diff 'arrival_time' and 'appointment_time'
        avg_wait_time = "8 min" 

        return jsonify({
            'success': True,
            'stats': {
                'todayAppointments': count_today,
                'patientsThisWeek': count_patients_week,
                'avgWaitTime': avg_wait_time
            },
            'appointments': today_appointments
        })

    except Exception as e:
        print(f"Dashboard Error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/appointments', methods=['GET', 'DELETE', 'PUT'])
def appointments_endpoint():
    if not supabase_staff:
        return jsonify({'success': False, 'message': 'Database not configured'}), 500

    if request.method == 'GET':
        date = request.args.get('date')
        if not date:
            return jsonify({'success': False, 'message': 'Date is required'}), 400
        
        try:
            response = supabase_staff.table('Booking').select("*").eq('Date', date).execute()
            return jsonify({'success': True, 'appointments': response.data})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    elif request.method == 'DELETE':
        data = request.json
        # Identify booking by composite key since we might not have ID on frontend easily without fetching first
        # Or we can pass ID if we fetch it in GET. Let's assume we fetch ID in GET.
        booking_id = data.get('id')
        
        try:
            if booking_id:
                response = supabase_staff.table('Booking').delete().eq('id', booking_id).execute()
            else:
                # Fallback to composite key
                doctor_name = data.get('doctor_name')
                date = data.get('date')
                time = data.get('time')
                if not doctor_name or not date or not time:
                     return jsonify({'success': False, 'message': 'Missing booking identifier'}), 400
                
                response = supabase_staff.table('Booking').delete().eq('doctor_name', doctor_name).eq('Date', date).eq('appoinment_time', time).execute()
            
            return jsonify({'success': True, 'data': response.data})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    elif request.method == 'PUT':
        data = request.json
        booking_id = data.get('id')
        new_date = data.get('newDate')
        new_time = data.get('newTime')
        
        if not booking_id or not new_date or not new_time:
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400
            
        try:
            response = supabase_staff.table('Booking').update({
                'Date': new_date,
                'appoinment_time': new_time
            }).eq('id', booking_id).execute()
            
            return jsonify({'success': True, 'data': response.data})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/patient_history', methods=['GET'])
def patient_history_endpoint():
    email = request.args.get('email')
    if not email:
        return jsonify({'success': False, 'message': 'Email is required'}), 400
    
    if not supabase_staff:
        return jsonify({'success': False, 'message': 'Database not configured'}), 500

    try:
        # Fetch bookings for the specific patient
        # Assuming 'patient_name' column stores the email as per book_endpoint logic
        response = supabase_staff.table('Booking').select("*").eq('patient_name', email).execute()
        return jsonify({'success': True, 'appointments': response.data})
    except Exception as e:
        print(f"Patient History Error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

if __name__ == '__main__':
    print("Starting ClinicConnect Server...")
    print("Go to http://localhost:5001 to see your new app!")
    app.run(debug=True, port=5001)
