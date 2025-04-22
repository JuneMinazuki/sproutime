import customtkinter
import sys
from function import *
import os

    

def button_callback():
    print("Start")
    win()
    
# Make application window
app = customtkinter.CTk()
app.geometry("1080x720")
app.title("Sproutime --main menu")




button = customtkinter.CTkButton(app, text="Start", command=button_callback)
button.pack(padx=20, pady=20)

close = customtkinter.CTkButton(app, text="Close", command=sys.exit)
close.pack(padx=20, pady=20)


app.mainloop()