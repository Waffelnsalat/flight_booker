import mysql.connector
import tkinter as tk
from tkinter import ttk
import datetime

# Connect to the MySQL database
def connect_to_database():
    try:
        connection = mysql.connector.connect(
            host="10.0.10.147",
            user="remote",
            password="sml12345",
            database="flightdata"
        )
        return connection
    except mysql.connector.Error as error:
        print("Failed to connect to the database:", error)

# Display the contents of a table in a new window
def display_table_data(connection, table_name):
    try:
        cursor = connection.cursor()
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        print(rows)

        # Create a new Tkinter window
        window = tk.Tk()


        # Add a search filter
        search_frame = tk.Frame(window)
        search_frame.pack()

        departure_label = tk.Label(search_frame, text="Departure Location:")
        departure_label.pack(side=tk.LEFT)
        departure_entry = tk.Entry(search_frame)
        departure_entry.pack(side=tk.LEFT)

        destination_label = tk.Label(search_frame, text="Destination Location:")
        destination_label.pack(side=tk.LEFT)
        destination_entry = tk.Entry(search_frame)
        destination_entry.pack(side=tk.LEFT)

        time_label = tk.Label(search_frame, text="Departure Time (HH:MM:SS):")
        time_label.pack(side=tk.LEFT)
        time_entry = tk.Entry(search_frame)
        time_entry.pack(side=tk.LEFT)

        search_button = tk.Button(search_frame, text="Search", command=lambda: search_treeview(treeview, connection, table_name, departure_entry.get(), destination_entry.get(), time_entry.get()))
        search_button.pack(side=tk.LEFT)

        # Create a treeview widget to display the data in a table form
        treeview = ttk.Treeview(window, height=25)
        treeview.pack()

        # Define table columns
        columns = [description[0] for description in cursor.description]
        treeview["columns"] = columns
        treeview["show"] = "headings"

        # Configure column headings
        for column in columns:
            treeview.heading(column, text=column, command=lambda col=column: sort_table(treeview, col))

        # Insert the rows into the treeview
        for row in rows:
            treeview.insert("", tk.END, values=row)

        # Create a second treeview for stopover flights
        stopover_frame = tk.Frame(window)
        stopover_frame.pack()

        stopover_label = tk.Label(stopover_frame, text="Stopover Flights:")
        stopover_label.pack()

        stopover_treeview = ttk.Treeview(stopover_frame, height=25)
        stopover_treeview.pack()

        # Define table columns
        stopover_treeview["columns"] = columns
        stopover_treeview["show"] = "headings"

        # Configure column headings
        for column in columns:
            stopover_treeview.heading(column, text=column)

        stopover_button = tk.Button(stopover_frame, text="Search Stopovers", command=lambda: search_stopovers(treeview, stopover_treeview, connection, table_name, departure_entry.get(), destination_entry.get(), time_entry.get()))
        stopover_button.pack()

        cursor.close()

        # Start the Tkinter event loop
        window.mainloop()

    except mysql.connector.Error as error:
        print("Error retrieving data from table:", error)

# Sort the table data based on the selected column
def sort_table(treeview, column):
    # Get the current table data
    data = [(treeview.set(child, column), child) for child in treeview.get_children('')]

    # Detect if the column is a time column by trying to parse the first value
    try:
        is_time_column = isinstance(datetime.datetime.strptime(data[0][0], "%H:%M:%S"), datetime.datetime)
    except ValueError:
        is_time_column = False

    # Sort the data using appropriate data types
    if is_time_column:
        # Convert strings to datetime objects for sorting
        data.sort(key=lambda item: datetime.datetime.strptime(item[0], "%H:%M:%S"))
    elif data and data[0][0].isnumeric():
        data.sort(key=lambda item: int(item[0]))
    else:
        data.sort()

    # Rearrange the table rows based on the sorted data
    for index, (value, child) in enumerate(data):
        treeview.move(child, '', index)

def refill_treeview(treeview, connection, table_name):
    cursor = connection.cursor()
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()
    treeview.delete(*treeview.get_children())
    for row in rows:
        treeview.insert("", tk.END, values=row)
    cursor.close()

def search_treeview(treeview, connection, table_name, departure, destination, time):
    refill_treeview(treeview, connection, table_name)
    children = treeview.get_children('')
    input_time = None
    if time:
        try:
            # convert the input string to a datetime object, ignoring the date
            input_time = datetime.datetime.strptime(time, "%H:%M:%S").time()
        except ValueError:
            print("Invalid time format. Please use HH:MM:SS")
    for child in children:
        row = treeview.item(child)['values']
        if departure and departure != row[3]:  
            treeview.detach(child)
        elif destination and destination != row[5].rstrip():  # use rstrip() to remove the trailing '\r'
            treeview.detach(child)
        elif input_time:
            try:
                # convert the row's time string to a datetime object, ignoring the date
                row_time = datetime.datetime.strptime(row[2], "%H:%M:%S").time()
                # detach the row if its time is before the input time
                if row_time < input_time:
                    treeview.detach(child)
            except ValueError:
                print(f"Invalid time format in table data: {row[2]}")

def search_stopovers(treeview, stopover_treeview, connection, table_name, departure, destination, time):
    # Find all flights from the departure airport
    cursor = connection.cursor()
    cursor.execute(f"SELECT * FROM {table_name} WHERE departure_location = %s", (departure,))
    departure_flights = cursor.fetchall()

    # Find all flights to the destination airport
    cursor.execute(f"SELECT * FROM {table_name} WHERE destination_location = %s", (destination,))
    destination_flights = cursor.fetchall()

    # Find all possible stopover flights
    stopover_flights = []
    for dep_flight in departure_flights:
        for dest_flight in destination_flights:
            if dep_flight[5].rstrip() == dest_flight[3].rstrip():  # Strip '\r' and compare
                stopover_flights.append(dep_flight)
                stopover_flights.append(dest_flight)

    # Display the stopover flights in the treeview
    stopover_treeview.delete(*stopover_treeview.get_children())
    for flight in stopover_flights:
        stopover_treeview.insert("", tk.END, values=flight)


# Main function
def main():
    connection = connect_to_database()
    if connection:
        table_name = "Flights"
        display_table_data(connection, table_name)
        connection.close()

# Entry point of the program
if __name__ == "__main__":
    main()
