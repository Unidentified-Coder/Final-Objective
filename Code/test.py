import tkinter as tk
from tkinter import Label, Entry, Button
import time

# Function to determine traffic light timing based on traffic density
def calculate_traffic_light():
    try:
        north = int(north_entry.get())
        south = int(south_entry.get())
        east = int(east_entry.get())
        west = int(west_entry.get())

        # Calculate total traffic on each road
        total_ns = north + south  # North-South Traffic
        total_ew = east + west  # East-West Traffic

        # Determine which direction gets priority
        if total_ns > total_ew:
            main_road = "North-South"
            sec_road = "East-West"
            main_duration = min(10 + total_ns // 2, 30)  # Max 30 sec green
            sec_duration = min(5 + total_ew // 3, 15)  # Max 15 sec green
        else:
            main_road = "East-West"
            sec_road = "North-South"
            main_duration = min(10 + total_ew // 2, 30)
            sec_duration = min(5 + total_ns // 3, 15)

        # Display the simulation
        simulate_traffic(main_road, main_duration, sec_road, sec_duration)

    except ValueError:
        status_label.config(text="Please enter valid numbers!", fg="red")

# Function to simulate the traffic light sequence
def simulate_traffic(main_road, main_duration, sec_road, sec_duration):
    status_label.config(text=f"{main_road} GREEN for {main_duration} sec", fg="green")
    light_canvas.config(bg="green")
    root.update()
    time.sleep(main_duration)

    status_label.config(text="YELLOW Light (Slow Down)", fg="orange")
    light_canvas.config(bg="yellow")
    root.update()
    time.sleep(3)

    status_label.config(text=f"{sec_road} GREEN for {sec_duration} sec", fg="green")
    light_canvas.config(bg="green")
    root.update()
    time.sleep(sec_duration)

    status_label.config(text="YELLOW Light (Slow Down)", fg="orange")
    light_canvas.config(bg="yellow")
    root.update()
    time.sleep(3)

    status_label.config(text="RED Light (Stop)", fg="red")
    light_canvas.config(bg="red")
    root.update()
    time.sleep(2)

    status_label.config(text="Simulation Complete!", fg="blue")

# Initialize GUI
root = tk.Tk()
root.title("Traffic Light Simulation")

# Instructions
instructions = tk.Label(root, text="Enter the number of cars on each side and press 'Start Simulation'", font=("Arial", 12))
instructions.pack(pady=10)

# Traffic Input Fields
frame = tk.Frame(root)
frame.pack()

tk.Label(frame, text="North:").grid(row=0, column=0)
north_entry = Entry(frame, width=5)
north_entry.grid(row=0, column=1)

tk.Label(frame, text="South:").grid(row=0, column=2)
south_entry = Entry(frame, width=5)
south_entry.grid(row=0, column=3)

tk.Label(frame, text="East:").grid(row=1, column=0)
east_entry = Entry(frame, width=5)
east_entry.grid(row=1, column=1)

tk.Label(frame, text="West:").grid(row=1, column=2)
west_entry = Entry(frame, width=5)
west_entry.grid(row=1, column=3)

# Start Button
start_btn = Button(root, text="Start Simulation", command=calculate_traffic_light)
start_btn.pack(pady=10)

# Traffic Light Display (Canvas)
light_canvas = tk.Canvas(root, width=100, height=150, bg="gray")
light_canvas.pack(pady=10)

# Status Label
status_label = tk.Label(root, text="Enter car counts and start simulation", font=("Arial", 14))
status_label.pack()

# Run GUI
root.mainloop()
