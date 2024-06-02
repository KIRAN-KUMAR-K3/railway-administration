import streamlit as st
import sqlite3
import pandas as pd

# Database connection
conn = sqlite3.connect('railway_system.db')
c = conn.cursor()

# Create tables if not exist
def create_DB_if_Not_available():
    c.execute('''CREATE TABLE IF NOT EXISTS users
                (username TEXT, password TEXT)''')
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
                    st.header("🚆 Search Result:")
                    st.table(pd.DataFrame([train_data], columns=[
                        "Train Number", "Train Name", "Departure Date", "Starting Destination", "Ending Destination"]))
                else:
                    st.error(f"❌ No train found with the train number: {train_number}")

        if st.button("🔎 Search by Destinations"):
            if starting_destination and ending_destination:
                train_data = search_trains_by_destinations(
                    starting_destination, ending_destination)
                if train_data:
                    st.header("🚆 Search Results:")
                    df = pd.DataFrame(train_data, columns=[
                        "Train Number", "Train Name", "Departure Date", "Starting Destination", "Ending Destination"])
                    st.table(df)
                else:
                    st.error(f"❌ No trains found for the given source and destination.")
    
    elif functions == "Delete Train":
        st.title("🗑️ Delete Train")
        train_number = st.text_input("Enter Train Number to delete:")
        departure_date = st.date_input("Enter the Train Departure date")
        if st.button("🗑️ Delete Train"):
            if train_number:
                c.execute(f"DROP TABLE IF EXISTS seats_{train_number}")
                delete_train(train_number, departure_date)
    
    elif functions == "Book Ticket":
        st.title("🎫 Book Train Ticket")
        train_number = st.text_input("Enter Train Number:")
        seat_type = st.selectbox(
            "Seat Type", ["Aisle", "Middle", "Window"], index=0)
        passenger_name = st.text_input("Passenger Name")
        passenger_age = st.number_input("Passenger Age", min_value=1)
        passenger_gender = st.selectbox(
            "Passenger Gender", ["Male", "Female", "Other"], index=0)

        if st.button("🎟️ Book Ticket"):
            if train_number and passenger_name and passenger_age and passenger_gender:
                book_ticket(train_number, passenger_name,
                            passenger_age, passenger_gender, seat_type)
    
    elif functions == "Cancel Ticket":
        st.title("❌ Cancel Ticket")
        train_number = st.text_input("Enter Train Number:")
        seat_number = st.number_input("Enter Seat Number", min_value=1)
        if st.button("❌ Cancel Ticket"):
            if train_number and seat_number:
                cancel_tickets(train_number, seat_number)
    
    elif functions == "View Seats":
        st.title("💺 View Seats")
        train_number = st.text_input("Enter Train Number:")
        if st.button("Submit"):
            if train_number:
                view_seats(train_number)

# Run the app
if __name__ == "__main__":
    train_functions()
    conn.close()