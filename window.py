import customtkinter as ctk
import psutil # type: ignore
import getpass #get user name
import win32gui

#DEBUG
DEBUG = 1 #Use this to lower the time check for app from minute to second to save time

app_name_list = []
app_time_list = []
sleep_time = 1 if DEBUG else 60
app_index = 0

#App Info
window = ctk.CTk()
window.geometry("1080x720")
window.title("Sproutime")

def get_active_app_name():
    foregroundApp = win32gui.GetForegroundWindow()
    appTitle = win32gui.GetWindowText(foregroundApp)
    appName = appTitle.split("-")[-1].strip()
    return appName

def update_list(): #this is the while true loop
    app_name = get_active_app_name()
    if app_name in app_name_list:
        app_index = app_name_list.index(app_name)
        app_time_list[app_index] += sleep_time

        app_list_TB.delete(f"{app_index +1}.0", f"{app_index +1}.end")
        app_list_TB.insert(f"{app_index +1}.0", f'{app_name_list[app_index]}: {app_time_list[app_index]} seconds')
    else:
        app_name_list.append(app_name)
        app_time_list.append(sleep_time)
        
        app_list_TB.insert(f"end", f'{app_name_list[-1]}: {app_time_list[-1]} seconds\n')

    window.after(sleep_time*1000, update_list)

app_list_TB = ctk.CTkTextbox(window, width=1080, height=720)
app_list_TB.grid(row=0, column=0)

update_list()

window.mainloop()