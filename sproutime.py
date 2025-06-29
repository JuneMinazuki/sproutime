import subprocess
import sys
import math

#Check OS and popup for missing libraries
try:
    import customtkinter as ctk
    import threading
    from time import sleep
    import sqlite3
    from datetime import datetime, date, timedelta
    from PIL import Image, ImageTk
    import json
    import os
    from pathlib import Path
    import tkinter.filedialog as filedialog
    import shutil

    if sys.platform == 'darwin':
        import AppKit
        import ScriptingBridge
        import subprocess
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
        self.activity_thread = None
        self.stats_thread = None
        self.treeview_thread = None

        #Create widget
        self.create_progress_widgets()
        self.create_quest_widgets()
        self.create_activity_widgets()
        self.create_stats_widgets()
        self.create_setting_widgets()
        self.create_treeview_widgets()

        self.start_updating()

    def create_progress_widgets(self):
        self.progress_tab = self.add("Progress")

        self.progress_sort_frame = ctk.CTkFrame(self.progress_tab, height=100, width=300)
        self.progress_sort_frame.grid(row=0, column=0, pady=(20,10))

        self.progress_search_label = ctk.CTkLabel(self.progress_sort_frame, text="Search by name:")
        self.progress_search_label.grid(row=0, column=0, padx=(0,6))

        self.progress_search_entry = ctk.CTkEntry(self.progress_sort_frame)
        self.progress_search_entry.grid(row=0, column=1, padx=(0,40))

        self.progress_sort_label = ctk.CTkLabel(self.progress_sort_frame, text="Sort by :")
        self.progress_sort_label.grid(row=0, column=2, padx=(0,6))

        sort_choices = ["Oldest", "Newest", "Longest Screentime", "Shortest Screentime", "Quests"]

        self.progress_sort_combobox = ctk.CTkComboBox(self.progress_sort_frame, width=160, values=sort_choices)
        self.progress_sort_combobox.grid(row=0, column=3, padx=(0,40))

        self.progress_search_button = ctk.CTkButton(self.progress_sort_frame, text="Search", command=self.progress_search)
        self.progress_search_button.grid(row=0, column=4)

        #Scrollable frame for progress bar
        self.progress_scrollable = ctk.CTkScrollableFrame(self.progress_tab, width=1080, height=500)
        self.progress_scrollable.grid(row=1, column=0)
        bg_color = self.progress_scrollable.cget("fg_color") # Get the background color of the scrollable frame
        self.progress_scrollable.configure( # Hide the scrollbar by making its colors the same as the background
            scrollbar_fg_color=bg_color,
            scrollbar_button_color=bg_color,
            scrollbar_button_hover_color=bg_color
        )
        self.progress_scrollable.grid_columnconfigure(0, weight=1)

        self.no_results_label = ctk.CTkLabel(self.progress_scrollable, text="No results")
        self.no_results_label.grid(row=0, pady=40)
        self.no_results_label.grid_remove()

        for col in range(1):
            self.progress_tab.grid_columnconfigure(col, weight=1)

        for row in range(1):
            self.progress_tab.grid_rowconfigure(row, weight=1)

    def create_quest_widgets(self):
        global quest_list_update
        self.quest_tab = self.add("Quest")
        
        self.quest_vars = {}
        self.quest_widgets = {}

        self.set_quest_frame = ctk.CTkFrame(self.quest_tab)
        self.set_quest_frame.pack(padx=100, fill="x")
        
        self.set_quest_frame.columnconfigure((0,1), weight=1)
        
        #App Option
        self.app_dropdown = ctk.CTkComboBox(self.set_quest_frame,values=app_list, command=self.combobox_callback)
        self.app_dropdown.grid(row=0, column=0, padx=10, pady=(20,0), sticky='w')
        
        #Maximum Option
        self.maximum_switch = ctk.CTkSwitch(master=self.set_quest_frame, text="", command=self.maximum_callback, variable=switch_var, onvalue=">", offvalue="<")
        self.maximum_switch.grid(row=0, column=2, padx=(10,0), pady=(20,0), sticky='e')
        
        #Time Option
        self.time_dropdown = ctk.CTkSlider(master=self.set_quest_frame, from_=1, to=12, number_of_steps=12, variable=slider_var, command=self.time_callback)
        self.time_dropdown.grid(row=0, column=3, padx=(0,10), pady=(20,0), sticky='e')
        
        self.quest_time_label = ctk.CTkLabel(self.set_quest_frame, text=f"{switch_var.get()}{slider_var.get()} hour(s)")
        self.quest_time_label.grid(row=1, column=3, padx=10, pady=(0,20), sticky='e')

        #Chrome Tab Option (only shown whenever Chrome is selected in the App Option, refer to combobox_callback)
        self.tabBox = ctk.CTkComboBox(self.set_quest_frame, values=tab_list, command=self.tabBox_callback)
        self.tabBox.grid(row=0, column=1, pady=(20,0), sticky="w")
        self.tabBox.set(tab_list[0])
        self.check_for_chrome()    
        
        #Refresh Button
        self.refresh_button = ctk.CTkButton(self.set_quest_frame, text="Refresh", command=self.refresh_app_list)
        self.refresh_button.grid(row=2, column=0, padx=10, pady=10, sticky='w')
        
        #Save Button
        self.save_button = ctk.CTkButton(self.set_quest_frame, text="Save", command=self.save_quest_time)
        self.save_button.grid(row=2, column=3, padx=10, pady=10, sticky='e')

        #Quest Saved Frame
        self.quest_list_frame = ctk.CTkScrollableFrame(self.quest_tab, width=1080, height=400)
        bg_color = self.quest_list_frame.cget("fg_color") # Get the background color of the scrollable frame
        self.quest_list_frame.configure( # Hide the scrollbar by making its colors the same as the background
            scrollbar_fg_color=bg_color,
            scrollbar_button_color=bg_color,
            scrollbar_button_hover_color=bg_color
        )
        self.quest_list_frame.pack(padx=10, pady=15)
        
        self.export_import_frame = ctk.CTkFrame(self.quest_tab)
        self.export_import_frame.pack(padx=100, fill="x")
        
        self.export_import_frame.columnconfigure((0,1), weight=1)
        
        #Import Button
        self.import_button = ctk.CTkButton(self.export_import_frame, text="Import Quest", command=self.upload_quest_json)
        self.import_button.grid(row=0, column=0, padx=10, sticky='w')
        
        #Export Button
        self.export_button = ctk.CTkButton(self.export_import_frame, text="Export Quest", command=self.export_quest)
        self.export_button.grid(row=0, column=1, padx=10, sticky='e')
        
        self.refresh_app_list()
        quest_list_update = True

    def create_activity_widgets(self):
        self.activity_tab = self.add("Activity")

        self.activity_nav_frame = ctk.CTkFrame(self.activity_tab, width=900, height=100)
        self.activity_nav_frame.grid(row=0)

        self.date_error_prompt = ctk.CTkLabel(self.activity_nav_frame, text="Invalid date: Please insert a valid date (YYYY-MM-DD)", text_color="red", font=(None, 13, "bold"))

        self.activitytab_scrollable = ctk.CTkScrollableFrame(self.activity_tab, width=900, height=500)
        self.activitytab_scrollable.grid(row=2)
        bg_color = self.activitytab_scrollable.cget("fg_color")
        self.activitytab_scrollable.configure(
            scrollbar_fg_color=bg_color,
            scrollbar_button_color=bg_color,
            scrollbar_button_hover_color=bg_color
        )

        self.activity_day_title = ctk.CTkLabel(self.activity_nav_frame, text=f"Today: {str(date.today())}", font=(None, 15, "bold"))
        self.activity_day_title.grid(row=0, column=0, sticky="w", pady=(0,10))

        self.activity_year = ctk.CTkEntry(self.activity_nav_frame, placeholder_text="Year")
        self.activity_year.grid(row=1, column=0, sticky="w", pady=(0,30), padx=(0,15))

        self.activity_month = ctk.CTkEntry(self.activity_nav_frame, placeholder_text="Month")
        self.activity_month.grid(row=1, column=1, sticky="w", pady=(0,30), padx=(0,15))

        self.activity_day = ctk.CTkEntry(self.activity_nav_frame, placeholder_text="Day")
        self.activity_day.grid(row=1, column=2, sticky="w", pady=(0,30), padx=(0,15))

        self.activity_search = ctk.CTkButton(self.activity_nav_frame, text="Search", command=self.search_date)
        self.activity_search.grid(row=1, column=3, padx=20, sticky="w", pady=(0,30))
        
        for col in range(1):
            self.activity_tab.columnconfigure(col, weight=1)

        self.activitytab_scrollable.grid_columnconfigure(0, weight=1)
        
    def create_stats_widgets(self):
        self.stat_tab = self.add("Stats")
        
        self.stat_frame = ctk.CTkFrame(self.stat_tab)
        self.stat_frame.pack(fill="x")
        for col in range(5):
            self.stat_frame.columnconfigure(col, weight=1)
            
        #Each Frame
        self.time_spend_frame = ctk.CTkFrame(self.stat_frame)
        self.time_spend_frame.grid(row=0, column=1, padx=10, pady=5)
        
        self.total_time_spend_frame = ctk.CTkFrame(self.stat_frame)
        self.total_time_spend_frame.grid(row=0, column=3, padx=10, pady=5)
        
        self.task_complete_frame = ctk.CTkFrame(self.stat_frame)
        self.task_complete_frame.grid(row=1, column=1, padx=10, pady=5)
        
        self.streak_frame = ctk.CTkFrame(self.stat_frame)
        self.streak_frame.grid(row=1, column=3, padx=10, pady=5)
        
        #Time Spend for Each App For 1 Week 
        self.time_spend_label = ctk.CTkLabel(self.time_spend_frame, text="Time Spend for Each App In The Last Week:")
        self.time_spend_label.pack()
        
        self.time_spend_chart = DrawPieChart(self.time_spend_frame, {})
        self.time_spend_chart.pack()
        
        #Total Time Spend For 1 Month
        self.total_time_spend_label = ctk.CTkLabel(self.total_time_spend_frame, text="Time Spend During The Past Month:")
        self.total_time_spend_label.pack()
        
        self.total_time_spend_chart = DrawPieChart(self.total_time_spend_frame, {})
        self.total_time_spend_chart.pack()

        #Total task complete since install
        self.task_complete_label = ctk.CTkLabel(self.task_complete_frame, text="Total Task Completed:", anchor="w")
        self.task_complete_label.pack(fill="x", padx=20, pady=(10,5))
        
        self.task_missed_label = ctk.CTkLabel(self.task_complete_frame, text="Total Task Missed:", anchor="w")
        self.task_missed_label.pack(fill="x", padx=20, pady=5)
        
        self.percentage_bar = ctk.CTkProgressBar(self.task_complete_frame, mode="determinate", height=15, width=500, progress_color='#76d169')
        self.percentage_bar.pack(padx=20, pady=(50,0))
        self.percentage_bar.set(0)
        
        self.percentage_label = ctk.CTkLabel(self.task_complete_frame, text="% of task completed")
        self.percentage_label.pack(fill="x", padx=20, pady=5)
        
        #Longest/Current streak
        self.current_streak_label = ctk.CTkLabel(self.streak_frame, text="Current Streak:", anchor="w")
        self.current_streak_label.pack(fill="x", padx=20, pady=(10,5))
        
        self.longest_streak_label = ctk.CTkLabel(self.streak_frame, text="Longest Streak:", anchor="w")
        self.longest_streak_label.pack(fill="x", padx=20, pady=5)
        
        self.streak_bar = ctk.CTkProgressBar(self.streak_frame, mode="determinate", height=15, width=500, progress_color='#76d169')
        self.streak_bar.pack(padx=20, pady=(50,0))
        self.streak_bar.set(0)
        
        self.streak_label = ctk.CTkLabel(self.streak_frame, text=" more day(s) to go!")
        self.streak_label.pack(fill="x", padx=20, pady=5)
        
        #Refresh Button
        self.refresh_stat_button = ctk.CTkButton(self.stat_tab, text="Refresh", command=self.refresh_stat, width=200)
        self.refresh_stat_button.pack(pady=20, padx=10, expand=True)

    def restart_program(self):
        """Restart the current program."""
        if sys.platform == 'darwin':
            subprocess.Popen(['open', '-n', '-a', 'Sproutime.app'])
        elif sys.platform == 'win32':
            subprocess.Popen([sys.executable, __file__])
        self.destroy()
        os._exit(0)
        
    def create_setting_widgets(self):
        global allow_noti, theme, secondary_colour
        conn = get_database_connection(APP_NAME, DB_RELATIVE_PATH, DATABASE_FILENAME)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM settings")
            presettings = cursor.fetchone()
            if presettings:
                theme = presettings[0]
                if presettings[1] == 1:
                    allow_noti = True
                else:
                    allow_noti = False
            else:
                cursor.execute("INSERT INTO settings (theme, notifications) VALUES (?, ?)", ("Dark", True))
                conn.commit()
        except sqlite3.Error as e:
            if DEBUG: print(f"An error occurred: {e}")
            conn.rollback()
        finally:
            if conn:
                conn.close()
        self.setting_tab = self.add("Settings")

        # Settings Frame
        self.settings_frame = ctk.CTkFrame(self.setting_tab, width=700, height=500)
        self.settings_frame.grid(pady=(30,0))
        self.settings_frame.grid_propagate(False)

        #Theme Selector
        self.theme_frame = ctk.CTkFrame(self.settings_frame, width=600, height=40)
        self.theme_frame.grid(pady=(0,20))
        self.theme_frame.grid_propagate(False)
        self.theme_frame.grid_columnconfigure(0, weight=1)
        self.theme_frame.grid_columnconfigure(1, weight=1)
        self.theme_label = ctk.CTkLabel(self.theme_frame, text="Theme", font=(None, 15, "bold"))
        self.theme_label.grid(row=0, column=0, pady=(6,0))
        self.theme_selector = ctk.CTkOptionMenu(self.theme_frame, values=theme_options)  # Change theme
        self.theme_selector.grid(row=0, column=1, pady=(6,0))
        self.theme_selector.set(theme)  # Set default theme

        #Notification Switch
        self.noti_frame = ctk.CTkFrame(self.settings_frame, width=600, height=40)
        self.noti_frame.grid(pady=(0, 20))
        self.noti_frame.grid_propagate(False)
        self.noti_frame.grid_columnconfigure(0, weight=1)
        self.noti_frame.grid_columnconfigure(1, weight=1)
        self.noti_label = ctk.CTkLabel(self.noti_frame, text="Notifications", font=(None, 15, "bold"))
        self.noti_label.grid(row=0, column=0, pady=(6,0))
        self.noti_switch = ctk.CTkSwitch(self.noti_frame, text="Enabled", variable=ctk.BooleanVar(value=True) if allow_noti == True else ctk.BooleanVar(value=False))
        self.noti_switch.grid(row=0, column=1, pady=(6,0))

        #Apply Settings Button
        self.apply_settings_button = ctk.CTkButton(self.settings_frame, text="Apply", command=self.apply_settings)
        self.apply_settings_button.grid(pady=(0,20))

        self.prompt_restart = ctk.CTkLabel(self.settings_frame, text="Changes saved. A restart is recommended to fully apply the settings.", text_color="red", font=(None, 13, "bold"))
        self.prompt_restart.grid(row=3)
        self.apply_settings()
        self.prompt_restart.grid_remove()
        
        self.theme_frame.configure(fg_color=secondary_colour)
        self.noti_frame.configure(fg_color=secondary_colour)
        
        #Debug Button
        self.debug_button = ctk.CTkButton(self.settings_frame, text="Debug", command=self.open_debug_menu)
        self.debug_button.grid(row=5, pady=50)

        self.settings_frame.grid_columnconfigure(0, weight=1)
        self.settings_frame.grid_columnconfigure(0, weight=1)

        for col in range(1):
            self.setting_tab.grid_columnconfigure(col, weight=1)

        for row in range(1):
            self.setting_tab.grid_rowconfigure(row, weight=1)

        #Restart Button
        self.restart_button = ctk.CTkButton(self.settings_frame, text="Restart", command=self.restart_program)
        self.restart_button.grid(row=4, pady=50)

    def create_treeview_widgets(self):
        self.treeview_tab = self.add("Garden")
        # Create a frame for the treeview
        self.treeview_frame = ctk.CTkFrame(self.treeview_tab)
        self.treeview_frame.pack(padx=10, pady=10, fill="both", expand=True)
        self.treeview_frame.columnconfigure(0, weight=1)
        
        # show current_time
        self.current_time_label = ctk.CTkLabel(self.treeview_frame, text=" Sync... ", font=(None, 15, "bold"))
        
        self.current_time_label.pack(pady=10)

        # show point in label
        self.treeview_label = ctk.CTkLabel(self.treeview_frame, text=f" Point:  ", font=(None, 15, "bold"))
        
        self.treeview_label.pack(pady=10)        
        
    def display_image(self, parent, image_path):
        """Display an image in the specified parent widget."""
        try:
            img = Image.open(image_path)
            img = img.resize((750, 450), Image.Resampling.LANCZOS)
            photo = ctk.CTkImage(light_image=img, dark_image=img, size=(875, 475))
            label = ctk.CTkLabel(parent, image=photo, text="")
            label.image = photo  # Keep a reference!
            label.pack(pady=20)
        except Exception as e:
            label = ctk.CTkLabel(parent, text=f"Error loading image:\n{e}")
            label.pack(pady=20)
        
        # only show one image only
        for widget in parent.winfo_children():
            if isinstance(widget, ctk.CTkLabel) and widget != label: # Check if it is not the current label
                widget.destroy()

    def update_timelabel(self):
        self.current_time_label.configure(text=f" Today: {str(date.today())}  ", font=(None, 15, "bold")) 

    def update_treeview(self):
        # update treeview with point
        global running, quest_complete_update, treeview_update
        
        # point_earn from quest_completion
        if running:
            if treeview_update:
                conn = get_database_connection(APP_NAME, DB_RELATIVE_PATH, DATABASE_FILENAME)
                cursor = conn.cursor()
                try:
                    cursor.execute("SELECT score_earn FROM activity_log WHERE type = 1")
                    result_earn = cursor.fetchall()
                    point = 0
                    for row in result_earn:
                        point += row[0]
                except sqlite3.Error as e:
                    if DEBUG: print(f"An error occurred: {e}")
                    conn.rollback()
                finally:
                    if conn:
                        conn.close()

                # update label with point
                self.treeview_label.configure(text=f" Point: {point} ", font=(None, 15, "bold"))
                # Get the current appearance mode as "dark" or "light"
                current_theme = ctk.get_appearance_mode().lower()
                
                # update image with your own image path
                if current_theme == "dark":
                    if point < 700:
                        self.display_image(self.treeview_tab, resource_path(os.path.join("img", f"tree{point // 100}_night.jpg")))
                    else:
                        self.display_image(self.treeview_tab, resource_path(os.path.join("img", "tree6_night.jpg")))
                        
                elif current_theme == "light":
                    if point < 700:
                        self.display_image(self.treeview_tab, resource_path(os.path.join("img", f"tree{point // 100}_day.jpg")))
                    else:
                        self.display_image(self.treeview_tab, resource_path(os.path.join("img", "tree6_day.jpg")))

                treeview_update = False

            # Update label
            if quest_complete_update:
                self.update_timelabel()
       
    def update_progress(self):
        global running, app_time_update, sort_type, search_by_name, secondary_colour
        while running:
            if app_time_update:
                temp_quest_data = {}
                conn = get_database_connection(APP_NAME, DB_RELATIVE_PATH, DATABASE_FILENAME)
                cursor = conn.cursor()
                try:
                    for app in app_dict:
                        cursor.execute("SELECT time, maximum FROM quest WHERE app_name = ?", (app,))
                        result = cursor.fetchone()
                        temp_quest_data[app] = result
                except sqlite3.Error as e:
                    if DEBUG: print(f"An SQL error occurred: {e}")
                    conn.rollback()
                finally:
                    conn.close()

                for widget in self.progress_scrollable.winfo_children():
                    widget.grid_remove()

                if sort_type == "Oldest":
                    sorted_apps = list(app_dict.keys())
                elif sort_type == "Newest":
                    sorted_apps = list(reversed(app_dict.keys()))
                elif sort_type == "Longest Screentime":
                    sorted_apps = sorted(app_dict.items(), key=lambda item: item[1], reverse=True)
                    sorted_apps = [app for app, _ in sorted_apps]
                elif sort_type == "Shortest Screentime":
                    sorted_apps = sorted(app_dict.items(), key=lambda item: item[1])
                    sorted_apps = [app for app, _ in sorted_apps]
                elif sort_type == "Quests":
                    apps_with_quests = []
                    apps_without_quests = []
                    for app in app_dict:
                        if temp_quest_data.get(app):
                            apps_with_quests.append(app)
                        else:
                            apps_without_quests.append(app)
                    sorted_apps = apps_with_quests + apps_without_quests
                else:
                    sorted_apps = list(app_dict.keys())

                if search_by_name:
                    if search_by_name in appname_dict.values():
                        search_by_name = next((k for k, v in appname_dict.items() if v == search_by_name), None)

                    if search_by_name in sorted_apps:
                        filtered_apps = []
                        for app in sorted_apps:
                            if app == search_by_name:
                                filtered_apps.append(app)
                        sorted_apps = filtered_apps
                    else:
                        sorted_apps.clear()
                        self.no_results_label.grid()

                for index, app in enumerate(sorted_apps):
                    result = temp_quest_data.get(app)
                    if result:
                        time = result[0] / 60
                        if result[1] == 1:
                            maximum = ">"
                        elif result[1] == 0:
                            maximum = "<"
                        quest_info = f"{maximum} {time} hour(s)"
                    else:
                        quest_info = "No quest set"

                    if appname_dict and app in old_name_list:
                        appname = appname_dict[app]
                    else:
                        appname = app

                    time = app_dict[app]
                    if time >= 60:
                        minutes = time // 60
                        hours = minutes // 60
                        remaining_minutes = minutes % 60

                        if remaining_minutes == 0:
                            time = f'{hours} hour(s)'
                        elif hours == 0:
                            time = f'{remaining_minutes} minute(s)'
                        else:
                            time = f'{hours} hour(s) & {remaining_minutes} minute(s)'
                    else:
                        time = f'{time} second(s)'

                    if app not in detected_app:
                                
                        #Frame for each app
                        self.progress_app_frame = ctk.CTkFrame(self.progress_scrollable, width=1080, height=150, fg_color=secondary_colour)
                        self.progress_app_frame.grid(column=0, padx=10, pady=10)
                        self.progress_app_frame.grid_propagate(False)
                        appframe_dict[app] = self.progress_app_frame

                        #Label for app name
                        self.app_label = ctk.CTkLabel(self.progress_app_frame, text=f"{appname}", font=(None, 15, "bold"))
                        self.app_label.grid(padx=10, pady=(20,0), sticky="w")
                        appname_label_dict[app] = self.app_label

                        #Label for time detected
                        self.app_time_label = ctk.CTkLabel(self.progress_app_frame, text=f"{time}")
                        self.app_time_label.grid(padx=10, sticky="w")
                        apptime_label_dict[app] = self.app_time_label
                        
                        #Label for quest info
                        self.quest_label = ctk.CTkLabel(self.progress_app_frame, text=f"Quest : {quest_info}")
                        self.quest_label.grid(padx=10, pady=(0,10), sticky="w")
                        appquest_label_dict[app] = self.quest_label

                        #Progress bar
                        self.progress_bar = ctk.CTkProgressBar(self.progress_app_frame, width=1040, fg_color="#2D2D2D")
                        self.progress_bar.grid(padx=10, pady=(0,20))
                        self.progress_bar.set(0)
                        progressbar_dict[app] = self.progress_bar

                        detected_app.append(app)

                    else:
                        if self.progress_scrollable.winfo_exists():
                            appframe_dict[app].grid(row=index, column=0, padx=10, pady=10)
                            apptime_label_dict[app].configure(text=f"{time}")
                            appquest_label_dict[app].configure(text=f"Quest : {quest_info}")
                            appname_label_dict[app].configure(text=f"{appname}")

                    if app in quest_list and result:
                        progressbar_dict[app].set(app_dict[app] / (result[0] * 60))

                for app in detected_app:
                    if app not in app_dict:
                        detected_app.clear()
                        for widget in self.progress_scrollable.winfo_children():
                            widget.pack_forget()

                app_time_update = False
            sleep(1)

    def update_quest(self):
        global running, quest_list_update, secondary_colour
        
        while running:
            if quest_list_update:
                conn = get_database_connection(APP_NAME, DB_RELATIVE_PATH, DATABASE_FILENAME)
                cursor = conn.cursor()
                
                try:
                    cursor.execute("SELECT app_name, maximum, time FROM quest")
                    quests = cursor.fetchall()
                    
                    for widget in self.quest_list_frame.winfo_children():
                        widget.pack_forget()
            
                    for app, sign, time in quests:
                        maximum = ">" if sign == 1 else "<"
                        if appname_dict and app in old_name_list:
                            app_name = appname_dict[app]
                        else:
                            app_name = app
                        
                        quest_box = ctk.CTkFrame(self.quest_list_frame, fg_color=secondary_colour, width=1080, height=150)
                        quest_box.pack(pady=5)
                        quest_box.grid_columnconfigure((0), weight=1)
                        quest_box.grid_propagate(False)
                        
                        maximum_switch_var = ctk.StringVar(value=maximum)
                        time_slider_var = ctk.IntVar(value=int(time / 60))
                        
                        #Quest Name
                        quest_name_label = ctk.CTkLabel(quest_box, text=f'{app_name}', font=(None, 15, "bold"))
                        quest_name_label.grid(row=0, column=0, sticky="w", padx=30, pady=10)

                        # Time Label
                        time_label = ctk.CTkLabel(quest_box, text=f"{maximum_switch_var.get()}{time_slider_var.get()} hour(s)")
                        time_label.grid(row=1, column=2, padx=(0, 30), pady=(0, 10), sticky='e')
                        
                        # Time Option
                        time_slider = ctk.CTkSlider(quest_box, from_=1, to=12, number_of_steps=11, variable=time_slider_var, fg_color="#2D2D2D",
                                                   command=lambda slider_var=time_slider_var.get(), switch_var=maximum_switch_var, label=time_label: label.configure(text=f"{switch_var.get()}{int(slider_var)} hour(s)"))
                        time_slider.grid(row=0, column=2, padx=(0, 10), pady=10, sticky='e')
                        
                        # Maximum Option
                        maximum_switch = ctk.CTkSwitch(quest_box, text="",
                                                       variable=maximum_switch_var, onvalue=">", offvalue="<",
                                                       command=lambda slider_var=time_slider_var.get(), switch_var=maximum_switch_var, label=time_label: label.configure(text=f"{switch_var.get()}{int(slider_var)} hour(s)"))
                        maximum_switch.grid(row=0, column=1, padx=(10, 0), pady=10, sticky='e')
                        
                        #Change Name 
                        entry = ctk.CTkEntry(quest_box, placeholder_text='Custom Name')
                        entry.grid(row=2, column=0, padx=30, pady=5, sticky="w")
            
                        #Delete Button
                        delete_button = ctk.CTkButton(quest_box, text="Delete", command=lambda current_app=app: self.delete_quest(current_app))
                        delete_button.grid(row=2, column=1, padx=(0, 5), pady=10, sticky="e")

                        #Update Button
                        save_button = ctk.CTkButton(quest_box, text="Update", command=lambda max_switch=maximum_switch, time_slider=time_slider, current_app=app, new_name_widget=entry: self.update_quest_frame(max_switch, time_slider, current_app, new_name_widget))
                        save_button.grid(row=2, column=2, padx=(5, 30), pady=10, sticky='e')
                except sqlite3.Error as e:
                    if DEBUG: print(f"An SQL error occurred: {e}")
                    conn.rollback()
                finally:
                    if conn:
                        conn.close()
                        
                quest_list_update = False
            sleep(1)
            
    def update_activity(self):
        global running, quest_complete_update, date_request, secondary_colour
        
        while running:
            if quest_complete_update:
                activity_log_dict = {}
                conn = get_database_connection(APP_NAME, DB_RELATIVE_PATH, DATABASE_FILENAME)
                cursor = conn.cursor()
                
                try:
                    cursor.execute("SELECT * FROM activity_log WHERE date = ?", (date_request,))
                    activity_list = cursor.fetchall()

                    for activity in activity_list:
                        timestamp = activity[1]
                        type = activity[2]
                        app_name = activity[3]
                        time = activity[4]
                        score_earn = activity[5]
                        score_deduct = activity[6]
                        new_name = activity[7]

                        if appname_dict and (app_name in old_name_list):
                            updated_name = appname_dict[app_name]
                        else:
                            updated_name = app_name
                            
                        if type == 1:
                            activity_log_dict[timestamp] = f'{updated_name} > {int(time) / 60} hour(s): Completed +{score_earn} points'
                        
                        elif type == 2:
                            activity_log_dict[timestamp] = f'{updated_name} < {int(time) / 60} hour(s): Failed -{score_deduct} points'
                        
                        elif type == 3:
                            activity_log_dict[timestamp] = f'''"{app_name}" was changed into "{new_name}"'''

                except sqlite3.Error as e:
                    if DEBUG: print(f"An SQL error occurred: {e}")
                    conn.rollback()
                finally:
                    if conn:
                        conn.close()

                for widget in self.activitytab_scrollable.winfo_children():
                    widget.grid_forget()

                for time, info in activity_log_dict.items():
                    activity_frame = ctk.CTkFrame(self.activitytab_scrollable, width=700, height=40, fg_color=secondary_colour)
                    activity_frame.grid(pady=3)
                    activity_frame.grid_propagate(False)

                    activity_time = ctk.CTkLabel(activity_frame, text=time, font=(None, 15, "bold"))
                    activity_time.place(x=10, rely=0.5, anchor="w")

                    activity_info = ctk.CTkLabel(activity_frame, text=info)
                    activity_info.place(x=100, rely=0.5, anchor="w")

                quest_complete_update = False
            sleep(1)

    def update_stats(self): 
        global running, stat_update
               
        while running:
            if stat_update:
                today = datetime.now()
                one_week_ago = (today - timedelta(days=7)).strftime('%Y-%m-%d')
                one_month_ago = (today - timedelta(days=30)).strftime('%Y-%m-%d')
        
                conn = get_database_connection(APP_NAME, DB_RELATIVE_PATH, DATABASE_FILENAME)
                cursor = conn.cursor()
                
                try:
                    #Time Spend for Each App For 1 Week
                    cursor.execute("SELECT app_name, duration FROM app_time WHERE date >= ?", (one_week_ago,))
                    app_time = cursor.fetchall()
                    
                    time_dict = {}
                    for app_name, time in app_time:
                        if appname_dict and (app_name in old_name_list):
                            app_name = appname_dict[app_name]
                        if app_name in time_dict:
                            time_dict[app_name] += time
                        else:   
                            time_dict[app_name] = time
                
                    self.time_spend_chart.update_data(time_dict)
                    self.after(100, self.time_spend_chart._draw_chart)

                    #Total Time Spend For 1 Month
                    cursor.execute("SELECT app_name, duration FROM app_time WHERE date >= ?", (one_month_ago,))
                    app_time = cursor.fetchall()
                    
                    time_dict = {}
                    for app_name, time in app_time:
                        if appname_dict and (app_name in old_name_list):
                            app_name = appname_dict[app_name]
                        if app_name in time_dict:
                            time_dict[app_name] += time
                        else:   
                            time_dict[app_name] = time
                            
                    self.total_time_spend_chart.update_data(time_dict)
                    self.after(100, self.total_time_spend_chart._draw_chart)
                            
                    #Total task complete since install
                    cursor.execute("SELECT SUM(quest_completed), SUM(quest_set) FROM streak")
                    task = cursor.fetchone()
                    
                    if (task) and (task[0] is not None) and (task[1] is not None):
                        self.task_complete_label.configure(text=f'Total Task Completed: {task[0]}')
                        self.task_missed_label.configure(text=f'Total Task Missed: {task[1] - task[0]}')
                        
                        if task[1] == 0:
                            percentage = 0
                        else:
                            percentage = float("{:.2f}".format(task[0] / task[1] * 100))
                            
                        self.percentage_bar.set(percentage / 100.0)
                        self.update_idletasks()
                        self.percentage_label.configure(text=f'{percentage}% of task completed')
                    
                    #Longest/Current streak
                    current_streak = 0
                    longest_streak = 0
                    count = 0
                    yesterday = date.today() - timedelta(days=1)
                    
                    cursor.execute("SELECT date, quest_completed, quest_set FROM streak WHERE date <= ? ORDER BY date DESC", (str(yesterday),))
                    days = cursor.fetchall()
                    
                    for day in days:
                        if day[1] == day[2]:
                            current_streak += 1
                        else:
                            break
                    self.current_streak_label.configure(text=f'Current Streak: {current_streak}')
                    
                    cursor.execute("SELECT date, quest_completed, quest_set FROM streak ORDER BY date ASC")
                    days = cursor.fetchall()

                    if days:
                        for day in days:
                            if day[1] == day[2]:
                                count += 1
                            else:
                                longest_streak = max(longest_streak, count)
                                count = 0
                    longest_streak = max(longest_streak, count)
                    self.longest_streak_label.configure(text=f'Longest Streak: {longest_streak}')
                    if longest_streak == 0:
                        self.streak_bar.set(0)
                    else:
                        self.streak_bar.set(current_streak / longest_streak)
                    self.update_idletasks()
                    day_left = longest_streak - current_streak
                    if longest_streak > current_streak:
                        self.streak_label.configure(text=f'{day_left} more day(s) to go!')
                    else:
                        self.streak_label.configure(text='You have broken your record, keep on going!')
                except sqlite3.Error as e:
                    if DEBUG: print(f"An SQL error occurred: {e}")
                    conn.rollback()
                finally:
                    if conn:
                        conn.close()
                
                stat_update = False
            sleep(1)
            
    def start_updating(self):     
        tab = self.get()
        self.progress_active = tab == "Progress"
        self.quest_active = tab == "Quest"
        self.activity_active = tab == "Activity"
        self.stats_active = tab == "Stats"
        self.treeview_active = tab == "Garden"

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
        if self.activity_active and (self.activity_thread is None or not self.activity_thread.is_alive()):
            self.activity_thread = threading.Thread(target=self.update_activity, daemon=True)
            self.activity_thread.start()
        elif not self.activity_active and self.activity_thread and self.activity_thread.is_alive():
            # The thread will naturally pause in its while loop
            pass
        
        #Stats Tab
        if self.stats_active and (self.stats_thread is None or not self.stats_thread.is_alive()):
            self.stats_thread = threading.Thread(target=self.update_stats, daemon=True)
            self.stats_thread.start()
        elif not self.stats_active and self.stats_thread and self.stats_thread.is_alive():
            # The thread will naturally pause in its while loop
            pass

        #Treeview Tab
        if self.treeview_active and (self.treeview_thread is None or not self.treeview_thread.is_alive()):
            self.treeview_thread = threading.Thread(target=self.update_treeview, daemon=True)
            self.treeview_thread.start()    
        elif not self.treeview_active and self.treeview_thread and self.treeview_thread.is_alive():
            # The thread will naturally pause in its while loop
            pass

    def tab_changed(self):
        self.start_updating()

    def progress_search(self):
        global sort_type, app_time_update, search_by_name
        sort_type = self.progress_sort_combobox.get()
        search_by_name = self.progress_search_entry.get()
        app_time_update = True

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

    def time_callback(self, value):
        self.quest_time_label.configure(text=f"{switch_var.get()}{slider_var.get()} hour(s)")

    def maximum_callback(self):
        self.quest_time_label.configure(text=f"{switch_var.get()}{slider_var.get()} hour(s)")

    def refresh_app_list(self):
        global temp_quest_app, temp_quest_tab
        
        app_list = get_all_app_list()
        self.app_dropdown.configure(values=app_list)

        tab_list = ["Any Tabs"] if google not in quest_list else []
        tab_list = [tab for tab in constant_tab_list if tab not in quest_list]
        self.tabBox.configure(values=tab_list)
        
        if app_list:
            temp_quest_app = app_list[0]
        else:
            temp_quest_app = ""

        temp_quest_tab = tab_list[0]
        
        self.check_for_chrome()
        
        self.app_dropdown.set(value=temp_quest_app)
        self.tabBox.set(value=temp_quest_tab)
    
    def delete_quest(self, app_name):
        global quest_list_update, quest_complete_update, treeview_update
        
        conn = get_database_connection(APP_NAME, DB_RELATIVE_PATH, DATABASE_FILENAME)
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM quest WHERE app_name = ?", (app_name,))
            cursor.execute("DELETE FROM activity_log WHERE app_name = ?", (app_name,))
            conn.commit()
        except sqlite3.Error as e:
            if DEBUG: print(f"An SQL error occurred: {e}")
            conn.rollback()
        finally:
            if conn:
                conn.close()
        
        quest_list.remove(app_name)
        self.refresh_app_list()
        progressbar_dict[app_name].set(0)
        
        quest_list_update = True
        quest_complete_update = True
        treeview_update = True

    def update_quest_frame(self, max_switch, time_slider, current_app, new_name_widget):
        global quest_list_update, quest_complete_update, app_time_update, treeview_update
        
        app_name = current_app
        maximum = 1 if max_switch.get() == '>' else 0
        minutes = (time_slider.get() * 60)
        new_name = new_name_widget.get().strip()

        conn = get_database_connection(APP_NAME, DB_RELATIVE_PATH, DATABASE_FILENAME)
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT time, maximum FROM quest WHERE app_name = ?", (app_name,))
            old_time, old_maximum = cursor.fetchone()
            
            cursor.execute("UPDATE quest SET time = ?, maximum = ? WHERE app_name = ?", (minutes, maximum, app_name))
             
            #New Name   
            if new_name:
                if new_name != app_name:
                    appname_dict[app_name] = new_name
                    old_name_list.append(app_name)
                    current_time = datetime.now().strftime("%H:%M:%S")
                    cursor.execute("INSERT INTO activity_log (app_name, new_name, date, timestamp, type) VALUES (?, ?, ?, ?, ?)", (app_name, new_name, str(date.today()), current_time, 3))
                else:
                    appname_dict.pop(app_name, None)
                    cursor.execute("DELETE FROM activity_log WHERE app_name = ? AND type = 3", (app_name,))
            
            if (old_time != minutes) or (old_maximum != maximum):
                cursor.execute("DELETE FROM activity_log WHERE app_name = ? AND date = ? AND type IN (1, 2)", (app_name, str(date.today())))
                quest_dict[app_name] = {"maximum": max_switch.get(), "time": minutes * 60}
                
                if app_name in completed_list:
                    completed_list.remove(app_name)
                if app_name in failed_list:
                    failed_list.remove(app_name)
                   
            conn.commit()
        except sqlite3.Error as e:
            if DEBUG: print(f"An SQL error occurred: {e}")
            conn.rollback()
        finally:
            if conn:
                conn.close()
 
        check_quest(app_name)

        quest_list_update = True
        app_time_update = True
        quest_complete_update = True
        treeview_update = True
        
    def save_quest_time(self):
        global temp_quest_app, temp_quest_tab, quest_list_update, quest_complete_update, app_time_update, treeview_update
        if temp_quest_app:
            minutes = slider_var.get() * 60
            name = temp_quest_tab if temp_quest_app == google and temp_quest_tab != "Any Tabs" else temp_quest_app
            if switch_var.get() == ">":
                maximum = 1
            else:
                maximum = 0
                completed_list.append(name)

            conn = get_database_connection(APP_NAME, DB_RELATIVE_PATH, DATABASE_FILENAME)
            cursor = conn.cursor()
            
            try:
                cursor.execute("INSERT INTO quest (app_name, time, maximum) VALUES (?, ?, ?)", (name, minutes, maximum))
                conn.commit()
                
                quest_list.append(name)
                quest_dict[name] = {"maximum": switch_var.get(), "time": minutes * 60}
                
                #Check if quest is completed today
                cursor.execute("DELETE FROM activity_log WHERE date = ? AND app_name = ? AND type = 1", (str(date.today()), name))
                conn.commit()

            except sqlite3.Error as e:
                if DEBUG: print(f"An SQL error occurred: {e}")
                conn.rollback()
            finally:
                if conn:
                    conn.close()
                
            check_quest(app_name)
            self.refresh_app_list()

            quest_list_update = True
        
    def refresh_stat(self):
        global stat_update
        update_log(str(date.today()))
        load_past_data()
        stat_update = True

    def apply_settings(self):
        global allow_noti, theme, secondary_colour
        theme = self.theme_selector.get()
        ctk.set_appearance_mode(theme)
        current_theme = ctk.get_appearance_mode().lower()

        if current_theme == "dark":
            secondary_colour = "#515151"
        else:
            secondary_colour = "#979da2"
        self.theme_frame.configure(fg_color=secondary_colour)
        self.noti_frame.configure(fg_color=secondary_colour)

        for widget in self.progress_scrollable.winfo_children():
            widget.configure(fg_color=secondary_colour)

        if self.noti_switch.get() == 1:
            allow_noti = True
        else:
            allow_noti = False
        self.noti_switch.configure(text="Enabled" if allow_noti else "Disabled")

        try:
            conn = get_database_connection(APP_NAME, DB_RELATIVE_PATH, DATABASE_FILENAME)
            cursor = conn.cursor()

            cursor.execute("UPDATE settings SET theme = ?, notifications = ?", (self.theme_selector.get(), allow_noti))
            conn.commit()
        except sqlite3.Error as e:
            if DEBUG: print(f"An SQL error occurred: {e}")
            conn.rollback()
        finally:
            if conn:
                conn.close()
        
        self.prompt_restart.grid()

    def open_debug_menu(self):
        global debug_menu
    
        if debug_menu is None or not debug_menu.winfo_exists():
            debug_menu = DebugMenu(self)  # Pass the main window as parent
        else:
            debug_menu.focus()

    def search_date(self):
        global date_request, quest_complete_update
        self.date_error_prompt.grid_forget()
        year = self.activity_year.get()
        month = self.activity_month.get()
        day = self.activity_day.get()

        self.activity_year.delete(0, ctk.END)
        self.activity_month.delete(0, ctk.END)
        self.activity_day.delete(0, ctk.END)
        self.activity_search.focus_set()

        try:
            date_request = f"{year}-{month}-{day}"
            date_request  = f"{int(year):04d}-{int(month):02d}-{int(day):02d}"
            datetime.strptime(date_request, "%Y-%m-%d")
            if date_request == str(date.today()):
                self.activity_day_title.configure(text=f"Today: {date_request}")
            else:
                self.activity_day_title.configure(text=date_request)

        except ValueError:
            date_request = str(date.today())
            self.date_error_prompt.grid(row=0, column=1, columnspan=2)
        quest_complete_update = True
        
    def upload_quest_json(self):
        file_path = filedialog.askopenfilename(
            title="Select a JSON File",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if file_path:
            try:
                show_confirmation(title='Import Quest?', message='Warning: This is overwrite your current quest', on_yes=lambda file_path=file_path: self.import_quest(file_path))
            except json.JSONDecodeError:
                show_popup("Error", "Error: Invalid JSON file.")
            except Exception as e:
                show_popup("Error", f"Error writing JSON file: {e}")
    
    def import_quest(self, file_path):
        global quest_list_update, quest_list, quest_dict
        
        with open(file_path, 'r') as file:
            json_data = json.load(file)
            
            conn = get_database_connection(APP_NAME, DB_RELATIVE_PATH, DATABASE_FILENAME)
            cursor = conn.cursor()
            
            try:
                for quest in json_data:
                    if quest['app_name'] in quest_list:
                        cursor.execute("SELECT time, maximum FROM quest WHERE app_name = ?", (quest['app_name'],))
                        old_time, old_maximum = cursor.fetchone()
                        
                        if (old_time != quest['time']) or (old_maximum !=  quest['maximum']):
                            cursor.execute("DELETE FROM activity_log WHERE app_name = ? AND date = ? AND type IN (1, 2)", (quest['app_name'], str(date.today())))   
                            if quest['app_name'] in completed_list:
                                completed_list.remove(quest['app_name'])
                            if quest['app_name'] in failed_list:
                                failed_list.remove(quest['app_name'])
                                                
                    cursor.execute("INSERT OR REPLACE INTO quest (app_name, time, maximum) VALUES (?, ?, ?)", (quest['app_name'], quest['time'], quest['maximum']))
                    check_quest(quest['app_name'])
                    
                conn.commit()
                
                quest_list = []
                quest_dict = {}
                
                cursor.execute("SELECT app_name, maximum, time FROM quest")
                quests = cursor.fetchall()
                
                for app, sign, time in quests:
                    if sign == 1:
                        maximum = ">" 
                    else:
                        maximum = "<"
                        completed_list.append(app)
                    quest_list.append(app)
                    quest_dict[app] = {"maximum": maximum, "time": time * 60}
                    
            except sqlite3.Error as e:
                if DEBUG: print(f"An SQL error occurred: {e}")
                conn.rollback()
            finally:
                if conn:
                    conn.close()
            
            quest_list_update = True
    
    def export_quest(self):
        conn = get_database_connection(APP_NAME, DB_RELATIVE_PATH, DATABASE_FILENAME)
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT app_name, time, maximum FROM quest")
            quests = cursor.fetchall()
            
            json_data = []
            for quest in quests:
                quest_json_dict = {"app_name": quest[0],
                                   "time": quest[1],
                                   "maximum": quest[2]}
                json_data.append(quest_json_dict)
            
            json_string = json.dumps(json_data, indent=4)
        except sqlite3.Error as e:
            if DEBUG: print(f"An SQL error occurred: {e}")
            conn.rollback()
        finally:
            if conn:
                conn.close()

        home_directory = str(Path.home())

        # Construct the path to the Downloads folder
        downloads_folder = os.path.join(home_directory, "Downloads")
        file_name = "sproutime-quest.json"
        file_path = os.path.join(downloads_folder, file_name)
        
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(json_string)
            
            show_popup("Quest Exported", "Your quest had been exported as a JSON in your Downloads")
        except Exception as e:
            print(f"An error occurred while saving the file: {e}")
    
class DrawPieChart(ctk.CTkFrame):
    def __init__(self, master, data, **kwargs):
        super().__init__(master, **kwargs)

        self.data = data
        self.colors = ["#6495ED", "#FFA07A", "#90EE90", "#F08080",
                       "#B0E0E6", "#A0522D", "#F080E1", "#D3D3D3",
                       "#BDB76B", "#AFEEEE", "#ADD8E6", "#FFDAB9"]

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)  # For the legend
        self.grid_rowconfigure(0, weight=1)

        self.pie_frame = None
        self.canvas = None
        self.legend_scrollable_frame = None
        self._create_widgets()

    def _create_widgets(self):
        # Pack the pie chart into a frame
        self.pie_frame = ctk.CTkFrame(self, width=610, height=260, fg_color='#323232')
        self.pie_frame.grid(row=0, column=0, sticky="nsew")

        # Create a canvas widget for the pie chart
        canvas_width = 260
        canvas_height = 260
        self.canvas = ctk.CTkCanvas(self.pie_frame, width=canvas_width, height=canvas_height, highlightthickness=0)
        self.canvas.pack(side="left", padx=10, pady=10)

        # Create a frame for the legend
        legend_frame = ctk.CTkFrame(self.pie_frame, width=300, height=260)
        legend_frame.pack(side="right", padx=5, pady=10, fill="y")
        legend_frame.grid_propagate(False)  # Prevent the frame from resizing with content

        # Create a scrollable container for the legend items
        self.legend_scrollable_frame = ctk.CTkScrollableFrame(legend_frame, height=240)
        self.legend_scrollable_frame.pack(fill="both", expand=True)

        self._draw_chart()

    def _draw_pie_chart(self):
        self.canvas.delete("all")  # Clear the previous chart
        total = sum(self.data.values())
        start_angle = 0
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        center_x = canvas_width / 2
        center_y = canvas_height / 2
        radius = min(center_x, center_y) - 20

        for i, (_, value) in enumerate(self.data.items()):
            if len(self.data.items()) > 1:
                angle = (value / total) * 360

                # Draw the arc (slice)
                self.canvas.create_arc(
                    center_x - radius,
                    center_y - radius,
                    center_x + radius,
                    center_y + radius,
                    start=start_angle,
                    extent=angle,
                    fill=self.colors[i % len(self.colors)],
                    outline="black",
                    width=1,
                    tags="pie_slice" 
                )
                start_angle += angle
            else:  # Handle the case where there's only one data item.
                i = 0
                x0 = center_x - radius
                y0 = center_y - radius
                x1 = center_x + radius
                y1 = center_y + radius
                
                if value > 60:
                    self.canvas.create_oval(x0, y0, x1, y1, fill=self.colors[i % len(self.colors)], outline="black", width=1)
                else:
                    self.canvas.create_oval(x0, y0, x1, y1, fill="grey", outline="black", width=1)

    def _create_legend(self):
        # Clear previous legend items
        for widget in self.legend_scrollable_frame.winfo_children():
            widget.pack_forget()

        for i, (label, value) in enumerate(self.data.items()):
            time = 0
            minutes = value // 60
            hours = minutes // 60
            remaining_minutes = minutes % 60

            if not (minutes == 0):
                if remaining_minutes == 0:
                    time = f'{hours} hour(s)'
                elif hours == 0:
                    time = f'{remaining_minutes} minute(s)'
                else:
                    time= f'{hours} hour(s) & {remaining_minutes} minute(s)'

                # Create a frame for each legend item (color + text)
                legend_item_frame = ctk.CTkFrame(self.legend_scrollable_frame, fg_color="transparent")
                legend_item_frame.pack(pady=(0, 10), fill="x")  # Added some padding between items

                # Create the color box and label container
                color_label_container = ctk.CTkFrame(legend_item_frame, fg_color="transparent")
                color_label_container.pack(side="top", fill="x")

                # Create the color box
                legend_color_box = ctk.CTkLabel(color_label_container, text="", width=20, height=20, bg_color=self.colors[i % len(self.colors)], fg_color=self.colors[i % len(self.colors)])
                legend_color_box.pack(side="left", padx=(5, 10))  # Reduced horizontal padding

                # Create the label (Fruit Name)
                legend_label = ctk.CTkLabel(color_label_container, text=f"{label}:", anchor="w")
                legend_label.pack(side="left", fill="x", expand=True, padx=(0, 20))

                # Create the value label below
                legend_value_label = ctk.CTkLabel(legend_item_frame, text=f"{time}", anchor="w")
                legend_value_label.pack(side="top", fill="x", padx=(35, 10))  # Indent to align under the value

    def _draw_chart(self):
        self._draw_pie_chart()
        self._create_legend()

    def update_data(self, new_data):
        self.data = new_data
        self._draw_chart()

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
        
        #Clear data
        conn = get_database_connection(APP_NAME, DB_RELATIVE_PATH, DATABASE_FILENAME)
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            table_names = [table[0] for table in tables]
            table_var = ctk.StringVar(value=table_names[0])
        except sqlite3.Error as e:
            if DEBUG: print(f"An SQL error occurred: {e}")
            conn.rollback()
        finally:
            if conn:
                conn.close()

        self.table_dropdown = ctk.CTkComboBox(self, values=table_names, variable=table_var)
        self.table_dropdown.grid(row=1, column=0, padx=20, pady=10, sticky='ew', columnspan = 2)
        
        self.clear_data_button = ctk.CTkButton(master=self, text="Clear Data",
                                               command=lambda title=f'Clear Data?', on_yes=lambda table=table_var: self.clear_data(table), : show_confirmation(title=title, on_yes=on_yes))
        self.clear_data_button.grid(row=2, column=0, padx=20, pady=10, sticky='ew', columnspan = 2)
        
        #Drop every table
        self.drop_table_button = ctk.CTkButton(master=self, text="Reset Database",
                                               command=lambda title='Drop All Table?', on_yes=lambda: self.reset_database(), : show_confirmation(title=title, on_yes=on_yes))
        self.drop_table_button.grid(row=3, column=0, padx=20, pady=10, sticky='ew', columnspan = 2)
        
        #Export App Data
        self.export_app_data_button = ctk.CTkButton(master=self, text="Export App Data", command=self.export_app_data)
        self.export_app_data_button.grid(row=4, column=0, padx=20, pady=10, sticky='ew', columnspan = 2)
        
        #Import App Data
        self.import_app_data_button = ctk.CTkButton(master=self, text="Import App Data", command=self.upload_app_data_json)
        self.import_app_data_button.grid(row=5, column=0, padx=20, pady=10, sticky='ew', columnspan = 2)

    def clear_data(self, table):
        global app_time_update, quest_complete_update, quest_list_update, app_dict, quest_list, quest_dict, completed_list, failed_list, appname_dict, old_name_list, treeview_update
        
        conn = get_database_connection(APP_NAME, DB_RELATIVE_PATH, DATABASE_FILENAME)
        cursor = conn.cursor()
        
        try:
            cursor.execute(f"DELETE FROM {table.get()}")
            conn.commit()
        except sqlite3.Error as e:
            if DEBUG: print(f"An SQL error occurred: {e}")
            conn.rollback()
        finally:
            if conn:
                conn.close()
                
        match table:
            case 'app_time':
                app_dict = {}
            case 'quest':
                quest_list = []
                quest_dict = {}
            case 'activity_Log':
                completed_list = []
                failed_list = []
                appname_dict = {}
                old_name_list = []
        
        app_time_update = True
        quest_list_update = True
        quest_complete_update = True
        treeview_update = True
            
    def reset_database(self):
        global treeview_update, app_time_update, quest_complete_update, quest_list_update, app_dict, quest_list, quest_dict, completed_list, failed_list, appname_dict, old_name_list
        
        conn = get_database_connection(APP_NAME, DB_RELATIVE_PATH, DATABASE_FILENAME)
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
            if DEBUG: print(f"An SQL error occurred: {e}")
            conn.rollback()
        finally:
            if conn:
                conn.close()
        
        app_dict = {}
        quest_list = []
        quest_dict = {}
        completed_list = []
        failed_list = []
        appname_dict = {}
        old_name_list = []
        
        setup_sql()
        app_time_update = True
        quest_list_update = True
        quest_complete_update = True
        treeview_update = True
        
    def export_app_data(self):
        conn = get_database_connection(APP_NAME, DB_RELATIVE_PATH, DATABASE_FILENAME)
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            
            database_data = {}
            tables = cursor.fetchall()
            table_names = [table[0] for table in tables]
            
            for table_name in table_names:
                if DEBUG: print(f"Exporting data from table: {table_name}")
                cursor.execute(f"SELECT * FROM {table_name}")
                
                # Get column names
                columns = [description[0] for description in cursor.description]
                rows = cursor.fetchall()

                # Convert rows to a list of dictionaries
                table_rows_as_dicts = []
                for row in rows:
                    row_dict = {}
                    for i, col_name in enumerate(columns):
                        row_dict[col_name] = row[i]
                    table_rows_as_dicts.append(row_dict)
                
                database_data[table_name] = table_rows_as_dicts
        except sqlite3.Error as e:
            if DEBUG: print(f"An SQL error occurred: {e}")
            conn.rollback()
        finally:
            if conn:
                conn.close()
        
        home_directory = str(Path.home())

        # Construct the path to the Downloads folder
        downloads_folder = os.path.join(home_directory, "Downloads")
        file_name = "sproutime-app-data.json"
        file_path = os.path.join(downloads_folder, file_name)
                
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                json.dump(database_data, file, ensure_ascii=False, indent=4)
            show_popup("App Data Exported", "Your app data had been exported as a JSON in your Downloads")
        except Exception as e:
            show_popup("Error", f"Error writing JSON file: {e}")
            
    def upload_app_data_json(self):
        file_path = filedialog.askopenfilename(
            title="Select a JSON File",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if file_path:
            try:
                show_confirmation(title='Import App Data?', message='Warning: This might overwrite your current app data', on_yes=lambda file_path=file_path: self.import_app_data(file_path))
            except json.JSONDecodeError:
                show_popup("Error", "Error: Invalid JSON file.")
            except Exception as e:
                show_popup("Error", f"Error writing JSON file: {e}")
    
    def import_app_data(self, file_path):
        global app_time_update, quest_list_update, quest_complete_update, stat_update, treeview_update
        
        with open(file_path, 'r') as file:
            json_data = json.load(file)
            
            conn = get_database_connection(APP_NAME, DB_RELATIVE_PATH, DATABASE_FILENAME)
            cursor = conn.cursor()
            
            try:
                for table_name, records in json_data.items():
                    if not records: #Skipping empty table
                        continue
                    
                    columns = list(records[0].keys())
                    
                    #Insert data
                    placeholders = ', '.join(['?' for _ in columns])
                    insert_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
                    
                    for record in records:
                        values = [record.get(col) for col in columns] # Use .get() to handle missing keys gracefully
                        try:
                            cursor.execute(insert_sql, values)
                        except sqlite3.OperationalError as op_e:
                            show_popup(f"Error inserting into {table_name} for record {record}: {op_e}", "This often means the table or columns don't exist, or there's a data type mismatch.")
                        except Exception as ex:
                            show_popup("SQL Error", f"An unexpected error occurred during insertion for record {record}: {ex}")
                conn.commit()
            except sqlite3.Error as e:
                if DEBUG: print(f"An SQL error occurred: {e}")
                conn.rollback()
            finally:
                if conn:
                    conn.close()
                    
            show_popup("App Data Import Sucessfully", "Data successfully imported into SQLite database")
                    
            app_time_update = True
            quest_list_update = True
            quest_complete_update = True
            stat_update = True
            treeview_update = True
        
    def close_debug_menu(self):
        self.destroy() 

# PyInstaller creates a temp folder and stores path in _MEIPASS
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

#Configuration
APP_NAME = "Sproutime" 
DATABASE_FILENAME = "sproutime.db"
DB_RELATIVE_PATH = os.path.join("database", DATABASE_FILENAME)

#Get Writable App Data Directory
def get_app_data_dir(app_name):
    if sys.platform == "darwin":
        app_support_dir = os.path.join(os.path.expanduser("~"), "Library", "Application Support")
    elif sys.platform == 'win32':
        app_support_dir = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "Sproutime")

    app_dir = os.path.join(app_support_dir, app_name)
    os.makedirs(app_dir, exist_ok=True) # Create the directory if it doesn't exist
    return app_dir

#Database Setup
def get_database_connection(app_name, db_relative_path, db_filename):
    app_data_dir = get_app_data_dir(app_name)
    writable_db_path = os.path.join(app_data_dir, db_filename)

    # Check if the database already exists in the writable location
    if not os.path.exists(writable_db_path):
        # Get the path to the bundled database
        db_source_path = resource_path(db_relative_path)

        if not os.path.exists(db_source_path):
            raise FileNotFoundError(
                f"Bundled database '{db_source_path}' not found! "
                "Ensure it's added correctly with --add-data."
            )

        # Copy the bundled database to the writable location
        try:
            shutil.copy2(db_source_path, writable_db_path)
        except Exception as e:
            raise IOError(f"Failed to copy database from {db_source_path} to {writable_db_path}: {e}")
        
    conn = sqlite3.connect(writable_db_path)
    return conn

def setup_sql():   
    conn = get_database_connection(APP_NAME, DB_RELATIVE_PATH, DATABASE_FILENAME)
    cursor = conn.cursor()
 
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quest (
                app_name TEXT UNIQUE NOT NULL,
                time INTEGER NOT NULL,
                maximum INTEGER NOT NULL
            );
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS app_time (
                app_name TEXT NOT NULL,
                date TEXT NOT NULL, --Store as YYYY-MM-DD
                duration INTEGER NOT NULL
            );
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS streak (
                date TEXT UNIQUE PRIMARY KEY, --Store as YYYY-MM-DD
                quest_completed INTEGER NOT NULL,
                quest_set INTEGER NOT NULL
            );
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS activity_log(
                date TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                type INTEGER NOT NULL,
                app_name TEXT,
                time INTEGER,
                score_earn INTEGER,
                score_deduct INTEGER,
                new_name TEXT
            );
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                theme TEXT,
                notifications BOOLEAN
            );
        ''') 
    except sqlite3.Error as e:
        if DEBUG: print(f"An SQL error occurred: {e}")
        conn.rollback()
    finally:
        if conn:
            conn.close()

def get_active_app_name():
    global appName

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

        try:
            for process in psutil.process_iter(['pid', 'name']):
                if process.info['pid'] == pid:
                    process_name = process.info['name']
                    if process_name not in ignored_processes:
                        appName = process_name.split(".")[0].capitalize()
                        if appName == "Chrome":
                            tabName = get_active_tab_name()
                            if tabName != "URL not detected":
                                appName = tabName
        except Exception as e:
            pass

    return appName

def get_all_app_list():
    global google
    app_list = []
    
    if sys.platform == 'darwin':
        running_app = AppKit.NSWorkspace.sharedWorkspace().runningApplications()
        
        for app in running_app:
            launch_date = app.launchDate()
            if (not app.isHidden() and launch_date) and (not app.localizedName() == "Sproutime"):
                app_list.append(app.localizedName())
                
    elif sys.platform == 'win32':
        for process in psutil.process_iter(['pid', 'name']):
            pid = process.info['pid']

            def enumWindowsArguments(handle, __):
                _, foundPID = win32process.GetWindowThreadProcessId(handle)

                if foundPID == pid and win32gui.IsWindowVisible(handle):
                    process_name = process.info["name"]
                    if (process_name not in ignored_processes) and (process_name != "Sproutime.exe"):
                        app_name = process_name.split(".")[0].capitalize() # Get all active app name
                        if app_name not in app_list:
                            app_list.append(app_name)

            win32gui.EnumWindows(enumWindowsArguments, None)
              
    app_list = [app for app in app_list if (app not in quest_list) or (app == google)]
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

def notify(app_name, info):
    global allow_noti
    if allow_noti == True:
        if appname_dict and app_name in old_name_list:
            app_name = appname_dict[app_name]
            
        if info == "min time completed":
            Title = f"Quest Completed for {app_name}"
            Msg = f"Well done! You've spent enough time on {app_name}"
        
        elif info == "max time failed":
            Title = f"Quest Failed for {app_name}"
            Msg = f"Oh no! You've exceeded your screentime limit for {app_name}"

        elif info == "10 mins left":
            Title = f"10 minutes left for {app_name}"
            Msg = f"You are nearing your screentime limit for {app_name}"

        if sys.platform == 'darwin':
            applescript = f'display notification "{Msg}" with title "{Title}" sound name "Blow"'

            try:
                subprocess.run(["osascript", "-e", applescript], check=True)
            except subprocess.CalledProcessError as e:
                print(f"Error sending notification: {e}")
            except FileNotFoundError:
                print("Error: 'osascript' command not found. Are you on macOS?")
            
        elif sys.platform == 'win32':      
            noti = winotify.Notification(app_id="Sproutime",
                    title = Title,
                    msg = Msg,
                    duration = "long")
            
            noti.set_audio(winotify.audio.Default, loop=False)
            noti.show()

def load_past_data():
    global app_time_update, app_dict, completed_list, failed_list, appname_dict, old_name_list, quest_list, quest_dict, detected_app, allow_noti, theme
    
    app_dict = {}
    quest_list = []
    quest_dict = {}
    completed_list = []
    failed_list = []
    
    conn = get_database_connection(APP_NAME, DB_RELATIVE_PATH, DATABASE_FILENAME)
    cursor = conn.cursor()
    
    try:
        #App Time
        cursor.execute("SELECT app_name, duration FROM app_time WHERE date = ?", (str(date.today()),))
        apps = cursor.fetchall()
        
        for app in apps:
            app_dict[app[0]] = app[1]

        #Completed quest
        cursor.execute("SELECT app_name FROM activity_log WHERE date = ? AND type = 1", (str(date.today()),))
        quests = cursor.fetchall()
        
        for quest in quests:
            completed_list.append(quest[0])
        
        #Current Quest
        cursor.execute("SELECT app_name, maximum, time FROM quest")
        quests = cursor.fetchall()
        
        for app, sign, time in quests:
            maximum = ">" if sign == 1 else "<"
            
            quest_list.append(app)
            quest_dict[app] = {"maximum": maximum, "time": time * 60}

        #Updated new names
        cursor.execute("SELECT app_name, new_name FROM activity_log WHERE type = 3")
        names_changed = cursor.fetchall()

        for change in names_changed:
            if change[0] not in old_name_list:
                old_name_list.append(change[0])
            appname_dict[change[0]] = change[1]


    except sqlite3.Error as e:
        if DEBUG: print(f"An SQL error occurred: {e}")
        conn.rollback()
    finally:
        if conn:
            conn.close()
            
    app_time_update = True

def update_time():
    global app_name, app_time_update, running, _d_time_speed
    
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

            check_quest(app_name)
            
            app_time_update = True
            sleep(1)

def check_quest(app_name):
    global quest_complete_update, treeview_update
    
    if (quest_list) and (app_name in quest_list):
        task_score = determine_score()
        
        if (app_name in app_dict):
            if quest_dict[app_name]["time"] <= app_dict[app_name]:
                if (quest_dict[app_name]["maximum"] == ">") and (app_name not in completed_list):
                    conn = get_database_connection(APP_NAME, DB_RELATIVE_PATH, DATABASE_FILENAME)
                    cursor = conn.cursor()
                    
                    try:
                        cursor.execute("SELECT time FROM quest WHERE app_name = ?", (app_name,))
                        quest = cursor.fetchone()
                        quest_time = quest[0]
                        current_time = datetime.now().strftime("%H:%M:%S")
                        
                        cursor.execute("SELECT COUNT(*) FROM activity_log WHERE app_name = ? AND date = ? AND type = 1", (app_name, str(date.today())))
                        if cursor.fetchone()[0] == 0:
                            cursor.execute("INSERT INTO activity_log (date, app_name, time, type, score_earn, timestamp) VALUES (?, ?, ?, ?, ?, ?)", (str(date.today()), app_name, quest_time, 1, task_score, current_time))
                            conn.commit()
                    except sqlite3.Error as e:
                        if DEBUG: print(f"An SQL error occurred: {e}")
                        conn.rollback()
                    finally:
                        if conn:
                            conn.close()

                    completed_list.append(app_name)
                    notify(app_name, "min time completed")
                            
                #Failed Quest      
                elif (quest_dict[app_name]["maximum"] == "<") and (app_name not in failed_list):
                    failed_list.append(app_name)
                    completed_list.remove(app_name)
                    
                    conn = get_database_connection(APP_NAME, DB_RELATIVE_PATH, DATABASE_FILENAME)
                    cursor = conn.cursor()
                    
                    try:
                        cursor.execute("SELECT time FROM quest WHERE app_name = ?", (app_name,))
                        quest_time = cursor.fetchone()[0]
                        current_time = datetime.now().strftime("%H:%M:%S")
                    
                        cursor.execute("DELETE FROM activity_log WHERE app_name = ? AND date = ? AND type = 1", (app_name, str(date.today())))
                        cursor.execute("INSERT INTO activity_log (date, app_name, time, score_deduct, timestamp, type) VALUES (?, ?, ?, ?, ?, ?)", (str(date.today()), app_name, quest_time, task_score, current_time, 2))
                        conn.commit()
                    except sqlite3.Error as e:
                        if DEBUG: print(f"An SQL error occurred: {e}")
                        conn.rollback()
                    finally:
                        if conn:
                            conn.close()
                    
                    notify(app_name, "max time failed")
            
            # 10 mins left till quest failed
            elif ((quest_dict[app_name]["time"] - 600) == app_dict[app_name]) and (quest_dict[app_name]["maximum"] == "<"):
                notify(app_name, "10 mins left")
                
            elif (quest_dict[app_name]["time"] > app_dict[app_name]) and (quest_dict[app_name]["maximum"] == "<"):
                conn = get_database_connection(APP_NAME, DB_RELATIVE_PATH, DATABASE_FILENAME)
                cursor = conn.cursor()
                
                try:
                    cursor.execute("SELECT time FROM quest WHERE app_name = ?", (app_name,))
                    quest_time = cursor.fetchone()[0]
                    current_time = datetime.now().strftime("%H:%M:%S")
                        
                    cursor.execute("SELECT COUNT(*) FROM activity_log WHERE app_name = ? AND date = ? AND type = 1", (app_name, str(date.today())))
                    if cursor.fetchone()[0] == 0:
                        cursor.execute("INSERT INTO activity_log (date, app_name, time, type, score_earn, timestamp) VALUES (?, ?, ?, ?, ?, ?)", (str(date.today()), app_name, quest_time, 1, task_score, current_time))
                        conn.commit()
                except sqlite3.Error as e:
                    if DEBUG: print(f"An SQL error occurred: {e}")
                    conn.rollback()
                finally:
                    if conn:
                        conn.close()
                
        elif (quest_dict[app_name]["maximum"] == "<") and (app_name not in completed_list):
            conn = get_database_connection(APP_NAME, DB_RELATIVE_PATH, DATABASE_FILENAME)
            cursor = conn.cursor()

            try:
                cursor.execute("SELECT time, maximum FROM quest WHERE app_name = ?", (app_name,))
                quest_time = cursor.fetchone()[0]
                completed_list.append(app_name)
                current_time = datetime.now().strftime("%H:%M:%S")
                
                cursor.execute("SELECT COUNT(*) FROM activity_log WHERE app_name = ? AND date = ? AND type = 1", (app_name, str(date.today())))
                if cursor.fetchone()[0] == 0:
                    cursor.execute("INSERT INTO activity_log (date, app_name, time, type, score_earn, timestamp) VALUES (?, ?, ?, ?, ?, ?)", (str(date.today()), app_name, quest_time, 1, task_score, current_time))
                    conn.commit()
                conn.commit()
            except sqlite3.Error as e:
                if DEBUG: print(f"An SQL error occurred: {e}")
                conn.rollback()
            finally:
                if conn:
                    conn.close()
                
            completed_list.append(app_name)
        quest_complete_update = True
        treeview_update = True

def determine_score():
    conn = get_database_connection(APP_NAME, DB_RELATIVE_PATH, DATABASE_FILENAME)
    cursor = conn.cursor()
    
    current_streak = 0
    yesterday = date.today() - timedelta(days=1)
    try:
        cursor.execute("SELECT date, quest_completed, quest_set FROM streak WHERE date <= ? ORDER BY date DESC", (str(yesterday),))
        days = cursor.fetchall()
        
        for day in days:
            if day[1] == day[2]:
                current_streak += 1
            else:
                break
    except sqlite3.Error as e:
        if DEBUG: print(f"An SQL error occurred: {e}")
        conn.rollback()
    finally:
        if conn:
            conn.close()
    
    #Total Task
    if len(quest_list) > 5:
        score = 500 // len(quest_list)
    else:
        score = 100
    
    #Streak Multiplier
    multiplier = 1 + (current_streak // 7) * 0.1
    score = math.floor(score * multiplier)

    return score
    
def update_log(today):
    global app_dict, completed_list, failed_list
    conn = get_database_connection(APP_NAME, DB_RELATIVE_PATH, DATABASE_FILENAME)
    cursor = conn.cursor()
    
    try:
        #App Time
        for app in app_dict:
            cursor.execute("SELECT COUNT(*) FROM app_time WHERE app_name = ? AND date = ?", (app, today))
            if cursor.fetchone()[0] > 0:
                cursor.execute("UPDATE app_time SET duration = ? WHERE app_name = ? AND date = ?", (app_dict[app], app, today))
            else:
                cursor.execute("INSERT INTO app_time (app_name, date, duration) VALUES (?, ?, ?)", (app, today, app_dict[app]))

        #Streak
        cursor.execute("SELECT COUNT(*) FROM quest")
        quest_set = cursor.fetchone()[0]
        
        cursor.execute("INSERT OR REPLACE INTO streak (date, quest_completed, quest_set) VALUES (?, ?, ?)", (today, len(completed_list), quest_set))
        
        conn.commit()
        app_dict = {}
        completed_list = []
        failed_list = []
    except sqlite3.Error as e:
        if DEBUG: print(f"An SQL error occurred: {e}")
        conn.rollback()
    finally:
        if conn:
            conn.close()
            
def show_confirmation(title='Are you sure?', message='Warning: This action cannot be undone', on_yes=None, on_no=None):
    dialog = ctk.CTkToplevel()
    dialog.title(title)
    dialog.geometry("360x140")
    dialog.attributes('-topmost', True)
    dialog.grab_set()

    # Create a label to display the message
    message_label = ctk.CTkLabel(dialog, text=message)
    message_label.grid(row=0, column=0, pady=(20,10), padx=20, columnspan=2, sticky='ew')

    def yes_callback():
        dialog.destroy()
        if on_yes:
            on_yes() # Call the 'Yes' callback

    def no_callback():
        dialog.destroy()
        if on_no:
            on_no()  # Call the 'No' callback

    # Add buttons to the dialog.
    yes_button = ctk.CTkButton(dialog, text="Yes", command=yes_callback)
    yes_button.grid(row=1, column=0, pady=20, padx=20, sticky='w')
    no_button = ctk.CTkButton(dialog, text="No", command=no_callback)
    no_button.grid(row=1, column=1, pady=20, padx=20, sticky='e')

    # The dialog will block until a button is pressed.
    dialog.wait_window()

def show_popup(title, message):
    dialog = ctk.CTkToplevel()
    dialog.title(title)
    dialog.geometry("500x140")
    dialog.attributes('-topmost', True)
    dialog.grab_set()

    # Create a label to display the message
    message_label = ctk.CTkLabel(dialog, text=message)
    message_label.pack(pady=(20,10), padx=20, fill='x')
    
    def callback():
        dialog.destroy()

    # Add buttons to the dialog.
    okay_button = ctk.CTkButton(dialog, text="Okay", command=callback)
    okay_button.pack(pady=20, padx=20)

    # The dialog will block until a button is pressed.
    dialog.wait_window()

def on_closing(): #when user close the program
    global running
    
    running = False
    
    p1.join()
    
    update_log(str(date.today()))
    sys.exit()

#DEBUG
DEBUG = 1

setup_sql()

app = App()

#Thread Setup
running = False
time_lock = threading.Lock()

##Global Var
appName = ""
app_dict = {}
temp_quest_app = ""
temp_quest_tab = ""
web_browser = ["Google Chrome"]
quest_list = []
quest_dict = {}
completed_list = []
failed_list = []
slider_var = ctk.IntVar(value=1)
switch_var = ctk.StringVar(value=">")
ignored_processes = ["", "explorer.exe", "TextInputHost.exe", "ApplicationFrameHost.exe", "Taskmgr.exe", "SearchHost.exe", "ShellExperienceHost.exe"]

# Progress Tab UI
progressbar_dict = {}
detected_app = []
appframe_dict = {}
appname_label_dict = {}
apptime_label_dict = {}
appquest_label_dict = {}
sort_type = "Oldest"
search_by_name = ""

# Activity Log Tab UI
date_request = str(date.today())

google = "Google Chrome"

if sys.platform == "win32":
    google = "Chrome"

 # Used in name changer
appname_dict = {}
old_name_list = []

#Debug Menu Var
debug_menu = None
_d_time_speed = ctk.IntVar(value=1)

#GUI Update Request
app_time_update = True
quest_list_update = True
quest_complete_update = True
stat_update = True
treeview_update = True

#First load
running = True

load_past_data()
app_list = get_all_app_list()
constant_tab_list = ["Youtube", "Reddit", "Instagram", "Facebook", "Linkedin"]
tab_list = [tab for tab in constant_tab_list if tab not in quest_list]
if google not in quest_list:
    tab_list.insert(0, "Any Tabs")
theme_options = ["Dark", "Light", "System"]
allow_noti = True
theme = "Dark"
secondary_colour = "#515151"
if app_list:
    temp_quest_app = app_list[0]
else:
    temp_quest_app = ""
temp_quest_tab = tab_list[0]

p1 = threading.Thread(target=update_time)

p1.start()

scrollable_frame = ctk.CTkScrollableFrame(app)
bg_color = scrollable_frame.cget("fg_color") # Get the background color of the scrollable frame
scrollable_frame.configure( # Hide the scrollbar by making its colors the same as the background
    scrollbar_fg_color=bg_color,
    scrollbar_button_color=bg_color,
    scrollbar_button_hover_color=bg_color
)
scrollable_frame.pack(fill="both", expand=True)

Tabview(master=scrollable_frame).pack(padx=(20), pady=20, fill="x",)
app.protocol("WM_DELETE_WINDOW", on_closing)
app.mainloop()