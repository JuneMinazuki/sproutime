import tkinter as tk
import AppKit # type: ignore

#App Info
window = tk.Tk()
window.geometry("1080x720")
window.title("Sproutime")

def get_app_open_durations():
    running_apps = AppKit.NSWorkspace.sharedWorkspace().runningApplications()
    app_durations = {}

    for app in running_apps:
        if not app.isHidden(): # Check if the application is hidden.
            app_name = app.localizedName()
            launch_date = app.launchDate()

            if app_name and launch_date:
                now = AppKit.NSDate.date()
                duration = now.timeIntervalSinceDate_(launch_date)
                duration = round(duration / 3600, 2)
                app_durations[app_name] = duration

    return app_durations

listbox = tk.Listbox(window, width=1080, height=720)
listbox.pack()

for app_name, duration in get_app_open_durations().items():
    listbox.insert(tk.END, f'{app_name}: {duration} hours')

window.mainloop()