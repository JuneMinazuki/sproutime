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
        self.bar_thread = None

        #Create widget
        self.create_progress_widgets()
        self.create_quest_widgets()
        self.create_score_widgets()
        self.create_stats_widgets()
        self.create_setting_widgets()
        self.create_bar_widgets()

        self.start_updating()

    def create_progress_widgets(self):
        self.progress_tab = self.add("Progress")

        #Textbox
        self.app_list_TB = ctk.CTkTextbox(self.progress_tab, width=1080, height=180)
        self.app_list_TB.grid(row=0, column=0, columnspan=4)

        for col in range(3):
            self.progress_tab.columnconfigure(col, weight=1)

        for row in range(5):
            self.progress_tab.rowconfigure(row, weight=1)

    def create_quest_widgets(self):
        global quest_list_update
        self.quest_tab = self.add("Quest")

        #App Option
        self.app_dropdown = ctk.CTkComboBox(self.quest_tab,values=app_list, command=self.combobox_callback)
        self.app_dropdown.grid(row=0, column=0, padx=10, pady=20, sticky='w')

        #Time Option
        self.time_dropdown = ctk.CTkComboBox(self.quest_tab,values=time, command=self.timebox_callback)
        self.time_dropdown.grid(row=0, column=2, padx=10, pady=20, sticky='e')

        #Chrome Tab Option (only shown whenever Chrome is selected in the App Option, refer to combobox_callback)
        self.tabBox = ctk.CTkComboBox(self.quest_tab, values=tab_list, command=self.tabBox_callback)
        self.tabBox.grid(row=0, column=1)
        self.tabBox.set(tab_list[0])
        self.check_for_chrome()    
        
        #Refresh Button
        self.refresh_button = ctk.CTkButton(self.quest_tab, text="Refresh", command=self.refresh_app_list)
        self.refresh_button.grid(row=1, column=0, padx=10, pady=20, sticky='w')
        
        #Delete Button
        self.delete_button = ctk.CTkButton(self.quest_tab, text="Delete", command=self.delete_quest)
        self.delete_button.grid(row=1, column=1, padx=10, pady=20, sticky="e")

        #Save Button
        self.save_button = ctk.CTkButton(self.quest_tab, text="Save", command=self.save_quest_time)
        self.save_button.grid(row=1, column=2, padx=10, pady=20, sticky='e')

        #Quest Saved Textbox
        self.quest_list_TB = ctk.CTkTextbox(self.quest_tab, width=1080, height=180)
        self.quest_list_TB.grid(row=2, column=0, padx=10, pady=20, columnspan = 3)
        quest_list_update = True

        # Scrollable frame for name changer
        self.appname_widgets = []  

        self.scrollable_frame = ctk.CTkScrollableFrame(self.quest_tab)
        self.scrollable_frame.grid(row=3, column=0, sticky="nsew")

        for i, app in enumerate(app_list):
            label = ctk.CTkLabel(self.scrollable_frame, text=app)
            label.grid(row=i, column=0, padx=10, pady=5)

            entry = ctk.CTkEntry(self.scrollable_frame, placeholder_text="New name")
            entry.grid(row=i, column=1, padx=10, pady=5)

            self.appname_widgets.append((label, entry))

        # Add Change Name Button
        save_button = ctk.CTkButton(self.quest_tab, text="Change", command=self.change_app_name)
        save_button.grid(row=4, column=0)

    def create_score_widgets(self):
        self.score_tab = self.add("Score")

        #Completed Quests Textbox
        self.completed_list_TB = ctk.CTkTextbox(self.score_tab, width=1080, height=180)
        self.completed_list_TB.grid(row=0, column=0, columnspan=3)

        #Name Change Log
        self.namechange_list_TB = ctk.CTkTextbox(self.score_tab, width=1080, height=180)
        self.namechange_list_TB.grid(row=1, column=0, columnspan=3)

        #Failed Quests Textbox
        self.failed_list_TB = ctk.CTkTextbox(self.score_tab, width=1080, height=180)
        self.failed_list_TB.grid(row=2, column=0, columnspan=3)

        for col in range(1):
            self.score_tab.columnconfigure(col, weight=1)
        
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
        
        #Total Time Spend
        self.total_time_spend_label = ctk.CTkLabel(self.total_time_spend_frame, text="Total Time Spend:")
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
        
    def create_setting_widgets(self):
        self.setting_tab = self.add("Settings")
        
        #Theme
        self.theme_selector = ctk.CTkOptionMenu(master=self.setting_tab, values=theme_options, command=lambda theme: ctk.set_appearance_mode(theme))  # Change theme
        self.theme_selector.pack(padx=20, pady=10)
        self.theme_selector.set("System")  # Set default theme to "System"
        
        #Debug Button
        self.debug_button = ctk.CTkButton(master=self.setting_tab, text="Debug", command=self.open_debug_menu)
        self.debug_button.pack(padx=20, pady=10)

    def create_bar_widgets(self):
        self.bar_tab = self.add("Progress Bar")
        # get data from database
        global quest_list_update, quest_list,quest_dict
        conn = sqlite3.connect('sproutime.db')
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT app_name, maximum, time FROM quest")
            quests = cursor.fetchall()
            quest_list = []
            quest_dict = {}
            for quest in quests:
                app_name = quest[0]
                maximum = ">" if quest[1] == 1 else "<"
                time = quest[2]
                quest_list.append(f"{app_name} : {maximum} {time / 60} hour")
        except sqlite3.Error as e:
            if DEBUG: print(f"An error occurred: {e}")
            conn.rollback()
        finally:
            if conn:
                conn.close()

        # if quest_list is empty, set to "No quests available" until not empty and updated to dropdown
        if not quest_list:
            quest_list = ["No quests available"]
        #Quest Option
        self.quest_dropdown = ctk.CTkComboBox(self.bar_tab, values=quest_list, command=self.combobox_callback)
        self.quest_dropdown.pack(pady=10, padx=10)
        self.quest_dropdown.set(quest_list[0])  # Set default value
        
        # Add Refresh Button for Progress Bar Tab
        self.refresh_bar_button = ctk.CTkButton(self.bar_tab, text="Refresh", command=self.refresh_bar_tab)
        self.refresh_bar_button.pack(pady=10)

        #Add Progress Bar Button
        self.add_progress_button = ctk.CTkButton(self.bar_tab, text="Add", command=self.add_progress_bar)
        self.add_progress_button.pack(pady=10)
        # if quest_dropdown choose "No quests available", disable the button
        if self.quest_dropdown.get() == "No quests available":
            self.add_progress_button.configure(state="disabled")
        else:
            self.add_progress_button.configure(state="normal")

        self.progress_frame = ctk.CTkFrame(self.bar_tab)
        self.progress_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.progress_bars = []
        
    def add_progress_bar(self):
        global quest_list, quest_list_update, quest_dict
        # Frame for each progress bar
        bar_frame = ctk.CTkFrame(self.progress_frame)
        bar_frame.pack(fill="x", pady=5)
        
        # get the selected quest from dropdown out of the frame
        selected_quest = self.quest_dropdown.get()
        if selected_quest:
            # Extract app name, maximum, and time from the selected quest
            app_name, maximum_time = selected_quest.split(" : ")
            maximum, time, unit = maximum_time.split(" ")
            time = (float(time) * 60)
            label_text = f"{app_name} : {maximum} {time / 60} hour"
            # Create a label for the progress bar
            label = ctk.CTkLabel(bar_frame, text=label_text)
            label.pack(pady=5)
        
        


        # Progress bar
        progress_bar = ctk.CTkProgressBar(bar_frame)
        progress_bar.set(0)  # Set initial progress to 0%
        progress_bar.pack(fill="x", padx=5, pady=5)
        bar_frame.progress_bar = progress_bar  # Store reference to the progress bar in the frame        

        # Delete button
        delete_button = ctk.CTkButton(bar_frame, text="Delete", width=80, command=lambda: self.delete_progress_bar(bar_frame))
        delete_button.pack(pady=5)

        self.progress_bars.append(bar_frame)
        

    def refresh_bar_tab(self):
        # Remove all progress bars
        for bar_frame in self.progress_bars:
            bar_frame.destroy()
        self.progress_bars.clear()

        # Refresh quest list from database
        global quest_list, quest_dict
        conn = sqlite3.connect('sproutime.db')
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT app_name, maximum, time FROM quest")
            quests = cursor.fetchall()
            quest_list = []
            quest_dict = {}
            for quest in quests:
                app_name = quest[0]
                maximum = ">" if quest[1] == 1 else "<"
                time = quest[2]
                quest_list.append(f"{app_name} : {maximum} {time / 60} hour")
        except sqlite3.Error as e:
            if DEBUG: print(f"An error occurred: {e}")
            conn.rollback()
        finally:
            if conn:
                conn.close()

        # If quest_list is empty, set to "No quests available"
        if not quest_list:
            quest_list = ["No quests available"]

        # Update dropdown values and reset selection
        self.quest_dropdown.configure(values=quest_list)
        self.quest_dropdown.set(quest_list[0])

        # Re-enable the add button if there are quests available
        if self.quest_dropdown.get() == "No quests available":
            self.add_progress_button.configure(state="disabled")
        else:
            self.add_progress_button.configure(state="normal")

    def delete_progress_bar(self, bar_frame):
        bar_frame.destroy()
        self.progress_bars.remove(bar_frame)

    def update_progress_bar(self,bar_frame):
        global app_dict
        
        selected_quest = self.quest_dropdown.get()
        # if selected quest is in quest_list, extract quest_list
        if selected_quest:
            app_name, maximum_time = selected_quest.split(" : ")
            maximum, time, _ = maximum_time.split(" ")
            time = (float(time) * 3600)
            
            if app_name in app_dict:
                current_time = app_dict[app_name]
            else:
                current_time = 0
            
            # get the current progress of the bar
            current_value = bar_frame.progress_bar.get()
            
            # calculate the new value until it reaches max (1.0) using do until
            if current_value < 1.0:
                new_value = current_time / time  # increase by 1% of the total time
                bar_frame.progress_bar.set(new_value)
                self.update_idletasks()
                # if the progress bar reaches 100%, show a message box
            
           
            
        
                    
                    
  

    


    def update_progress(self):
        global running, app_time_update, app_dict, update_tick, appname_dict, old_name_list
        
        while running:
            if app_time_update:
                self.app_list_TB.delete("0.0", "end")
                for app in app_dict:
                    if appname_dict and app in old_name_list:
                        self.app_list_TB.insert("end", f'{appname_dict[app]}: {app_dict[app]} seconds\n')
                    else:
                        self.app_list_TB.insert("end", f'{app}: {app_dict[app]} seconds\n')
                
                app_time_update = False
            sleep(update_tick)

    def update_quest(self):
        global running, quest_list_update, quest_dict, quest_list, update_tick, old_name_list
        
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

                        if appname_dict and quest[0] in old_name_list:
                            self.quest_list_TB.insert("0.0", f'{appname_dict[quest[0]]} : {maximum}{quest[2] / 60} hour\n')
                        else:
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
        global running, quest_complete_update, update_tick, old_name_list
        
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
                        
                        if appname_dict and quest[0] in old_name_list:
                            self.completed_list_TB.insert("end", f'{appname_dict[quest[0]]} {maximum} {int(quest[1]) / 60} hour(s): Completed +{quest[3]} points\n')
                        else:
                            self.completed_list_TB.insert("end", f'{quest[0]} {maximum} {int(quest[1]) / 60} hour(s): Completed +{quest[3]} points\n')
                
                    # Failed Quest Textbox Update
                    self.failed_list_TB.delete("0.0", "end")
                    cursor.execute("SELECT app_name, time, score_deduct FROM failed_quests")
                    failed_quests = cursor.fetchall()

                    for quest in failed_quests:
                        if appname_dict and quest[0] in old_name_list:
                            self.failed_list_TB.insert("end", f'{appname_dict[quest[0]]} < {int(quest[1]) / 60} hour(s): Failed -{quest[2]} points\n')
                        else:
                            self.failed_list_TB.insert("end", f'{quest[0]} < {int(quest[1]) / 60} hour(s): Failed -{quest[2]} points\n')

                    # App Name Change Log
                    cursor.execute("SELECT old_name, new_name FROM new_app_name")
                    names = cursor.fetchall()

                    self.namechange_list_TB.delete("0.0", "end")
                    for name in names:
                        self.namechange_list_TB.insert("end", f""" "{name[0]}" was changed into "{name[1]}"\n""")

                except sqlite3.Error as e:
                    if DEBUG: print(f"An error occurred: {e}")
                    conn.rollback()
                finally:
                    if conn:
                        conn.close()

                quest_complete_update = False
            sleep(update_tick)

    def update_stats(self): 
        global running, update_tick, stat_update
               
        while running:
            if stat_update:
                today = datetime.now()
                one_week_ago = (today - timedelta(days=7)).strftime('%Y-%m-%d')
        
                conn = sqlite3.connect('sproutime.db')
                cursor = conn.cursor()
                
                try:
                    #Time Spend for Each App For 1 Week
                    cursor.execute("SELECT app_name, duration FROM app_time WHERE date >= ?", (one_week_ago,))
                    app_time = cursor.fetchall()
                    
                    time_dict = {}
                    for app_name, time in app_time:
                        if app_name in time_dict:
                            time_dict[app_name] += time
                        else:   
                            time_dict[app_name] = time
                
                    self.time_spend_chart.update_data(time_dict)
                    self.after(100, self.time_spend_chart._draw_chart)

                    #Total Time Spend
                    cursor.execute("SELECT app_name, duration FROM app_time")
                    app_time = cursor.fetchall()
                    
                    time_dict = {}
                    for app_name, time in app_time:
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
                    
                    cursor.execute("SELECT date, quest_completed, quest_set FROM streak WHERE date <= ? ORDER BY date DESC", (str(date.today()),))
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
                    self.streak_label.configure(text=f'{day_left} more day(s) to go!')
                    
                except sqlite3.Error as e:
                    if DEBUG: print(f"An error occurred: {e}")
                    conn.rollback()
                finally:
                    if conn:
                        conn.close()
                
                stat_update = False
            sleep(update_tick)
            
    def start_updating(self):     
        tab = self.get()
        self.progress_active = tab == "Progress"
        self.quest_active = tab == "Quest"
        self.score_active = tab == "Score"
        self.stats_active = tab == "Stats"
        self.bar_active = tab == "Progress Bar"

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
            self.stats_thread = threading.Thread(target=self.update_stats, daemon=True)
            self.stats_thread.start()
        elif not self.stats_active and self.stats_thread and self.stats_thread.is_alive():
            # The thread will naturally pause in its while loop
            pass
        
        #Bar Tab
        if self.bar_active and (self.bar_thread is None or not self.bar_thread.is_alive()):
            self.bar_thread = threading.Thread(target=self.update_bar_tab, daemon=True)
            self.bar_thread.start()
        elif not self.bar_active and self.bar_thread and self.bar_thread.is_alive():
            pass

    def update_bar_tab(self):
        while self.bar_active:
            for bar_frame in self.progress_bars:
                self.update_progress_bar(bar_frame)
            sleep(1)

            

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
        app_list = get_all_app_list()
        self.app_dropdown.configure(values=app_list)

        self.appname_widgets = []

        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        for i, app in enumerate(app_list):
            label = ctk.CTkLabel(self.scrollable_frame, text=app)
            label.grid(row=i, column=0, padx=10, pady=5)

            entry = ctk.CTkEntry(self.scrollable_frame, placeholder_text="New name")
            entry.grid(row=i, column=1, padx=10, pady=5)

            self.appname_widgets.append((label, entry))

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

        if maximum == 0:
            completed_list.append(name)

        quest_list_update = True

    def change_app_name(self):
        global appname_dict, old_name_list, quest_list_update, quest_complete_update

        conn = sqlite3.connect("sproutime.db")
        cursor = conn.cursor()
        try:
            for label, entry in self.appname_widgets:
                new_name = entry.get().strip()
                if new_name: 
                    original_name = label.cget("text")
                    appname_dict[original_name] = new_name
                    old_name_list.append(original_name)
                    cursor.execute("SELECT * FROM new_app_name WHERE old_name = ?", (original_name,))
                    row = cursor.fetchone()
                    if row:
                        cursor.execute("DELETE FROM new_app_name WHERE old_name = ?", (original_name,))
                        conn.commit()
                    cursor.execute("INSERT INTO new_app_name (old_name, new_name) VALUES (?, ?)", (original_name, new_name))
                entry.delete(0, 'end')
                conn.commit()
        except sqlite3.Error as e:
            if DEBUG: print(f"An error occurred: {e}")
            conn.rollback()
        finally:
            if conn:
                conn.close()

        quest_list_update = True
        quest_complete_update = True
        
    def refresh_stat(self):
        global stat_update
        update_log(str(date.today()))
        load_past_data()
        stat_update = True

    def open_debug_menu(self):
        global debug_menu
    
        if debug_menu is None or not debug_menu.winfo_exists():
            debug_menu = DebugMenu(self)  # Pass the main window as parent
        else:
            debug_menu.focus()
        
class DrawPieChart(ctk.CTkFrame):
    def __init__(self, master, data, **kwargs):
        super().__init__(master, **kwargs)

        self.data = data
        self.colors = ["#6495ED", "#FFA07A", "#90EE90", "#F08080",
                       "#B0E0E6", "#A0522D", "#F08080", "#D3D3D3",
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
        self.pie_frame = ctk.CTkFrame(self, width=610, height=260, fg_color='#323232') # increased pie_frame width
        self.pie_frame.grid(row=0, column=0, sticky="nsew")

        # Create a canvas widget for the pie chart
        self.canvas = ctk.CTkCanvas(self.pie_frame, width=290, height=260, highlightthickness=0)
        self.canvas.pack(side="left", padx=10, pady=10) # Use pack for single element in frame

        # Create a frame for the legend
        legend_frame = ctk.CTkFrame(self.pie_frame, width=300, height=260) 
        legend_frame.pack(side="right", padx=5, pady=10, fill="y")
        legend_frame.grid_propagate(False) 

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

        for i, (label, value) in enumerate(self.data.items()):
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
                tags="pie_slice"  # Add a tag to identify slices
            )
            start_angle += angle

    def _create_legend(self):
        # Clear previous legend items
        for widget in self.legend_scrollable_frame.winfo_children():
            widget.pack_forget() 
        
        for i, (label, value) in enumerate(self.data.items()):
            minutes = value // 60
            hours = minutes // 60
            remaining_minutes = minutes % 60

            if minutes == 0:
                continue
            else:
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
        global app_time_update, quest_complete_update, quest_list_update, app_dict, quest_list, quest_dict, completed_list, failed_list, total_points, appname_dict, old_name_list
        
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
        
        app_dict = {}
        quest_list = []
        quest_dict = {}
        completed_list = []
        failed_list = []
        total_points = 0

        appname_dict = {}
        old_name_list = []
        
        setup_sql()
        app_time_update = True
        quest_list_update = True
        quest_complete_update = True
        
    def close_debug_menu(self):
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
                quest_set INTEGER NOT NULL
            );
        ''')

        cursor.execute('''
                CREATE TABLE IF NOT EXISTS new_app_name(
                    id INTEGER PRIMARY KEY,
                    old_name TEXT NOT NULL,
                    new_name TEXT
            );
        ''')

        cursor.execute('''
                CREATE TABLE IF NOT EXISTS failed_quests(
                    id INTEGER PRIMARY KEY,
                    date TEXT NOT NULL, --Store as YYYY-MM-DD
                    app_name TEXT NOT NULL,
                    time INTEGER NOT NULL,
                    score_deduct INTEGER NOT NULL
            );
        ''')
        
    except sqlite3.Error as e:
        if DEBUG: print(f"An error occurred: {e}")
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
            process = psutil.Process(pid)
            process_name = process.name()
            appName = process_name.split(".")[0].capitalize()
            if appName == "Chrome": 
                tabName = get_active_tab_name()
                if tabName == "URL not detected":
                    pass
                else:
                    appName = tabName

        except Exception as e:
            pass

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

def notify(app_name, info):
    if appname_dict and app_name in old_name_list:
        app_name = appname_dict[app_name]

    if sys.platform == 'darwin':
        pass
        
    elif sys.platform == 'win32':
        if info == "min time completed":
            Title = f"Quest Completed for {app_name}"
            Msg = f"Well done! You've spent enough time on {app_name}"
        
        elif info == "max time failed":
            Title = f"Quest Failed for {app_name}"
            Msg = f"Oh no! You've exceeded your screentime limit for {app_name}"

        elif info == "10 mins left":
            Title = f"10 minutes left for {app_name}"
            Msg = f"You are nearing your screentime limit for {app_name}"
        
        noti = winotify.Notification(app_id="Sproutime",
                title = Title,
                msg = Msg,
                duration = "long")
        
        noti.set_audio(winotify.audio.Default, loop=False)
        noti.show()

def load_past_data():
    global app_time_update, app_dict, completed_list, failed_list, total_points, appname_dict, old_name_list, quest_list, quest_dict
    
    app_dict = {}
    quest_list = []
    quest_dict = {}
    completed_list = []
    failed_list = []
    total_points = 0
    
    conn = sqlite3.connect('sproutime.db')
    cursor = conn.cursor()
    
    try:
        #App Time
        cursor.execute("SELECT app_name, duration FROM app_time WHERE date = ?", (str(date.today()),))
        apps = cursor.fetchall()
        
        for app in apps:
            app_dict[app[0]] = app[1]
            
        #Completed quest
        cursor.execute("SELECT app_name, maximum FROM quest_completion WHERE date = ?", (str(date.today()),))
        quests = cursor.fetchall()
        
        for quest in quests:
            completed_list.append(quest[0])
            
        #Total Score
        cursor.execute("SELECT SUM(score_earn) FROM quest_completion")
        score = cursor.fetchone()
        
        if score and score[0] is not None:
            total_points = score[0]

        #Updated new names
        cursor.execute("SELECT * FROM new_app_name")

        for col in cursor:
            old_name_list.append(col[1])
            appname_dict[col[1]] = col[2]


    except sqlite3.Error as e:
        if DEBUG: print(f"An error occurred: {e}")
        conn.rollback()
    finally:
        if conn:
            conn.close()
            
    app_time_update = True

def update_time():
    global app_name, app_dict, app_time_update, running, quest_complete_update, quest_dict, _d_time_speed, task_score, total_points, completed_list, stat_update
    
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
                
            if (quest_list) and (app_name in quest_list):
                if quest_dict[app_name]["time"] <= app_dict[app_name]:
                    if (quest_dict[app_name]["maximum"] == ">") and (app_name not in completed_list):
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
                        total_points += task_score
                        notify(app_name, "min time completed")
                                
                    #Failed Quest      
                    elif (quest_dict[app_name]["maximum"] == "<") and (app_name not in failed_list):
                        failed_list.append(app_name)
                        completed_list.remove(app_name)
                        
                        conn = sqlite3.connect('sproutime.db')
                        cursor = conn.cursor()

                        cursor.execute("SELECT time FROM quest WHERE app_name = ?", (app_name,))
                        quest = cursor.fetchone()
                        quest_time = quest[0]
                        
                        try:
                            cursor.execute("DELETE FROM quest_completion WHERE app_name = ? AND date = ?", (app_name, str(date.today())))
                            cursor.execute("INSERT INTO failed_quests (date, app_name, time, score_deduct) VALUES (?, ?, ?, ?)", (str(date.today()), app_name, quest_time, task_score))
                            conn.commit()
                        except sqlite3.Error as e:
                            if DEBUG: print(f"An error occurred: {e}")
                            conn.rollback()
                        finally:
                            if conn:
                                conn.close()
                        
                        total_points -= task_score
                        
                        notify(app_name, "max time failed")

                    quest_complete_update = True
                
                # 10 mins left till quest failed
                elif ((quest_dict[app_name]["time"] - 600) == app_dict[app_name]) and (quest_dict[app_name]["maximum"] == "<"):
                    notify(app_name, "10 mins left")

            app_time_update = True
            sleep(1)
    
def update_log(today):
    global app_dict, completed_list, quest_list, failed_list, task_score
    conn = sqlite3.connect('sproutime.db')
    cursor = conn.cursor()
    
    try:
        #App Time
        for app in app_dict:
            cursor.execute("SELECT COUNT(*) FROM app_time WHERE app_name = ? AND date = ?", (app, today))
            if cursor.fetchone()[0] > 0:
                cursor.execute("UPDATE app_time SET duration = ? WHERE app_name = ?", (app_dict[app], app))
            else:
                cursor.execute("INSERT INTO app_time (app_name, date, duration) VALUES (?, ?, ?)", (app, today, app_dict[app]))
        
        #Quest Completed For "<" Quest
        if (quest_list):
            cursor.execute("SELECT time, app_name FROM quest WHERE maximum = 0")
            quests = cursor.fetchall()
            
            for quest in quests:
                quest_time = quest[0]
                app_name = quest[1]
                
                if (app_name in quest_list) and (app_name not in failed_list):
                    cursor.execute("INSERT INTO quest_completion (date, app_name, time, maximum, score_earn) VALUES (?, ?, ?, 0, ?)", (today, app_name, quest_time, task_score))
                elif (app_name in failed_list):
                    cursor.execute("DELETE FROM quest_completion WHERE app_name = ? AND date = ?", (app, today))

        #Streak
        cursor.execute("SELECT COUNT(*) FROM quest")
        quest_set = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM streak WHERE date = ?", (today,))
        if quest_set > 0: 
            if cursor.fetchone()[0] > 0:
                cursor.execute("UPDATE streak SET quest_completed = ?, quest_set = ? WHERE date = ?", (len(completed_list), quest_set, today))
            else:
                cursor.execute("INSERT INTO streak (date, quest_completed, quest_set) VALUES (?, ?, ?)", (today, len(completed_list), quest_set))
        
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
appName = ""
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

#First load
running = True

time = [">1 hour", ">2 hours", '>3 hours', '<1 hour', '<2 hours']
temp_quest_time = time[0]
app_list = get_all_app_list()
tab_list = ["Any Tabs", "Youtube", "Reddit", "Instagram", "Facebook", "Linkedin"]
theme_options = ["Light", "Dark", "System"]
temp_quest_app = app_list[0]
temp_quest_tab = tab_list[0]
load_past_data()

p1 = threading.Thread(target=update_time)

p1.start()

Tabview(master=app).grid(row=0, column=0, columnspan=2, sticky="nsew")
app.protocol("WM_DELETE_WINDOW", on_closing)
app.mainloop()