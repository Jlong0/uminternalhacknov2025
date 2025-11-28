function mockLogin(event) {
    event.preventDefault(); // Stop the form from submitting normally
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const message = document.getElementById('message');
    
    // Mock Validation: Hardcoded credentials
    if (username === "staff" && password === "123") {
        message.style.color = 'green';
        message.textContent = "Login Successful! Redirecting to Staff Portal...";
        // In a real scenario, this would redirect to the Streamlit staff page
        // For now, it stays for demonstration.
        // window.location.href = 'staff_main_streamlitaspx'; // Example redirect
        return true; 
    } else {
        message.style.color = 'red';
        message.textContent = "Invalid Credentials. Please try again.";
        return false;
    }
}