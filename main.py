import streamlit as st
import sqlite3
import pandas as pd

# Database connection
conn = sqlite3.connect('railway_system.db')
c = conn.cursor()

# Create user table if not exists
def create_user_table():
  c.execute('''CREATE TABLE IF NOT EXISTS users
              (username TEXT PRIMARY KEY, password TEXT)''')
  conn.commit()

create_user_table()

# Function to hash passwords before storing them in the database
def hash_password(password):
  import hashlib
  return hashlib.sha256(password.encode()).hexdigest()

# Function to register a new user
def register_user(username, password):
  hashed_password = hash_password(password)
  c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
  conn.commit()
  st.success("✅ User registration successful!")

# Function to authenticate user (use hashed password comparison)
def login(username, password):
  hashed_password = hash_password(password)
  user_query = c.execute("SELECT * FROM users WHERE username = ?", (username,))
  user_data = user_query.fetchone()
  if user_data and user_data[1] == hashed_password:
    return True
  else:
    return False

# Function to check if user is authenticated
def is_authenticated():
  return st.session_state.get('authenticated', False)

# Function to logout user
def logout():
  st.session_state['authenticated'] = False

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

# Function to book a ticket (continued)
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
    seat_query = c.execute(f'''SELECT 'Number : ' || seat_number, '\n Type : ' || seat_type ,'\n Name : ' || passenger_name , '\n Age : ' || passenger_age ,'\n Gender : ' || passenger_gender as Details, booked FROM seats_{train_number} ORDER BY seat_number asc''')
    result = seat_query.fetchall()
    if result:
      st.dataframe(data=result)
  else:
    st.error(f"❌ No such Train with Number {train_number} is available")

# Main function for the Streamlit app
def main():
  st.title("Registration and Login System")

  # Display login or registration form based on authentication state
  if not is_authenticated():
    login_or_register = st.sidebar.selectbox("Login or Register", ["Login", "Register"])

    if login_or_register == "Login":
      username = st.sidebar.text_input("Username")
      password = st.sidebar.text_input("Password", type="password")
      if st.sidebar.button("Login"):
        if login(username, password):
          st.session_state['authenticated'] = True
          st.success("Login successful!")
        else:
          st.error("Invalid username or password")

    elif login_or_register == "Register":
      new_username = st.sidebar.text_input("Username")
      new_password = st.sidebar.text_input("Password", type="password")
      confirm_password = st.sidebar.text_input("Confirm Password", type="password")
      if st.sidebar.button("Register"):
        
        if new_password == confirm_password:
          register_user(new_username, new_password)
        else:
          st.error("Passwords do not match")

  # Display railway management system functions only after successful login
  else:
    st.sidebar.title("️ Train Administrator")
    functions = st.sidebar.selectbox("Select Train Functions", [
        "Add Train", "View Trains", "Search Train", "Delete Train", "Book Ticket", "Cancel Ticket", "View Seats"])

    if functions == "Add Train":
      st.header("️ Add New Train")
      with st.form(key='new_train_details'):
        train_number = st.text_input("Train Number")
        train_name = st.text_input("Train Name")
        departure_date = st.date_input(" Date of Departure")
        starting_destination = st.text_input(" Starting Destination")
        ending_destination = st.text_input(" Ending Destination")
        submitted = st.form_submit_button("Add Train")
      if submitted and train_name != "" and train_number != '' and starting_destination != "" and ending_destination != "":
        add_train(train_number, train_name, departure_date,
                  starting_destination, ending_destination)
        st.success("✅ Train Added Successfully!")

    # ... Implement the remaining functions for train management as in your original code (refer to previous responses)
# Run the app
if __name__ == "__main__":
    
  main()
  conn.close()
