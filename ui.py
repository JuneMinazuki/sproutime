import customtkinter
import sys
from function import *
import os

x=0

def button_callback():
    print("Start")
    if x==1:
        win()
    elif x==2:
        mac()
    else:
        print("Sorry, this OS is not supported yet")
    
# Make application window
app = customtkinter.CTk()
app.geometry("1080x720")
app.title("Sproutime --main menu")

# Determine the operating system
os_name = os.name  # Returns 'nt' for Windows, 'posix' for Mac
if os_name == "nt":
    print("Running on Windows")
    x=1

elif os_name == "posix":
    print("Running on macOS")
    x=2

else:
    print(f"Unknown OS: {os_name}")
    x=3

button = customtkinter.CTkButton(app, text="Start", command=button_callback)
button.pack(padx=20, pady=20)

app.mainloop()