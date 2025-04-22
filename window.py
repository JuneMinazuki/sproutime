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
    
    app_dict = {}
    app_time_list = []
    sleep_time = 1 if DEBUG else 60
    app_index = 1
    
    #App Info
    window = ctk.CTk()
    window.geometry("1080x720")
    window.title("Sproutime")
    
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
        window.destroy()
    
    app_list_TB = ctk.CTkTextbox(window, width=1080, height=720)
    app_list_TB.grid(row=0, column=0)
    
    update_loop()
    
    print(get_all_app_list())
    
    window.protocol("WM_DELETE_WINDOW", on_closing) #check for if user close the program
    
    window.mainloop()