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
            import winotify

    except ModuleNotFoundError as e:
        import tkinter
        tkinter.messagebox.showerror("Missing Libraries", str(e))

    #DEBUG
    DEBUG = 1 #Use this to lower the time check for app from minute to second to save time
    
    #SQLite Setup
    conn = sqlite3.connect('sproutime.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quest (
                id INTEGER PRIMARY KEY,
                app_name TEXT NOT NULL,
                time INTEGER NOT NULL,
                maximum INTEGER NOT NULL
            )
        ''')
        
        #if DEBUG:
            #cursor.execute(f"DELETE FROM quest")
            #conn.commit()
        
    except sqlite3.Error as e:
        if DEBUG: print(f"An error occurred: {e}")
        conn.rollback()

    global temp_quest_app, temp_quest_time, app_dict, app_time_update, update_tick, running, maximum_map, time_map, quest_dict, quest_complete_update, total_points
    
    app_dict = {}
    update_tick = 1 if DEBUG else 60
    app_time_update = False
    temp_quest_app = ""
    temp_quest_time = ""
    running = False
    counter_lock = threading.Lock()
    quest_list = []
    quest_dict = {}
    quest_complete_update = False
    completed_list = []
    total_points = 0    # Right now +100 per completed quest

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
        temp_quest_app = choice
   
    def refresh_app_list():
        global app_list
        app_list = get_all_app_list()
        
        app_dropdown.configure(values=app_list)
            
    def save_quest_time():
        global temp_quest_app, temp_quest_time
        
        #Pending changes from UI time drop-box update
        maximum_map = {'>':1, '<':0}
        time_map = {'1 hour':60, '2 hours':120, '3 hours':180}
        maximum = maximum_map.get(list(temp_quest_time)[0])
        time = time_map.get(temp_quest_time[1:])
        
        try:
            cursor.execute("SELECT COUNT(*) FROM quest WHERE app_name = ?", (temp_quest_app,)) #Check for duplicate
            result = cursor.fetchone()
            
            if result and result[0] > 0:
                cursor.execute("UPDATE quest SET time = ?, maximum = ? WHERE app_name = ?", (time, maximum, temp_quest_app))
            else:
                cursor.execute("INSERT INTO quest (app_name, time, maximum) VALUES (?, ?, ?)", (temp_quest_app, time, maximum))
            conn.commit()

        except sqlite3.Error as e:
            if DEBUG: print(f"An error occurred: {e}")
            conn.rollback()
        
        update_quest_list()

    def update_quest_list():
        try:
            cursor.execute("SELECT app_name, maximum, time FROM quest")
            quests = cursor.fetchall()
            
            quest_list_TB.delete("0.0", "end")
            quest_dict.clear()
            quest_list.clear()
            for quest in quests:
                maximum = ">" if quest[1] == 1 else "<"
                time = quest[2] / 60

                quest_list_TB.insert("0.0", f'{quest[0]} : {maximum}{time} hour\n')
                
                quest_list.append(quest[0])
                quest_dict[quest[0]] = {"maximum": maximum, "time": quest[2] * 60}
        except sqlite3.Error as e:
            if DEBUG: print(f"An error occurred: {e}")
            conn.rollback()

    def delete_quest():
        global temp_quest_app
        cursor.execute("DELETE FROM quest WHERE app_name = ?", (temp_quest_app,))
        conn.commit()
        update_quest_list()

    def quest_done_noti(app_name):
        if sys.platform == 'darwin':
            pass
            
        elif sys.platform == 'win32':
            Title = f"Quest Completed for {app_name}"
            Msg = f"Well done! You've spent enough time on {app_name}"

            noti = winotify.Notification(app_id="Sproutime",
                          title = Title,
                          msg = Msg,
                          duration = "long")
            
            noti.set_audio(winotify.audio.Default, loop=False)

            noti.show()

    def update_time():
        global app_name, app_dict, app_time_update, running, quest_complete_update
        
        while running:
            with counter_lock:
                app_name = get_active_app_name()
                if quest_list:
                    if app_name in quest_list and app_name not in completed_list:
                        if app_name in app_dict:
                            if quest_dict[app_name]["maximum"] == ">":
                                if quest_dict[app_name]["time"] > app_dict[app_name]:
                                    new_app = False
                                    app_index = list(app_dict.keys()).index(app_name) +1
                                    app_dict[app_name] += 1200
                                else:
                                    quest_complete_update = True
                                    completed_list.append(app_name)
                            else:
                                if quest_dict[app_name]["time"] < app_dict[app_name]:
                                    new_app = False
                                    app_index = list(app_dict.keys()).index(app_name) +1
                                    app_dict[app_name] += 1
                                else:
                                    pass
                        else:
                            app_dict[app_name] = 1
                    else:
                        pass
                    
                    app_time_update = True
                    sleep(1)
                else:
                    pass

    def ui_update(): #this is the while true loop
        global app_dict, app_time_update, quest_complete_update, total_points
        
        if app_time_update:
            app_list_TB.delete("0.0", "end")
            for app in app_dict:
                app_list_TB.insert("end", f'{app}: {app_dict[app]} seconds\n')
            
            app_time_update = False

        if quest_complete_update:
            completed_list_TB.insert("end", f'{completed_list[-1]} {quest_dict[completed_list[-1]]["maximum"]} {quest_dict[completed_list[-1]]["time"] / 60 / 60} hour(s): Completed +100 points\n')
            quest_done_noti(completed_list[-1])
            total_points += 100
            quest_complete_update = False

        window.after(update_tick*1000, ui_update)
        
    def on_closing(): #when user close the program
        global running
        
        running = False
        
        p1.join()
        
        conn.close()
        
        print("Window is closing!") #temp code
        sys.exit()

    running = True
    
    #Textbox
    app_list_TB = ctk.CTkTextbox(window, width=1080, height=180)
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
    time_dropdown.grid(row=1, column=2, padx=20, pady=10, sticky='e')

    #Chrome Tab Option (only shown whenever Chrome is selected in the App Option, refer to combobox_callback)
    tabBox = ctk.CTkComboBox(master=window, values=tab_list, command=tabBox_callback)
    def show_tabBox():
        tabBox.grid(row=1, column=1, padx=20, pady=10)
        
    #Refresh Button
    refresh_button = ctk.CTkButton(master=window, text="Refresh", command=refresh_app_list)
    refresh_button.grid(row=2, column=0, padx=20, pady=10, sticky='e')
    
    #Delete Button
    delete_button = ctk.CTkButton(master=window, text="Delete", command=delete_quest)
    delete_button.grid(row=2, column=1, padx=20, pady=10, sticky='e')

    #Save Button
    save_button = ctk.CTkButton(master=window, text="Save", command=save_quest_time)
    save_button.grid(row=2, column=2, padx=20, pady=10, sticky='e')

    #Quest Saved Textbox
    quest_list_TB = ctk.CTkTextbox(window, width=1080, height=180)
    quest_list_TB.grid(row=3, column=0, columnspan = 2)
    update_quest_list()

    #Completed Quests Textbox
    completed_list_TB = ctk.CTkTextbox(window, width=1080, height=180)
    completed_list_TB.grid(row=4, column=0, columnspan=2)
    
    #First load
    p1 = threading.Thread(target=update_time)
    
    p1.start()                      
    ui_update()

    window.protocol("WM_DELETE_WINDOW", on_closing) #check for if user close the program

    window.mainloop()
    
if __name__=="__main__":
    window()