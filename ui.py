import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import time

def time():
    """Display the current time in the label."""
    current_time = datetime.now().strftime("%H:%M:%S")
    label_time.config(text=current_time)  # Update the label with the current time
    label_time.after(1000, time)  # Call this function again after 1 second
    return current_time

# Create the main application window
root = tk.Tk()
root.title("Sproutime")
root.geometry("400x300")  # Set the window size

label = ttk.Label(root, text="Welcome to Sproutime!")
label.pack(pady=10)

# Add time display
label_time = ttk.Label(root, text="", font=("Helvetica", 12))
label_time.pack(pady=10)
label_time.place(x=0, y=0)  # Position the label at the top left corner)
time()  # Call the time function to start updating the label



# Add a quit button

def on_closing():
    if tk.messagebox.askokcancel(title="Quit", message="Do you want to quit?"):
        root.destroy()
        # Add a message box to confirm quitting
quit_button = ttk.Button(root, text="Quit", command=on_closing)
quit_button.pack(pady=10)


root.protocol("WM_DELETE_WINDOW", on_closing)

# Run the application
root.mainloop()