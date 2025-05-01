import customtkinter
from window import *
import sys
import threading
import time



def setup_tab1(tab, tabview):
    """Configure Tab 1."""
    tab.columnconfigure(0, weight=1)
    global current_time, running, time_lock

    # Add a label to display the current time
    label_time = customtkinter.CTkLabel(
        master=tab,
        text=f"Current Time:{current_time}",
        font=("Arial", 16)
    )
    label_time.pack(padx=20, pady=20)

    # Update the label every second
    def update_time():
        global current_time, running, time_lock
        current_time = time.strftime("%Y-%m-%d %H:%M:%S")
        with time_lock:
            label_time.configure(text=f"Current Time: {current_time}")
        if running:
            tab.after(1000, update_time)
    update_time()

    # Add a label
    label_info = customtkinter.CTkLabel(tab, text="Timer is started", font=("Arial", 16))
    label_info.pack(padx=20, pady=20)

    # Add a button to switch to Tab 2
    button_tab1 = customtkinter.CTkButton(
        master=tab,
        text="View Timer",
        command=lambda: tabview.set("Tab 2")  # Switch to Tab 2
    )
    button_tab1.pack(padx=20, pady=20)

    # Add a close button with sys.exit()
    button_close = customtkinter.CTkButton(tab, text="Close", command=on_closing)
    button_close.pack(padx=20, pady=20)
    



def setup_tab2(tab, tabview):
    """Configure Tab 2."""
    tab.columnconfigure(0, weight=1)
    global count, running, counter_lock
    label_count = customtkinter.CTkLabel(tab, text=f"Count: {count}", font=("Arial", 16))
    label_count.pack(padx=20, pady=20)
    
    # update count every second
    def update_count():
        global count, running, counter_lock
        with counter_lock:
            label_count.configure(text=f"Count: {count}")
            count += 1
        if running:
            tab.after(1000, update_count)
    update_count()

def setup_tab3(tab):
    """Configure Tab 3 (Theme Selection)."""
    tab.columnconfigure(0, weight=1)

    # Add a dropdown menu to select the theme
    theme_options = ["Light", "Dark", "System"]
    theme_selector = customtkinter.CTkOptionMenu(
        master=tab,
        values=theme_options,
        command=lambda theme: customtkinter.set_appearance_mode(theme)  # Change theme
    )
    theme_selector.pack(padx=20, pady=20)
    theme_selector.set("System")  # Set default theme to "System"




# Make application window
window = customtkinter.CTk()
window.geometry("1080x720")
window.title("Sproutime --main menu")

# Create a TabView
tabview = customtkinter.CTkTabview(window)
tabview.pack(pady=20, padx=20, fill="both", expand=True)

# global variables
count = 0
current_time = time.strftime("%Y-%m-%d %H:%M:%S")
running = True
counter_lock = threading.Lock()
time_lock = threading.Lock()



# Add tabs
tabview.add("Tab 1")  # Add Tab 1
tabview.add("Tab 2")  # Add Tab 2
tabview.add("Tab 3")  # Add Tab 3 (Theme Selection)
tabview.set("Tab 1")  # Set Tab 1 as the default visible tab

# Configure tabs
setup_tab1(tabview.tab("Tab 1"), tabview)
setup_tab2(tabview.tab("Tab 2"), tabview)
setup_tab3(tabview.tab("Tab 3"))



# when user close the program
def on_closing():
    exit()
window.protocol("WM_DELETE_WINDOW", on_closing) #check for if user close the program

window.mainloop()