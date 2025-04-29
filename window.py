def window():   
    import sys

    #Check OS and popup for missing libraries
    try:
        import customtkinter as ctk
        import threading
        from time import sleep
        import sqlite3

        if sys.platform == 'darwin':
            import AppKit
        elif sys.platform == 'win32':
            import psutil
            import win32gui
            import win32process
            import pywinauto.application

    except ModuleNotFoundError as e:
        import tkinter
        tkinter.messagebox.showerror("Missing Libraries", str(e))

    #DEBUG
    DEBUG = 1 #Use this to lower the time check for app from minute to second to save time
    
    global temp_quest_app, temp_quest_time, app_dict, new_app, app_index, update_tick, running
    
    #SQLite Setup
    conn = sqlite3.connect('sproutime.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quest (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                app_name TEXT NOT NULL,
                time INTEGER NOT NULL,
                maximum INTEGER NOT NULL
            )
        ''')
        
        if DEBUG:
            cursor.execute(f"DELETE FROM quest")
            conn.commit()
        
    except sqlite3.Error as e:
        if DEBUG: print(f"An error occurred: {e}")
        conn.rollback()

    app_dict = {}
    update_tick = 1 if DEBUG else 60
    new_app = False
    app_index = 0
    temp_quest_app = ""
    temp_quest_time = ""
    running = False
    counter_lock = threading.Lock()
    quest_list = []

    #App Info
    window = ctk.CTk()
    window.geometry("1080x720")
    window.title("Sproutime")
    window.columnconfigure(1, weight=1)
    window.columnconfigure(1, weight=1)

    def get_active_app_name():
        if sys.platform == 'darwin':
            appName = AppKit.NSWorkspace.sharedWorkspace().activeApplication()['NSApplicationName']
            
        elif sys.platform == 'win32':
            foregroundApp = win32gui.GetForegroundWindow()
            appTitle = win32gui.GetWindowText(foregroundApp)
            appName = appTitle.split(" - ")[-1]
            if appName == "Google Chrome": 
                tabName = get_active_tab_name()
                if tabName == "URL not detected":
                    pass
                else:
                    appName = tabName
            
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
                    ignored_processes = ["", "Windows Input Experience", "Program Manager"]

                    def enumWindowsArguments(handle, __): # This will be called for each top-level window to exclude all other background processes (refer to EnumWindows)
                        threadID, foundPID = win32process.GetWindowThreadProcessId(handle) # Get the Process ID for the current window handle

                        if foundPID == pid and win32gui.IsWindowVisible(handle): # This checks if it is actually a visible window
                            window_title = win32gui.GetWindowText(handle)
                            app_name = window_title.split(" - ")[-1]
                            if app_name not in app_list and app_name not in ignored_processes: 
                                app_list.append(app_name)
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
                chromeApp = pywinauto.application.Application(backend = "uia").connect(process = PID) # Connects to active Chrome
                topWindow = chromeApp.top_window() 
                url = topWindow.child_window(title = "Address and search bar", control_type = "Edit").get_value() # URL is here

                tabName = url.split("/")[0].split(".")[-2].capitalize()

            except Exception:
                tabName = "URL not detected"

        return tabName
    
    def combobox_callback(choice):
        if choice == "Google Chrome":
            show_tabBox()
        else:
            tabBox.grid_remove()

        global temp_quest_app
        temp_quest_app = choice
            
    def timebox_callback(choice):
        global temp_quest_time
        temp_quest_time = choice

    def tabBox_callback(choice):
        global temp_quest_app
        if choice == "Any Tab": # For now "Any Tab" will just detect Chrome in General
            pass
        else:
            temp_quest_app = choice
            
    def save_quest_time():
        global temp_quest_app, temp_quest_time
        
        #Pending changes from UI time drop-box update
        maximum_map = {">":1, "<":0}
        maximum = maximum_map.get(list(temp_quest_app)[0])
        temp_quest_time = temp_quest_time[1:]
        
        try:
            cursor.execute("INSERT INTO quest (app_name, time, maximum) VALUES (?, ?, ?)", (temp_quest_app, temp_quest_time, maximum))
            conn.commit()
        except sqlite3.Error as e:
            if DEBUG: print(f"An error occurred: {e}")
            conn.rollback()
        
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

    def refresh_app_list():
        global app_list
        app_list = get_all_app_list()
        
        app_dropdown.configure(values=app_list)

    def update_quest_list():
        try:
            quest_list_TB.delete("0.0", "end")
            with open("quest_log.txt", "r") as log:
                for line in log:
                    quest_list_TB.insert("0.0", f'{line.strip()}\n')
                    quest_name = line.split(" : ")[0]
                    quest_list.append(quest_name)
        except FileNotFoundError:
            pass

    def update_time():
        global app_name, app_dict, app_index, new_app, running
        
        while running:
            with counter_lock:
                app_name = get_active_app_name()
                if quest_list:
                    if app_name in quest_list:
                        if app_name in app_dict:
                            new_app = False
                            app_index = list(app_dict.keys()).index(app_name) +1
                            app_dict[app_name] += 1
                        else:
                            new_app = True
                            app_dict[app_name] = 1
                    else:
                        pass
                    sleep(1)
                else:
                    pass

    def update_loop(): #this is the while true loop
        global app_name, app_dict, app_index, new_app
        
        try:
            if app_name in quest_list:
                if new_app:
                    app_list_TB.insert(f"end", f'{app_name}: {app_dict[app_name]} seconds\n')
                    new_app = False
                else:
                    app_list_TB.delete(f"{app_index}.0", f"{app_index}.end")
                    app_list_TB.insert(f"{app_index}.0", f'{app_name}: {app_dict[app_name]} seconds')
        except:
            pass

        window.after(update_tick*1000, update_loop)
        
    def on_closing(): #when user close the program
        global running
        
        running = False
        
        p1.join()
        
        print("Window is closing!") #temp code
        sys.exit()

    running = True
    
    #Textbox
    app_list_TB = ctk.CTkTextbox(window, width=1080, height=360)
    app_list_TB.grid(row=0, column=0, columnspan = 2)

    time = [">1 hour", ">2 hours", '>3 hours']
    temp_quest_time = time[0]
    app_list = get_all_app_list()
    tab_list = ["Youtube", "Reddit", "Instagram", "Facebook"]
    temp_quest_app = app_list[0]
    
    #App Option
    app_dropdown = ctk.CTkComboBox(master=window,values=app_list, command=combobox_callback)
    app_dropdown.grid(row=1, column=0, padx=20, pady=10, sticky='w')

    #Time Option
    time_dropdown = ctk.CTkComboBox(master=window,values=time, command=timebox_callback)
    time_dropdown.grid(row=1, column=1, padx=20, pady=10, sticky='e')

    #Chrome Tab Option (only shown whenever Chrome is selected in the App Option, refer to combobox_callback)
    tabBox = ctk.CTkComboBox(master=window, values=tab_list, command=tabBox_callback)
    def show_tabBox():
        tabBox.grid(row=1, column=1, padx=20, pady=10)
        
    #Refresh Button
    button = ctk.CTkButton(master=window, text="Refresh", command=refresh_app_list)
    button.grid(row=2, column=0, padx=20, pady=10, sticky='e')

    #Save Button
    button = ctk.CTkButton(master=window, text="Save", command=save_quest_time)
    button.grid(row=2, column=1, padx=20, pady=10, sticky='e')

    #Quest Saved Textbox
    quest_list_TB = ctk.CTkTextbox(window, width=1080, height=360)
    quest_list_TB.grid(row=3, column=0, columnspan = 2)
    update_quest_list()
    
    #First load
    p1 = threading.Thread(target=update_time)
    
    p1.start()                      
    update_loop()

    window.protocol("WM_DELETE_WINDOW", on_closing) #check for if user close the program

    window.mainloop()
    
if __name__=="__main__":
    window()