import streamlit as st
import sqlite3
import pandas as pd

# Database connection
conn = sqlite3.connect('railway_system.db')
c = conn.cursor()

# Create tables if not exist
def create_DB_if_Not_available():
    c.execute('''CREATE TABLE IF NOT EXISTS users
                (username TEXT UNIQUE, password TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS employees
                (employee_id TEXT, password TEXT, designation TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS trains
                (train_number TEXT, train_name TEXT, departure_date TEXT, starting_destination TEXT, ending_destination TEXT)''')
create_DB_if_Not_available()

# Function to add a new train
def add_train(train_number, train_name, departure_date, starting_destination, ending_destination):
    c.execute("INSERT INTO trains (train_number, train_name, departure_date, starting_destination, ending_destination) VALUES (?, ?, ?, ?, ?)",
              (train_number, train_name, departure_date, starting_destination, ending_destination))
    conn.commit()
    create_seat_table(train_number)

# Function to delete a train
def delete_train(train_number, departure_date):
    train_query = c.execute("SELECT * FROM trains WHERE train_number = ?", (train_number,))
    train_data = train_query.fetchone()
    if train_data:
        c.execute("DELETE FROM trains WHERE train_number = ? AND departure_date=?", (train_number, departure_date))
        conn.commit()
        st.success(f"✅ Train with Train Number {train_number} has been deleted.")
    else:
        st.error(f"❌ No such Train with Number {train_number} is available")

# Function to create seat table for a train
def create_seat_table(train_number):
    c.execute(f'''
        CREATE TABLE IF NOT EXISTS seats_{train_number} (
            seat_number INTEGER PRIMARY KEY,
            seat_type TEXT,
            booked INTEGER,
            passenger_name TEXT,
            passenger_age INTEGER,
            passenger_gender TEXT
        )
    ''')

    for i in range(1, 51):
        val = categorize_seat(i)
        c.execute(f'''INSERT INTO seats_{train_number}(seat_number, seat_type, booked, passenger_name, passenger_age, passenger_gender) VALUES (?,?,?,?,?,?);''', (
            i, val, 0, "", "", ""))
    conn.commit()

# Function to categorize seat type
def categorize_seat(seat_number):
    if (seat_number % 10) in [0, 4, 5, 9]:
        return "Window"
    elif (seat_number % 10) in [2, 3, 6, 7]:
        return "Aisle"
    else:
        return "Middle"

# Function to allocate next available seat
def allocate_next_available_seat(train_number, seat_type):
    seat_query = c.execute(f"SELECT seat_number FROM seats_{train_number} WHERE booked=0 and seat_type=? ORDER BY seat_number asc", (seat_type,))
    result = seat_query.fetchall()
    if result:
        return result[0]

# Function to book a ticket
def book_ticket(train_number, passenger_name, passenger_age, passenger_gender, seat_type):
    train_query = c.execute("SELECT * FROM trains WHERE train_number = ?", (train_number,))
    train_data = train_query.fetchone()
    if train_data:
        seat_number = allocate_next_available_seat(train_number, seat_type)
        if seat_number:
            c.execute(f"UPDATE seats_{train_number} SET booked=1, seat_type=?, passenger_name=?, passenger_age=?, passenger_gender=? WHERE seat_number=?", (
                seat_type, passenger_name, passenger_age, passenger_gender, seat_number[0]))
            conn.commit()
            st.success(f"✅ Successfully booked seat {seat_number[0]} ({seat_type}) for {passenger_name}.")
        else:
            st.error("❌ No available seats for booking in this train.")
    else:
        st.error(f"❌ No such Train with Number {train_number} is available")

# Function to cancel a ticket
def cancel_tickets(train_number, seat_number):
    train_query = c.execute("SELECT * FROM trains WHERE train_number = ?", (train_number,))
    train_data = train_query.fetchone()
    if train_data:
        c.execute(f'''UPDATE seats_{train_number} SET booked=0, passenger_name='', passenger_age='', passenger_gender='' WHERE seat_number=?''', (seat_number,))
        conn.commit()
        st.success(f"✅ Successfully canceled seat {seat_number} from {train_number} .")
    else:
        st.error(f"❌ No such Train with Number {train_number} is available")

# Function to search train by train number
def search_train_by_train_number(train_number):
    train_query = c.execute("SELECT * FROM trains WHERE train_number = ?", (train_number,))
    train_data = train_query.fetchone()
    return train_data

# Function to search trains by starting and ending destinations
def search_trains_by_destinations(starting_destination, ending_destination):
    train_query = c.execute("SELECT * FROM trains WHERE starting_destination = ? AND ending_destination = ?", (starting_destination, ending_destination))
    train_data = train_query.fetchall()
    return train_data

# Function to view seats of a train
def view_seats(train_number):
    train_query = c.execute("SELECT * FROM trains WHERE train_number = ?", (train_number,))
    train_data = train_query.fetchone()
    if train_data:
        seat_query = c.execute(f'''SELECT 'Number : ' || seat_number, '\n Type : '  || seat_type ,'\n Name : ' ||  passenger_name , '\n Age : ' || passenger_age ,'\n Gender : ' ||  passenger_gender as Details, booked  FROM seats_{train_number} ORDER BY seat_number asc''')
        result = seat_query.fetchall()
        if result:
            st.dataframe(data=result)
    else:
        st.error(f"❌ No such Train with Number {train_number} is available")

# Function to handle user registration
def register_user(username, password):
    # Check if username already exists
    c.execute("SELECT * FROM users WHERE username = ?", (username,))
    if c.fetchone():
        st.error("Username already exists! Please choose a different username.")
    else:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        st.success("User registered successfully! Please log in.")

# Function to validate user login
def login_user(username, password):
    c.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    return c.fetchone()

# Main function for the Streamlit app
def train_functions():
    st.title("🚆 Railway Management System")
    st.sidebar.title("🛤️ Train Administrator")
    functions = st.sidebar.selectbox("Select Train Functions", [
        "Add Train", "View Trains", "Search Train", "Delete Train", "Book Ticket", "Cancel Ticket", "View Seats"])
    
    if functions == "Add Train":
        st.header("🛤️ Add New Train")
        with st.form(key='new_train_details'):
            train_number = st.text_input("Train Number")
            train_name = st.text_input("Train Name")
            departure_date = st.date_input("📅 Date of Departure")
            starting_destination = st.text_input("🚉 Starting Destination")
            ending_destination = st.text_input("🛑 Ending Destination")
            submitted = st.form_submit_button("Add Train")
        if submitted and train_name != "" and train_number != '' and starting_destination != "" and ending_destination != "":
            add_train(train_number, train_name, departure_date,
                      starting_destination, ending_destination)
            st.success("✅ Train Added Successfully!")
    
    elif functions == "View Trains":
        st.title("🚆 View All Trains")
        train_query = c.execute("SELECT * FROM trains")
        trains = train_query.fetchall()

        if trains:
            st.header("Available Trains:")
            st.dataframe(data=trains)
        else:
            st.error("❌ No trains available in the database.")
    
    elif functions == "Search Train":
        st.title("🔍 Train Details Search")

        st.write("🔍 Search by Train Number:")
        train_number = st.text_input("Enter Train Number:")

        st.write("🔍 Search by Starting and Ending Destination:")
        starting_destination = st.text_input("Starting Destination:")
        ending_destination = st.text_input("Ending Destination:")

        if st.button("🔎 Search by Train Number"):
            if train_number:
                train_data = search_train_by_train_number(train_number)
                if train_data:
                    st.header("🚆 Train Details:")
                    st.table(pd.DataFrame([train_data], columns=[
                        "Train Number", "Train Name", "Departure Date", "Starting Destination", "Ending Destination"]))
                else:
                    st.error(f"❌ No train found with the Train Number: {train_number}")

        if st.button("🔎 Search by Destinations"):
            if starting_destination and ending_destination:
                trains = search_trains_by_destinations(
                    starting_destination, ending_destination)
                if trains:
                    st.header("🚆 Search Result:")
                    st.table(pd.DataFrame(trains, columns=[
                        "Train Number", "Train Name", "Departure Date", "Starting Destination", "Ending Destination"]))
                else:
                    st.error(f"❌ No trains found from {starting_destination} to {ending_destination}")
    
    elif functions == "Delete Train":
        st.header("🛤️ Delete a Train")
        train_number = st.text_input("Train Number to delete:")
        departure_date = st.date_input("📅 Date of Departure")
        if st.button("Delete Train"):
            if train_number:
                delete_train(train_number, departure_date)
    
    elif functions == "Book Ticket":
        st.header("🛤️ Book Ticket")
        with st.form(key='booking_details'):
            train_number = st.text_input("Train Number")
            passenger_name = st.text_input("Passenger Name")
            passenger_age = st.number_input("Passenger Age", min_value=1, step=1)
            passenger_gender = st.selectbox(
                "Passenger Gender", ["Male", "Female", "Other"])
            seat_type = st.selectbox("Seat Type", ["Window", "Aisle", "Middle"])
            submitted = st.form_submit_button("Book Ticket")
        if submitted:
            book_ticket(train_number, passenger_name,
                        passenger_age, passenger_gender, seat_type)
    
    elif functions == "Cancel Ticket":
        st.header("🛤️ Cancel Ticket")
        train_number = st.text_input("Train Number")
        seat_number = st.number_input("Seat Number", min_value=1, step=1)
        if st.button("Cancel Ticket"):
            if train_number and seat_number:
                cancel_tickets(train_number, seat_number)
    
    elif functions == "View Seats":
        st.header("🛤️ View Seats")
        train_number = st.text_input("Train Number to view seats:")
        if st.button("View Seats"):
            if train_number:
                view_seats(train_number)

def main():
    st.title("🚆 Railway Management System")
    
    # Sidebar for login and registration
    st.sidebar.title("User Authentication")
    auth_mode = st.sidebar.selectbox("Choose Authentication Mode", ["Login", "Register"])
    
    if auth_mode == "Register":
        st.sidebar.header("Register")
        username = st.sidebar.text_input("Username")
        password = st.sidebar.text_input("Password", type="password")
        confirm_password = st.sidebar.text_input("Confirm Password", type="password")
        
        if st.sidebar.button("Register"):
            if password == confirm_password:
                register_user(username, password)
                st.sidebar.success("User registered successfully! Please log in.")
            else:
                st.sidebar.error("Passwords do not match!")
    
    elif auth_mode == "Login":
        st.sidebar.header("Login")
        username = st.sidebar.text_input("Username")
        password = st.sidebar.text_input("Password", type="password")
        
        if st.sidebar.button("Login"):
            user = login_user(username, password)
            if user:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.sidebar.success("Logged in successfully!")
            else:
                st.sidebar.error("Invalid username or password!")
    
    if 'logged_in' in st.session_state and st.session_state.logged_in:
        st.sidebar.header(f"Welcome, {st.session_state.username}")
        if st.sidebar.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.sidebar.success("Logged out successfully!")

        # Execute railway management system functions
        train_functions()
    else:
        st.write("Please log in to access the Railway Management System")

# Execute main function
if __name__ == "__main__":
    main()
