
import sys

#Check OS and popup for missing libraries
try:
    import customtkinter as ctk
    import threading
    from time import sleep
    import sqlite3

    if sys.platform == 'darwin':
        import AppKit
        import ScriptingBridge
    elif sys.platform == 'win32':
        import psutil
        import win32gui
        import win32process
        import pywinauto.application
        import winotify

except ModuleNotFoundError as e:
    import tkinter
    tkinter.messagebox.showerror("Missing Libraries", str(e))

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        #App Info
        self.geometry("1280x720")
        self.title("Sproutime")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

class Tabview(ctk.CTkTabview):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, command=self.tab_changed, **kwargs)
            
        self.tab1_thread = None
        self.tab2_thread = None

        self.create_tab1_widgets()
        self.create_tab2_widgets()
        self.create_tab3_widgets()
        self.create_tab4_widgets()

        self.start_updating()

    def create_tab1_widgets(self):
        global quest_list_update
        
        self.tab1 = self.add("Progress")

        #Textbox
        self.app_list_TB = ctk.CTkTextbox(self.tab1, width=1080, height=180)
        self.app_list_TB.grid(row=0, column=0, columnspan=3)

        #App Option
        self.app_dropdown = ctk.CTkComboBox(self.tab1,values=app_list, command=self.combobox_callback)
        self.app_dropdown.grid(row=1, column=0,sticky='w')

        #Time Option
        self.time_dropdown = ctk.CTkComboBox(self.tab1,values=time, command=self.timebox_callback)
        self.time_dropdown.grid(row=1, column=2,sticky='e')

        #Chrome Tab Option (only shown whenever Chrome is selected in the App Option, refer to combobox_callback)
        self.tabBox = ctk.CTkComboBox(self.tab1, values=tab_list, command=self.tabBox_callback)
        self.tabBox.grid(row=1, column=1, padx=20, pady=10)
        self.tabBox.set(tab_list[0])
        self.tabBox.grid_remove()
            
        #Refresh Button
        self.refresh_button = ctk.CTkButton(self.tab1, text="Refresh", command=self.refresh_app_list)
        self.refresh_button.grid(row=2, column=0, sticky='w')
        
        #Delete Button
        self.delete_button = ctk.CTkButton(self.tab1, text="Delete", command=self.delete_quest)
        self.delete_button.grid(row=2, column=1, sticky='e')

        #Save Button
        self.save_button = ctk.CTkButton(self.tab1, text="Save", command=self.save_quest_time)
        self.save_button.grid(row=2, column=2, sticky='e')

        #Quest Saved Textbox
        self.quest_list_TB = ctk.CTkTextbox(self.tab1, width=1080, height=180)
        self.quest_list_TB.grid(row=3, column=0, columnspan = 3)
        quest_list_update = True

        for col in range(3):
            self.tab1.columnconfigure(col, weight=1)

        for row in range(5):
            self.tab1.rowconfigure(row, weight=1)
            
        #Debug Button
        debug_button = ctk.CTkButton(master=self.tab1, text="Debug", command=self.open_debug_menu)
        debug_button.grid(row=5, column=0, padx=20, pady=10, sticky='w')

    def create_tab2_widgets(self):
        self.tab2 = self.add("Score")

        #Completed Quests Textbox
        self.completed_list_TB = ctk.CTkTextbox(self.tab2, width=1080, height=180)
        self.completed_list_TB.grid(row=0, column=0, columnspan=3)

        for col in range(1):
            self.tab2.columnconfigure(col, weight=1)

    def create_tab3_widgets(self):
        self.tab3 = self.add("Stats")


    def create_tab4_widgets(self):
        self.tab4 = self.add("Settings")
        theme_selector = ctk.CTkOptionMenu(master=self.tab4, values=theme_options, command=lambda theme: ctk.set_appearance_mode(theme))  # Change theme
        theme_selector.pack(padx=20, pady=20)
        theme_selector.set("System")  # Set default theme to "System"

    def update_tab1(self):
        global app_dict, app_time_update, quest_complete_update, total_points, quest_list_update
        
        while running:
            if app_time_update:
                self.app_list_TB.delete("0.0", "end")
                for app in app_dict:
                    self.app_list_TB.insert("end", f'{app}: {app_dict[app]} seconds\n')
                
                app_time_update = False

            if quest_complete_update:
                self.completed_list_TB.insert("end", f'{completed_list[-1]} {quest_dict[completed_list[-1]]["maximum"]} {quest_dict[completed_list[-1]]["time"] / 60 / 60} hour(s): Completed +100 points\n')
                quest_done_noti(completed_list[-1])
                total_points += 100
                quest_complete_update = False
                
            if quest_list_update:
                conn = sqlite3.connect('sproutime.db')
                cursor = conn.cursor()
                
                try:
                    cursor.execute("SELECT app_name, maximum, time FROM quest")
                    quests = cursor.fetchall()
                    
                    self.quest_list_TB.delete("0.0", "end")
                    quest_dict.clear()
                    quest_list.clear()
                    for quest in quests:
                        maximum = ">" if quest[1] == 1 else "<"
                        time = quest[2] / 60

                        self.quest_list_TB.insert("0.0", f'{quest[0]} : {maximum}{time} hour\n')
                        
                        quest_list.append(quest[0])
                        quest_dict[quest[0]] = {"maximum": maximum, "time": quest[2] * 60}
                except sqlite3.Error as e:
                    if DEBUG: print(f"An error occurred: {e}")
                    conn.rollback()
                finally:
                    if conn:
                        conn.close()
                quest_list_update = False

            sleep(update_tick)

    def start_updating(self):
        tab = self.get()
        self.is_tab1_active = tab == "Progress"
        self.is_tab2_active = tab == "Score"

        if self.is_tab1_active and (self.tab1_thread is None or not self.tab1_thread.is_alive()):
            self.tab1_thread = threading.Thread(target=self.update_tab1, daemon=True)
            self.tab1_thread.start()

    def tab_changed(self):
        self.start_updating()

    def combobox_callback(self, choice):  
        global temp_quest_app
        temp_quest_app = choice
        if choice == "Google Chrome":
            self.tabBox.grid()
        else:
            self.tabBox.grid_remove()

    def tabBox_callback(self, choice):
        global temp_quest_tab
        temp_quest_tab = choice

    def timebox_callback(self, choice):
        global temp_quest_time
        temp_quest_time = choice

    def refresh_app_list(self):
        self.app_dropdown.configure(values=get_all_app_list())

    def delete_quest(self):
        global temp_quest_app, quest_list_update
        
        conn = sqlite3.connect('sproutime.db')
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM quest WHERE app_name = ?", (temp_quest_app,))
            conn.commit()
        except sqlite3.Error as e:
            if DEBUG: print(f"An error occurred: {e}")
            conn.rollback()
        finally:
            if conn:
                conn.close()
        
        quest_list_update = True

    def save_quest_time(self):
        global temp_quest_app, temp_quest_tab, temp_quest_time
        max_map = {'>': 1, '<': 0}
        time_map = {'1 hour': 60, '2 hours': 120, '3 hours': 180}
        maximum = max_map.get(temp_quest_time[0])
        minutes = time_map.get(temp_quest_time[1:])
        name = temp_quest_tab if temp_quest_app == "Google Chrome" and temp_quest_tab != "Any Tabs" else temp_quest_app

        conn = sqlite3.connect('sproutime.db')
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT COUNT(*) FROM quest WHERE app_name = ?", (name,))
            if cursor.fetchone()[0] > 0:
                cursor.execute("UPDATE quest SET time = ?, maximum = ? WHERE app_name = ?", (minutes, maximum, name))
            else:
                cursor.execute("INSERT INTO quest (app_name, time, maximum) VALUES (?, ?, ?)", (name, minutes, maximum))
            conn.commit()
        except sqlite3.Error as e:
            if DEBUG: print(f"An error occurred: {e}")
            conn.rollback()
        finally:
            if conn:
                conn.close()

        quest_list_update = True
        
    def open_debug_menu(self):
        global debug_menu
    
        if debug_menu is None or debug_menu.winfo_exists():
            debug_menu = DebugMenu(self)  # Pass the main window as parent
        else:
            debug_menu.focus()
        
class DebugMenu(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.geometry("250x300")
        self.title("Debug Menu")
        
        self.setup_menu()

        self.protocol("WM_DELETE_WINDOW", self.close_debug_menu) # Handle window closing

    def setup_menu(self):
        global _d_time_speed
        
        self.grid_columnconfigure((0,1), weight=1)

        #Speed up time
        self.time_speed_label = ctk.CTkLabel(master=self, text="Speed Up")
        self.time_speed_label.grid(row=0, column=0, padx=20, pady=10, sticky='w')
        self.time_speed_checkbox = ctk.CTkCheckBox(master=self, text='', variable=_d_time_speed,
                                                    onvalue=3600, offvalue=1, width=10)
        self.time_speed_checkbox.grid(row=0, column=1, padx=20, pady=10, sticky='e')
        
        #Drop every table
        self.drop_table_button = ctk.CTkButton(master=self, text="Reset Database", command=self.reset_database)
        self.drop_table_button.grid(row=1, column=0, padx=20, pady=10, sticky='ew', columnspan = 2)

    def reset_database(self):
        global app_time_update, quest_complete_update, quest_list_update
        
        conn = sqlite3.connect('sproutime.db')
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()

            for table in tables:
                table_name = table[0]
                try:
                    cursor.execute(f"DROP TABLE IF EXISTS {table_name};")
                    if DEBUG: print(f"Dropped table: {table_name}")
                except sqlite3.Error as e:
                    if DEBUG: print(f"Error dropping table {table_name}: {e}")
            conn.commit()
        except sqlite3.Error as e:
            if DEBUG: print(f"An error occurred: {e}")
            conn.rollback()
        finally:
            if conn:
                conn.close()
        
        setup_sql()
        app_time_update = True
        quest_list_update = True
        #quest_complete_update = True
        

    def close_debug_menu(self):
        global debug_menu
        debug_menu = None
        self.destroy() 
    
def setup_sql():   
    conn = sqlite3.connect('sproutime.db')
    cursor = conn.cursor()
 
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quest (
                quest_id INTEGER PRIMARY KEY,
                app_name TEXT NOT NULL,
                time INTEGER NOT NULL,
                maximum INTEGER NOT NULL
            );
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quest_completion (
                date TEXT PRIMARY KEY, --Store as YYYY-MM-DD
                quest_id TEXT NOT NULL,
                score_earn INTEGER NOT NULL,
                FOREIGN KEY(quest_id) REFERENCES quest(quest_id)
            );
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS app_time (
                log_id INTEGER PRIMARY KEY,
                app_name TEXT NOT NULL,
                date TEXT NOT NULL, --Store as YYYY-MM-DD
                duration INTEGER NOT NULL
            );
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS streak (
                date TEXT PRIMARY KEY, --Store as YYYY-MM-DD
                quest_completed INTEGER NOT NULL,
                quest_Set INTEGER NOT NULL
            );
        ''')
    except sqlite3.Error as e:
        if DEBUG: print(f"An error occurred: {e}")
        conn.rollback()
    finally:
        if conn:
            conn.close()

def get_active_app_name():
    if sys.platform == 'darwin':
        appName = AppKit.NSWorkspace.sharedWorkspace().activeApplication()['NSApplicationName']
        
        if appName == "Google Chrome": 
            tabName = get_active_tab_name()
            if tabName == "URL not detected":
                pass
            else:
                appName = tabName
        
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
        chrome = ScriptingBridge.SBApplication.applicationWithBundleIdentifier_("com.google.Chrome")
        if not chrome.windows():
            return "URL not detected"

        window = chrome.windows()[0]  # Get the first window
        url = window.activeTab().URL() # Get the active tab in the window
        tab = url.split('/')[2]
        
        match tab:
            case "www.youtube.com":
                tabName = "Youtube"
            case "www.reddit.com":
                tabName = "Reddit"
            case "www.instagram.com":
                tabName = "Instagram"
            case "www.facebook.com":
                tabName = "Facebook"
            case _:
                tabName = "Google Chrome"

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
    global app_name, app_dict, app_time_update, running, quest_complete_update, quest_dict, tab_list, _d_time_speed
    
    while running:
        with time_lock:
            app_name = get_active_app_name()
            if quest_list:
                if app_name in quest_list and app_name not in completed_list:
                    if app_name in app_dict:
                        if quest_dict[app_name]["maximum"] == ">":
                            if quest_dict[app_name]["time"] > app_dict[app_name]:
                                app_dict[app_name] += _d_time_speed.get()
                            else:
                                quest_complete_update = True
                                completed_list.append(app_name)
                        else:
                            if quest_dict[app_name]["time"] < app_dict[app_name]:
                                app_dict[app_name] += 1
                                if app_name in tab_list:
                                    app_dict["Google Chrome"] += _d_time_speed.get()
                            else:
                                pass
                    else:
                        app_dict[app_name] = _d_time_speed.get()
                else:
                    pass
                
                app_time_update = True
                sleep(1)
            else:
                pass

def on_closing(): #when user close the program
    global running
    
    running = False
    
    p1.join()
    
    print("Window is closing!") #temp code
    sys.exit()

#DEBUG
DEBUG = 1 #Use this to lower the time check for app from minute to second to save time

setup_sql()

app = App()

#Thread Setup
running = False
time_lock = threading.Lock()

##Global Var
update_tick = 1 if DEBUG else 60
app_dict = {}
temp_quest_app = ""
temp_quest_tab = ""
temp_quest_time = ""
web_browser = ["Google Chrome"]
quest_list = []
quest_dict = {}
completed_list = []
total_points = 0    # Right now +100 per completed quest

#Debug Menu Var
debug_menu = None
_d_time_speed = ctk.IntVar(value=1)

#GUI Update Request
app_time_update = False
quest_list_update = False
quest_complete_update = False

running = True

time = [">1 hour", ">2 hours", '>3 hours']
temp_quest_time = time[0]
app_list = get_all_app_list()
tab_list = ["Any Tabs", "Youtube", "Reddit", "Instagram", "Facebook"]
temp_quest_app = app_list[0]
temp_quest_tab = tab_list[0]
theme_options = ["Light", "Dark", "System"]

#First load
p1 = threading.Thread(target=update_time)

p1.start()

Tabview(master=app).grid(row=0, column=0, columnspan=2, sticky="nsew")
app.protocol("WM_DELETE_WINDOW", on_closing)
app.mainloop()