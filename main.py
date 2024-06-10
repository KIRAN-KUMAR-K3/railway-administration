import streamlit as st
import sqlite3
import hashlib

# Database connection
conn = sqlite3.connect('user_database.db')
c = conn.cursor()

# Create users table if not exists
def create_users_table():
    c.execute('''CREATE TABLE IF NOT EXISTS users
                (username TEXT, password TEXT)''')
    conn.commit()

# Function to hash passwords
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Function to register a new user
def register_user(username, password):
    hashed_password = hash_password(password)
    c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
    conn.commit()

# Function to authenticate user
def login(username, password):
    hashed_password = hash_password(password)
    c.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, hashed_password))
    return c.fetchone()

# Function to check if user is authenticated
def is_authenticated():
    return st.session_state.get('authenticated', False)

# Function to logout user
def logout():
    st.session_state['authenticated'] = False

# Main function for the Streamlit app
def main():
    st.title("Streamlit Registration and Login")

    # Create users table if not exists
    create_users_table()

    # Display login form if not authenticated
    if not is_authenticated():
        auth_option = st.sidebar.radio("Select Option", ["Login", "Register"])
        
        if auth_option == "Register":
            st.sidebar.title("Register")
            new_username = st.sidebar.text_input("New Username")
            new_password = st.sidebar.text_input("New Password", type="password")
            if st.sidebar.button("Register"):
                if new_username and new_password:
                    register_user(new_username, new_password)
                    st.success("Registration successful! Please log in.")
                else:
                    st.error("Please fill in all fields.")
        
        elif auth_option == "Login":
            st.sidebar.title("Login")
            username = st.sidebar.text_input("Username")
            password = st.sidebar.text_input("Password", type="password")
            if st.sidebar.button("Login"):
                if login(username, password):
                    st.session_state['authenticated'] = True
                    st.success("Login successful")
                else:
                    st.error("Invalid username or password")
    
    # Display hello world for authenticated users
    else:
        if st.sidebar.button("Logout"):
            logout()
            st.success("Logged out successfully.")
        else:
            st.write("Hello World!")

# Run the app
if __name__ == "__main__":
    main()
    conn.close()
