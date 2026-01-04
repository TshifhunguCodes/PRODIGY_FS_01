import psycopg2
from psycopg2.extras import RealDictCursor
import bcrypt

DB_CONFIG = {
    "host": "localhost",
    "dbname": "UserAuthDB",
    "user": "postgres",
    "password": "Tshifhungu12@",
    "port": 5432
}

def get_connection():
    """Get database connection"""
    return psycopg2.connect(**DB_CONFIG)

def hash_password(password):
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def check_password(password, hashed_password):
    """Check if password matches hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_user(username, password, email, idnumber, gender, phonenumber):
    """
    Create a new user in the "User" table
    FIXED: Column name is "Passwords" (uppercase P with quotes)
    """
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Debug: Print what we're trying to insert
        print(f"DEBUG: Creating user: {username}, {email}, {idnumber}")
        
        # Check if user already exists (by username, email, or idnumber)
        cur.execute("""
            SELECT COUNT(*) FROM "User" 
            WHERE username = %s OR email = %s OR idnumber = %s
        """, (username, email, idnumber))
        
        count = cur.fetchone()['count']
        if count > 0:
            cur.close()
            conn.close()
            return False, "Username, email, or ID number already exists"
        
        # Hash the password
        password_hash = hash_password(password)
       
        #changed id
        # FIXED: Use "Passwords" (uppercase with quotes)
        cur.execute("""
            INSERT INTO "User" (username, email, idnumber, gender, phonenumber, "Passwords")
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING "id", username, email
        """, (username, email, idnumber, gender, phonenumber, password_hash))
        
        user = cur.fetchone()
        conn.commit()
        
        print(f"DEBUG: User created successfully with ID: {user['Id']}")
        
        cur.close()
        conn.close()
        return True, user
        
    except psycopg2.Error as e:
        print(f"Database error in create_user: {e}")
        return False, f"Database error: {e}"
    except Exception as e:
        print(f"Unexpected error in create_user: {e}")
        return False, f"Error: {e}"

def get_user(username, password):
    """
    Get user by username and verify password
    FIXED: Password column is called "Passwords" (uppercase with quotes)
    """
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # FIXED: Use "Passwords" (uppercase with quotes)
        cur.execute('''
            SELECT "id", username, email, idnumber, gender, phonenumber, "Passwords" 
            FROM "User" 
            WHERE username = %s
        ''', (username,))
        
        user = cur.fetchone()
        
        # Verify password if user exists
        if user and check_password(password, user['Passwords']):
            # Remove password from returned user data for security
            del user['Passwords']
            return user
        else:
            return None
            
    except psycopg2.Error as e:
        print(f"Database error in get_user: {e}")
        return None
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

def user_exists(username=None, email=None, idnumber=None):
    """Check if user exists by username, email, or idnumber"""
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        conditions = []
        params = []
        
        if username:
            conditions.append("username = %s")
            params.append(username)
        if email:
            conditions.append("email = %s")
            params.append(email)
        if idnumber:
            conditions.append("idnumber = %s")
            params.append(idnumber)
        
        if not conditions:
            return False
        
        query = f'SELECT COUNT(*) FROM "User" WHERE {" OR ".join(conditions)}'
        cur.execute(query, params)
        count = cur.fetchone()[0]
        
        cur.close()
        conn.close()
        return count > 0
        
    except psycopg2.Error as e:
        print(f"Database error in user_exists: {e}")
        return False