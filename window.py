import tkinter as tk
import psutil # type: ignore
import getpass #get user name

#App Info
window = tk.Tk()
window.geometry("1080x720")
window.title("Sproutime")

def pids_for_user(username: str) -> list[psutil.Process]:
    return [p for p in psutil.process_iter() if p.username() == username]


listbox = tk.Listbox(window, width=1080, height=720)
listbox.pack()

for n in pids_for_user(getpass.getuser()): #pending update to only check for app name and time, also remove any system appication
    listbox.insert(tk.END, n)

window.mainloop()