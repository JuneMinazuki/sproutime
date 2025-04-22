import customtkinter
import sys
from window import window

def button_callback():
    print("Start")
    window()


app = customtkinter.CTk()
app.geometry("1080x720")
app.title("Sproutime --main menu")

button = customtkinter.CTkButton(app, text="Start", command=button_callback)
button.pack(padx=20, pady=20)

app.mainloop()