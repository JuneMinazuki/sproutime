import customtkinter

def button_callback():
    print("Button clicked!")

app = customtkinter.CTk()
app.geometry("1080x720")
app.title("Sproutime")

button = customtkinter.CTkButton(app, text="Try to click me", command=button_callback)
button.pack(padx=20, pady=20)

app.mainloop()