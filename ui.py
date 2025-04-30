import customtkinter
from window import *

def setup_tab1(tab, tabview):
    """Configure Tab 1."""
    tab.columnconfigure(0, weight=1)

    # Add a button to switch to Tab 2
    button_tab1 = customtkinter.CTkButton(
        master=tab,
        text="Go to Tab 2",
        command=lambda: tabview.set("Tab 2")  # Switch to Tab 2
    )
    button_tab1.pack(padx=20, pady=20)

def setup_tab2(tab, tabview):
    """Configure Tab 2."""
    tab.columnconfigure(0, weight=1)

    # Create a frame and pass it to the plan function
    frame = customtkinter.CTkFrame(master=tab)
    frame.pack(pady=20, padx=20, fill="both", expand=True)
    app_list_TB = customtkinter.CTkTextbox(frame, width=1080, height=360)
    app_list_TB.pack(padx=20, pady=10, fill="both", expand=True)
    combobox = ctk.CTkComboBox(master=frame, values=app_list, command=combobox_callback)
    combobox.pack(padx=20, pady=10, fill="x")
    timebox = ctk.CTkComboBox(master=frame, values=time, command=timebox_callback)
    timebox.pack(padx=20, pady=10, fill="x")
    tabBox = ctk.CTkComboBox(master=frame, values=tab_list, command=tabBox_callback)
    def show_tabBox():
        tabBox.grid(row=1, column=1, padx=20, pady=10)  # Show the tabBox when needed
    button = ctk.CTkButton(master=frame, text="Save", command=save_quest_time)
    button.pack(padx=20, pady=10)
    quest_list_TB = ctk.CTkTextbox(frame, width=1080, height=360)
    quest_list_TB.pack(padx=20, pady=10, fill="both", expand=True)
    plan(frame)  # Call the plan function to populate Tab 2


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