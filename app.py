# app.py
from flask import Flask, render_template, request, redirect, url_for, session, flash
import database as db

app = Flask(__name__)


# HELPER FUNCTIONS
def validate_password(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number"       
    return True, ""

def validate_id_number(idnumber):
    """Validate ID number format (adjust for your country)"""
    # Remove any whitespace
    idnumber = str(idnumber).strip()
    
    # Check if it's 13 digits
    if len(idnumber) != 13:
        return False, "ID number must be 13 digits"
    
    if not idnumber.isdigit():
        return False, "ID number must be 13 digits"
    
    return True, ""

def validate_phone(phonenumber):
    """Validate phone number format"""
    # Remove spaces and dashes
    phonenumber = str(phonenumber).replace(' ', '').replace('-', '')
    
    if not phonenumber.isdigit():
        return False, "Phone number must contain only digits"
    
    if len(phonenumber) < 10 or len(phonenumber) > 15:
        return False, "Phone number must be between 10 and 15 digits"
    
    return True, ""

# ROUTES
@app.route("/", methods=["GET"])
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template("index.html")

@app.route("/login", methods=["POST"])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()
    
    if not username or not password:
        flash("Please enter both username and password", "error")
        return redirect(url_for('index'))
    
    user = db.get_user(username, password)
    
    if user:
        session['user_id'] = user['id']  
        session['username'] = user['username']
        session['email'] = user['email']
        return redirect(url_for('dashboard'))
    else:
        flash("Invalid username or password", "error")
        return redirect(url_for('index'))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # Get form data - using CORRECT field names that match HTML form
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()
        email = request.form.get("email", "").strip()
        idnumber = request.form.get("idnumber", "").strip()  # Matches HTML name="idnumber"
        gender = request.form.get("gender", "").strip()
        phonenumber = request.form.get("phonenumber", "").strip()  # Matches HTML name="phonenumber"
        
        # Debug print
        print(f"Registration attempt: {username}, ID: {idnumber}, Phone: {phonenumber}")
        
        # Validation
        errors = []
        
        # Check required fields
        if not all([username, password, confirm_password, email, idnumber, gender, phonenumber]):
            errors.append("All fields are required")
        
        # Check password match
        if password != confirm_password:
            errors.append("Passwords do not match")
        
        # Validate password strength
        is_valid_pass, pass_error = validate_password(password)
        if not is_valid_pass:
            errors.append(pass_error)
        
        # Validate ID number
        is_valid_id, id_error = validate_id_number(idnumber)
        if not is_valid_id:
            errors.append(id_error)
        
        # Validate phone
        is_valid_phone, phone_error = validate_phone(phonenumber)
        if not is_valid_phone:
            errors.append(phone_error)
        
        # Check if user already exists
        if db.user_exists(username=username):
            errors.append("Username already taken")
        if db.user_exists(email=email):
            errors.append("Email already registered")
        if db.user_exists(idnumber=idnumber):
            errors.append("ID number already registered")
        
        # If errors, show them
        if errors:
            for error in errors:
                flash(error, "error")
            return render_template("register.html")
        
        # Create user - parameter names match database function
        success, result = db.create_user(
            username=username, 
            password=password, 
            email=email, 
            idnumber=idnumber, 
            gender=gender, 
            phonenumber=phonenumber
        )
        
        if success:
            flash("Registration successful! Please login.", "success")
            return redirect(url_for('index'))
        else:
            flash(f"Registration failed: {result}", "error")
            return render_template("register.html")
    
    # GET request
    return render_template("register.html")

@app.route("/dashboard")
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    return f"""
    <h1>Welcome, {session['username']}!</h1>
    <p>Email: {session['email']}</p>
    <a href="/logout">Logout</a>
    """

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out", "success")
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)