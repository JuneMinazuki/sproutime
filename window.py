import sys

#Check OS and popup for missing libraries
try:
    import customtkinter as ctk
    import threading
    from time import sleep
    import sqlite3
    from datetime import datetime, date, timedelta

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
            
        self.progress_thread = None
        self.quest_thread = None
        self.score_thread = None
        self.stats_thread = None

        self.create_progress_widgets()
        self.create_quest_widgets()
        self.create_score_widgets()
        self.create_stats_widgets()
        self.create_setting_widgets()
        self.create_changeappname_widgets()
        self.create_bar()

        self.start_updating()

    def create_progress_widgets(self):
        self.tab1 = self.add("Progress")

        #Textbox
        self.app_list_TB = ctk.CTkTextbox(self.tab1, width=1080, height=180)
        self.app_list_TB.grid(row=0, column=0, columnspan=4)

        for col in range(3):
            self.tab1.columnconfigure(col, weight=1)

        for row in range(5):
            self.tab1.rowconfigure(row, weight=1)

    def create_quest_widgets(self):
        global quest_list_update
        self.tab2 = self.add("Quest")

        #App Option
        self.app_dropdown = ctk.CTkComboBox(self.tab2,values=app_list, command=self.combobox_callback)
        self.app_dropdown.grid(row=0, column=0, padx=10, pady=20, sticky='w')

        #Time Option
        self.time_dropdown = ctk.CTkComboBox(self.tab2,values=time, command=self.timebox_callback)
        self.time_dropdown.grid(row=0, column=2, padx=10, pady=20, sticky='e')

        #Chrome Tab Option (only shown whenever Chrome is selected in the App Option, refer to combobox_callback)
        self.tabBox = ctk.CTkComboBox(self.tab2, values=tab_list, command=self.tabBox_callback)
        self.tabBox.grid(row=0, column=1)
        self.tabBox.set(tab_list[0])
        self.check_for_chrome()    
        
        #Refresh Button
        self.refresh_button = ctk.CTkButton(self.tab2, text="Refresh", command=self.refresh_app_list)
        self.refresh_button.grid(row=1, column=0, padx=10, pady=20, sticky='w')
        
        #Delete Button
        self.delete_button = ctk.CTkButton(self.tab2, text="Delete", command=self.delete_quest)
        self.delete_button.grid(row=1, column=1, padx=10, pady=20, sticky="e")

        #Save Button
        self.save_button = ctk.CTkButton(self.tab2, text="Save", command=self.save_quest_time)
        self.save_button.grid(row=1, column=2, padx=10, pady=20, sticky='e')

        #Quest Saved Textbox
        self.quest_list_TB = ctk.CTkTextbox(self.tab2, width=1080, height=180)
        self.quest_list_TB.grid(row=2, column=0, padx=10, pady=20, columnspan = 3)
        quest_list_update = True

    def create_score_widgets(self):
        self.tab3 = self.add("Score")

        #Completed Quests Textbox
        self.completed_list_TB = ctk.CTkTextbox(self.tab3, width=1080, height=180)
        self.completed_list_TB.grid(row=0, column=0, columnspan=3)

        for col in range(1):
            self.tab3.columnconfigure(col, weight=1)
        
    def create_stats_widgets(self):
        self.tab4 = self.add("Stats")

    def create_setting_widgets(self):
        self.tab5 = self.add("Settings")
        
        #Theme
        self.theme_selector = ctk.CTkOptionMenu(master=self.tab5, values=theme_options, command=lambda theme: ctk.set_appearance_mode(theme))  # Change theme
        self.theme_selector.pack(padx=20, pady=10)
        self.theme_selector.set("System")  # Set default theme to "System"
        
        #Debug Button
        self.debug_button = ctk.CTkButton(master=self.tab5, text="Debug", command=self.open_debug_menu)
        self.debug_button.pack(padx=20, pady=10)

    def create_changeappname_widgets(self):
        self.tab6 = self.add("Change App Name")

        self.appname_widgets = []  

        # Scrollable frame for name changer
        self.scrollable_frame = ctk.CTkScrollableFrame(self.tab6)
        self.scrollable_frame.pack(fill="both", expand=True)

        for i, app in enumerate(app_list):
            label = ctk.CTkLabel(self.scrollable_frame, text=app)
            label.grid(row=i, column=0, sticky="w", padx=10, pady=5)

            entry = ctk.CTkEntry(self.scrollable_frame, placeholder_text="New name")
            entry.grid(row=i, column=1, sticky="ew", padx=10, pady=5)

            self.appname_widgets.append((label, entry))

        # Add Change Name Button
        save_button = ctk.CTkButton(self.scrollable_frame, text="Change", command=self.change_app_name)
        save_button.grid(row=0, column=2, padx=10, pady=5)

    def create_bar(self):
        self.tab7 = self.add("Progress Bar")
        self.add_progress_button = ctk.CTkButton(self.tab7, text="Add", command=self.add_progress_bar)
        self.add_progress_button.pack(pady=10)

        self.progress_frame = ctk.CTkFrame(self.tab7)
        self.progress_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.progress_bars = []
        

    def add_progress_bar(self):
        # Frame for each progress bar
        bar_frame = ctk.CTkFrame(self.progress_frame)
        bar_frame.pack(fill="x", pady=5)

        # Editable text above progress bar
        text_entry = ctk.CTkEntry(bar_frame, placeholder_text="Enter text here")
        text_entry.pack(anchor="w", fill="x", padx=5, pady=2)

        # Progress bar
        progress_bar = ctk.CTkProgressBar(bar_frame)
        progress_bar.set(0.1)  # Set initial progress to 10%
        progress_bar.pack(fill="x", padx=5, pady=5)

        # Increase progress button
        increase_button = ctk.CTkButton(bar_frame, text="Increase", width=80, command=lambda: self.increase_progress(progress_bar))
        increase_button.pack(pady=5)

        # Delete button
        delete_button = ctk.CTkButton(bar_frame, text="Delete", width=80, command=lambda: self.delete_progress_bar(bar_frame))
        delete_button.pack(pady=5)

        self.progress_bars.append(bar_frame)

    def increase_progress(self, progress_bar):
        current_value = progress_bar.get()
        new_value = min(current_value + 0.1, 1.0)  # initial progress to 10%, max is 100%
        progress_bar.set(new_value)

    def delete_progress_bar(self, bar_frame):
        bar_frame.destroy()
        self.progress_bars.remove(bar_frame)


    def update_progress(self):
        global running, app_time_update, app_dict, update_tick, appname_dict
        
        while running:
            if app_time_update:
                self.app_list_TB.delete("0.0", "end")
                for app in app_dict:
                    if appname_dict and app in self.old_name_list:
                        self.app_list_TB.insert("end", f'{appname_dict[app]}: {app_dict[app]} seconds\n')
                    else:
                        self.app_list_TB.insert("end", f'{app}: {app_dict[app]} seconds\n')
                
                app_time_update = False
                
            sleep(update_tick)

    def update_quest(self):
        global running, quest_list_update, quest_dict, quest_list, update_tick
        
        while running:
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

                        self.quest_list_TB.insert("0.0", f'{quest[0]} : {maximum}{quest[2] / 60} hour\n')
                        
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
            
    def update_score(self):
        global running, quest_complete_update, update_tick
        
        while running:
            if quest_complete_update:
                conn = sqlite3.connect('sproutime.db')
                cursor = conn.cursor()
                
                try:
                    cursor.execute("SELECT app_name, time, maximum, score_earn FROM quest_completion")
                    quests = cursor.fetchall()
                    
                    self.completed_list_TB.delete("0.0", "end")
                    for quest in quests:
                        maximum = ">" if quest[2] == 1 else "<"
                        
                        self.completed_list_TB.insert("end", f'{quest[0]} {maximum} {int(quest[1]) / 60} hour(s): Completed +{quest[3]} points\n')
                except sqlite3.Error as e:
                    if DEBUG: print(f"An error occurred: {e}")
                    conn.rollback()
                finally:
                    if conn:
                        conn.close()

                quest_complete_update = False
            sleep(update_tick)

    def update_stats(self): 
        global running, update_tick
               
        while running:
            sleep(update_tick)
            
    def start_updating(self):
        tab = self.get()
        self.progress_active = tab == "Progress"
        self.quest_active = tab == "Quest"
        self.score_active = tab == "Score"
        self.stats_active = tab == "Stats"

        #Progess Tab
        if self.progress_active and (self.progress_thread is None or not self.progress_thread.is_alive()):
            self.progress_thread = threading.Thread(target=self.update_progress, daemon=True)
            self.progress_thread.start()
        elif not self.progress_active and self.progress_thread and self.progress_thread.is_alive():
            # The thread will naturally pause in its while loop
            pass
        
        #Quest Tab
        if self.quest_active and (self.quest_thread is None or not self.quest_thread.is_alive()):
            self.quest_thread = threading.Thread(target=self.update_quest, daemon=True)
            self.quest_thread.start()
        elif not self.progress_active and self.quest_thread and self.quest_thread.is_alive():
            # The thread will naturally pause in its while loop
            pass
        
        #Score Tab
        if self.score_active and (self.score_thread is None or not self.score_thread.is_alive()):
            self.score_thread = threading.Thread(target=self.update_score, daemon=True)
            self.score_thread.start()
        elif not self.score_active and self.score_thread and self.score_thread.is_alive():
            # The thread will naturally pause in its while loop
            pass
        
        #Stats Tab
        if self.stats_active and (self.stats_thread is None or not self.stats_thread.is_alive()):
            self.stats_thread = threading.Thread(target=self.update_progress, daemon=True)
            self.stats_thread.start()
        elif not self.stats_active and self.stats_thread and self.stats_thread.is_alive():
            # The thread will naturally pause in its while loop
            pass

    def tab_changed(self):
        self.start_updating()

    def combobox_callback(self, choice):  
        global temp_quest_app
        temp_quest_app = choice
        self.check_for_chrome()
            
    def check_for_chrome(self): 
        global temp_quest_app
         
        if temp_quest_app == google:
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
        global temp_quest_app, temp_quest_tab, temp_quest_time, quest_list_update
        max_map = {'>': 1, '<': 0}
        time_map = {'1 hour': 60, '2 hours': 120, '3 hours': 180}
        maximum = max_map.get(temp_quest_time[0])
        minutes = time_map.get(temp_quest_time[1:])
        name = temp_quest_tab if temp_quest_app == google and temp_quest_tab != "Any Tabs" else temp_quest_app

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

    def change_app_name(self):
        global appname_dict

        self.old_name_list = []

        for label, entry in self.appname_widgets:
            new_name = entry.get().strip()
            if new_name: 
                original_name = label.cget("text")
                appname_dict[original_name] = new_name
                self.old_name_list.append(original_name)
        
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
        
        #Clear quest
        self.drop_table_button = ctk.CTkButton(master=self, text="Clear Quest", command=self.clear_quest)
        self.drop_table_button.grid(row=1, column=0, padx=20, pady=10, sticky='ew', columnspan = 2)
        
        #Clear quest_completion
        self.drop_table_button = ctk.CTkButton(master=self, text="Clear Completed", command=self.clear_completed)
        self.drop_table_button.grid(row=2, column=0, padx=20, pady=10, sticky='ew', columnspan = 2)
        
        #Clear app_time
        self.drop_table_button = ctk.CTkButton(master=self, text="Clear App Time", command=self.clear_app)
        self.drop_table_button.grid(row=3, column=0, padx=20, pady=10, sticky='ew', columnspan = 2)
        
        #Clear streak
        self.drop_table_button = ctk.CTkButton(master=self, text="Clear Streak", command=self.clear_quest_streak)
        self.drop_table_button.grid(row=4, column=0, padx=20, pady=10, sticky='ew', columnspan = 2)
        
        #Drop every table
        self.drop_table_button = ctk.CTkButton(master=self, text="Reset Database", command=self.reset_database)
        self.drop_table_button.grid(row=5, column=0, padx=20, pady=10, sticky='ew', columnspan = 2)

    def clear_quest(self):
        global quest_list_update
        
        conn = sqlite3.connect('sproutime.db')
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM quest")
            conn.commit()
        except sqlite3.Error as e:
            if DEBUG: print(f"An error occurred: {e}")
            conn.rollback()
        finally:
            if conn:
                conn.close()
        
        quest_list_update = True
    
    def clear_completed(self):
        global quest_complete_update
        
        conn = sqlite3.connect('sproutime.db')
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM quest_completion")
            conn.commit()
        except sqlite3.Error as e:
            if DEBUG: print(f"An error occurred: {e}")
            conn.rollback()
        finally:
            if conn:
                conn.close()
        
        quest_complete_update = True
    
    def clear_app(self):
        global app_time_update, app_dict
        
        conn = sqlite3.connect('sproutime.db')
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM app_time")
            conn.commit()
        except sqlite3.Error as e:
            if DEBUG: print(f"An error occurred: {e}")
            conn.rollback()
        finally:
            if conn:
                conn.close()
        
        app_dict = {}
        app_time_update = True
        
    def clear_quest_streak(self):    
        conn = sqlite3.connect('sproutime.db')
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM quest")
            conn.commit()
        except sqlite3.Error as e:
            if DEBUG: print(f"An error occurred: {e}")
            conn.rollback()
        finally:
            if conn:
                conn.close()
            
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
        quest_complete_update = True
        
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
                log_id INTEGER PRIMARY KEY,
                date TEXT NOT NULL, --Store as YYYY-MM-DD
                app_name TEXT NOT NULL,
                time INTEGER NOT NULL,
                maximum INTEGER NOT NULL,
                score_earn INTEGER NOT NULL
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
        _, pid = win32process.GetWindowThreadProcessId(foregroundApp)
        process = psutil.Process(pid)
        process_name = process.name()
        appName = process_name.split(".")[0].capitalize()
        if appName == "Chrome": 
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
            for process in psutil.process_iter(['pid', 'name']):
                pid = process.info['pid']
                ignored_processes = ["Applicationframehost", "Textinputhost"]

                def enumWindowsArguments(handle, __):
                    threadID, foundPID = win32process.GetWindowThreadProcessId(handle)

                    if foundPID == pid and win32gui.IsWindowVisible(handle):
                        window_title = win32gui.GetWindowText(handle)
                        app_name = process.info["name"].split(".")[0].capitalize() # Get all active app name
                        if app_name not in app_list and app_name not in ignored_processes: 
                            app_list.append(app_name)

                win32gui.EnumWindows(enumWindowsArguments, None)
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
            case "www.linkedin.com":
                tabName = "LinkedIn"
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

def load_past_data():
    global app_time_update, app_dict, completed_list, failed_list
    
    conn = sqlite3.connect('sproutime.db')
    cursor = conn.cursor()
    
    try:
        #App Time
        cursor.execute("SELECT app_name, duration FROM app_time WHERE date = ?", (str(date.today()),))
        apps = cursor.fetchall()
        
        for app in apps:
            app_dict[app[0]] = app[1]
            
        #Completed quest
        cursor.execute("SELECT app_name FROM quest_completion WHERE date = ?", (str(date.today()),))
        apps = cursor.fetchall()
        
        for app in apps:
            completed_list.append(app[0])
    except sqlite3.Error as e:
        if DEBUG: print(f"An error occurred: {e}")
        conn.rollback()
    finally:
        if conn:
            conn.close()
            
    app_time_update = True


def update_time():
    global app_name, app_dict, app_time_update, running, quest_complete_update, quest_dict, _d_time_speed, task_score, total_points, completed_list
    
    while running:
        now = datetime.now()

        if now.hour == 0 and now.minute == 0:
            today = str(date.today() - timedelta(days = 1))
            update_log(today)
        
        with time_lock:
            app_name = get_active_app_name()
            
            if (app_name == "Python") or (app_name == "Sproutime"):
                sleep(1)
                continue
            
            if app_name in app_dict:
                app_dict[app_name] += _d_time_speed.get()
            else:
                app_dict[app_name] = _d_time_speed.get()
                
            if (quest_list) and (app_name in quest_list) and (app_name not in completed_list) and (app_name not in failed_list) and (quest_dict[app_name]["time"] <= app_dict[app_name]):
                if quest_dict[app_name]["maximum"] == ">":
                    conn = sqlite3.connect('sproutime.db')
                    cursor = conn.cursor()
                    
                    try:
                        cursor.execute("SELECT time, maximum FROM quest WHERE app_name = ?", (app_name,))
                        quest = cursor.fetchone()
                        quest_time = quest[0]
                        maximum = quest[1]
                        
                        cursor.execute("INSERT INTO quest_completion (date, app_name, time, maximum, score_earn) VALUES (?, ?, ?, ?, ?)", (str(date.today()), app_name, quest_time, maximum, task_score))
                        conn.commit()
                    except sqlite3.Error as e:
                        if DEBUG: print(f"An error occurred: {e}")
                        conn.rollback()
                    finally:
                        if conn:
                            conn.close()

                    completed_list.append(app_name)
                    quest_done_noti(app_name)
                    total_points += task_score
                            
                elif quest_dict[app_name]["maximum"] == "<":
                    failed_list.append(app_name)
                quest_complete_update = True

            app_time_update = True
            sleep(1)
    
def update_log(today):
    global app_dict
    conn = sqlite3.connect('sproutime.db')
    cursor = conn.cursor()
    
    try:
        for app in app_dict:
            cursor.execute("SELECT COUNT(*) FROM app_time WHERE app_name = ? AND date = ?", (app, today))
            if cursor.fetchone()[0] > 0:
                cursor.execute("UPDATE app_time SET duration = ? WHERE app_name = ?", (app_dict[app], app))
            else:
                cursor.execute("INSERT INTO app_time (app_name, date, duration) VALUES (?, ?, ?)", (app, today, app_dict[app]))
        conn.commit()
        app_dict = {}
    except sqlite3.Error as e:
        if DEBUG: print(f"An error occurred: {e}")
        conn.rollback()
    finally:
        if conn:
            conn.close()

def on_closing(): #when user close the program
    global running
    
    running = False
    
    p1.join()
    
    update_log(str(date.today()))
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
failed_list = []
total_points = 0    # Right now +100 per completed quest
task_score = 100

google = "Google Chrome"

if sys.platform == "win32":
    google = "Chrome"

appname_dict = {} # used in name changer

#Debug Menu Var
debug_menu = None
_d_time_speed = ctk.IntVar(value=1)

#GUI Update Request
app_time_update = False
quest_list_update = False
quest_complete_update = True

#First load
running = True

time = [">1 hour", ">2 hours", '>3 hours', '<1 hours', '<2 hours']
temp_quest_time = time[0]
app_list = get_all_app_list()
tab_list = ["Any Tabs", "Youtube", "Reddit", "Instagram", "Facebook", "LinkedIn"]
theme_options = ["Light", "Dark", "System"]
temp_quest_app = app_list[0]
temp_quest_tab = tab_list[0]
load_past_data()

p1 = threading.Thread(target=update_time)

p1.start()

Tabview(master=app).grid(row=0, column=0, columnspan=2, sticky="nsew")
app.protocol("WM_DELETE_WINDOW", on_closing)
app.mainloop()