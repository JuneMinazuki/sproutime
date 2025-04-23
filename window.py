def window():   
    import customtkinter as ctk
    import sys

    #Check OS
    if sys.platform == 'darwin':
        import AppKit
    elif sys.platform == 'win32': #check if correct for win
        import psutil
        import win32gui
        import win32process
        from pywinauto.application import Application

    #DEBUG
    DEBUG = 1 #Use this to lower the time check for app from minute to second to save time
    
    global temp_quest_app, temp_quest_time

    app_dict = {}
    sleep_time = 1 if DEBUG else 60
    temp_quest_app = ""
    temp_quest_time = ""

    #App Info
    window = ctk.CTk()
    window.geometry("1080x720")
    window.title("Sproutime")
    window.columnconfigure(1, weight=1)
    window.columnconfigure(1, weight=1)

    def get_active_app_name():
        if sys.platform == 'darwin':
            appName = AppKit.NSWorkspace.sharedWorkspace().activeApplication()['NSApplicationName']
            
        elif sys.platform == 'win32': #check if correct for win
            foregroundApp = win32gui.GetForegroundWindow()
            appTitle = win32gui.GetWindowText(foregroundApp)
            appName = appTitle.split(" - ")[-1]
            if appName == "Google Chrome": 
                tabName = get_active_tab_name()
                appName = " - ".join([appName, tabName])
            
        return appName

    def get_all_app_list():
            app_list = []
            
            if sys.platform == 'darwin':
                running_app = AppKit.NSWorkspace.sharedWorkspace().runningApplications()
                
                for app in running_app:
                    launch_date = app.launchDate()
                    if not app.isHidden() and launch_date:
                        app_list.append(app.localizedName())
                        
            elif sys.platform == 'win32':
                PID_list = []
                for process in psutil.process_iter(['pid', 'name']): # Loops through all running processes 
                    pid = process.info['pid']

                    def enumWindowsArguments(handle, __): # This will be called for each top-level window to exclude all other background processes (refer to EnumWindows)
                        threadID, foundPID = win32process.GetWindowThreadProcessId(handle) # Get the Process ID for the current window handle

                        if foundPID == pid and win32gui.IsWindowVisible(handle): # This checks if it is actually a visible window
                            runningAppName = process.info['name'].split(".")[0].capitalize()
                            if runningAppName not in app_list:
                                app_list.append(runningAppName)
                                PID_list.append(pid) # I think this will be needed later when we implement the user task setup

                    win32gui.EnumWindows(enumWindowsArguments, None) # Enumerate all top-level windows

            return app_list

    def get_active_tab_name():
        if sys.platform == "darwin":
            pass

        elif sys.platform == "win32":
            try:
                foregroundApp = win32gui.GetForegroundWindow()
                TID, PID = win32process.GetWindowThreadProcessId(foregroundApp)
                chromeApp = Application(backend = "uia").connect(process = PID)
                topWindow = chromeApp.top_window()
                url = topWindow.child_window(title = "Address and search bar", control_type = "Edit").get_value() # URL is here

                tabName = url.split("/")[0].split(".")[-2].capitalize()
            except Exception:
                tabName = "URL not detected"

        return tabName
    
    def combobox_callback(choice):
        global temp_quest_app
        temp_quest_app = choice
            
    def timebox_callback(choice):
        global temp_quest_time
        temp_quest_time = choice
            
    def save_quest_time():
        global temp_quest_app, temp_quest_time
        try:
            with open("quest_log.txt", 'r') as log:
                lines = log.readlines()
        except FileNotFoundError:
            with open("quest_log.txt", "a") as log:
                log.write(f"{temp_quest_app} : {temp_quest_time}\n")
            update_quest_list()
            return

        updated_lines = []
        found = False
        for line in lines:
            if line.startswith(temp_quest_app):
                parts = line.split(':', 1)
                if len(parts) == 2:
                    updated_line = f"{temp_quest_app} : {temp_quest_time}\n"
                    updated_lines.append(updated_line)
                    found = True
                else:
                    updated_lines.append(line)
            else:
                updated_lines.append(line)

        if found:
            with open("quest_log.txt", 'w') as log:
                log.writelines(updated_lines)
        else:
            with open("quest_log.txt", "a") as log:
                log.write(f"{temp_quest_app} : {temp_quest_time}\n")
        update_quest_list()

    def update_quest_list():
        try:
            quest_list_TB.delete("0.0", "end")
            with open("quest_log.txt", "r") as log:
                for line in log:
                    quest_list_TB.insert("0.0", f'{line.strip()}\n')
        except FileNotFoundError:
            pass

    def update_loop(): #this is the while true loop
        app_name = get_active_app_name()
        if app_name in app_dict:
            app_index = list(app_dict.keys()).index(app_name) +1
            app_dict[app_name] += sleep_time

            app_list_TB.delete(f"{app_index}.0", f"{app_index}.end")
            app_list_TB.insert(f"{app_index}.0", f'{list(app_dict.keys())[app_index -1]}: {app_dict[app_name]} seconds')
        else:
            app_dict[app_name] = sleep_time
            
            app_list_TB.insert(f"end", f'{list(app_dict.keys())[-1]}: {app_dict[app_name]} seconds\n')

        window.after(sleep_time*1000, update_loop)
        
    def on_closing(): #when user close the program
        print("Window is closing!") #temp code
        ()

    #Textbox
    app_list_TB = ctk.CTkTextbox(window, width=1080, height=360)
    app_list_TB.grid(row=0, column=0, columnspan = 2)

    time = [">1 hour", ">2 hours", '>3 hours']
    temp_quest_time = time[0]
    app_list = get_all_app_list()
    temp_quest_app = app_list[0]
    
    #App Option
    combobox = ctk.CTkComboBox(master=window,values=app_list, command=combobox_callback)
    combobox.grid(row=1, column=0, padx=20, pady=10, sticky='w')

    #Time Option
    timebox = ctk.CTkComboBox(master=window,values=time, command=timebox_callback)
    timebox.grid(row=1, column=1, padx=20, pady=10, sticky='e')

    #Button
    button = ctk.CTkButton(master=window, text="Save", command=save_quest_time)
    button.grid(row=2, column=1, padx=20, pady=10, sticky='e')

    #Quest Saved Textbox
    quest_list_TB = ctk.CTkTextbox(window, width=1080, height=360)
    quest_list_TB.grid(row=3, column=0, columnspan = 2)
    update_quest_list()

    update_loop()

    window.protocol("WM_DELETE_WINDOW", on_closing) #check for if user close the program

    window.mainloop()
    
if __name__=="__main__":
    window()