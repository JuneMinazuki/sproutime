import tkinter as tk
import psutil # type: ignore
import getpass

window = tk.Tk()
window.geometry("720x250")
window.title("Sproutime")

def pids_for_user(username: str) -> list[psutil.Process]:
    return [p for p in psutil.process_iter() if p.username() == username]


listbox = tk.Listbox(window, width=720, height=250)
listbox.pack()

for n in pids_for_user(getpass.getuser()): #get user name
    listbox.insert(tk.END, n)

window.mainloop()