# sproutime
A desktop application that tracks application screen time, allows users to set usage goals, and rewards them upon completion.

Traditional app usage limiting solutions often focus solely on restrictions without offering positive reinforcement; our app provides an innovative solution by integrating both.

## ✨ Features

* **Set Daily Quests:** Navigate to the "Quest" tab to define daily time limits or usage goals for individual applications. For example, set a quest to "Use a learning app for 1 hour."

* **View App Usage:** The "Stat" section displays your app usage in an intuitive pie chart, allowing you to see where your time is spent.

* **Quest Completion Notifications:** Receive immediate, friendly notifications on your desktop when you successfully complete a quest, providing positive reinforcement.

* **Import/Export Data:** Use the "Setting" menu to import quest configurations and usage data from another device or export your current data for backup or transfer.

* **Watch Your Tree Grow:** In the "Garden" section, observe your virtual tree flourish and grow as you complete more quests, visually rewarding your progress.

## 🚀 Installation for Mac
Follow these steps to get a copy of the project up and running on your local machine.

1. Install pyinstaller
```
pip install pyinstaller
```
   
2. Clone the repository
```
git clone https://github.com/JuneMinazuki/sproutime.git
```

3. Build the app using terminal
```
pyinstaller --windowed --name Sproutime --add-data img:img --add-data database/sproutime.db:database sproutime.py
```

## 🪟 Installation for Windows
1. Install pyinstaller
```
pip install pyinstaller
```

2. Clone the repository
```
git clone https://github.com/JuneMinazuki/sproutime.git
```

3. Build the app using powershell
```
pyinstaller --windowed --name Sproutime --add-data "img;img" --add-data "database/sproutime.db;database" sproutime.py
```

## 💡 Usage
**Basic workflow:** Our app helps you manage screen time positively by letting you set **daily quests** for specific applications. It **automatically tracks usage** in the background, shows your progress, **notifies** you when quests are complete, and visually represents your achievements through **tree growth**. You can also easily **import and export** your quest and app data.

**Example scenarios:**

1. A parent wants their child to spend 1 hour on an educational app each day. They set a quest for this app. The child uses the app, receives a notification upon completion, and sees their virtual tree grow a bit taller, encouraging continued positive habits.

2. A user wants to limit their social media use. They set a daily quest for a social media app. The app tracks their usage, notifies them if they exceed the limit, and allows them to review their usage patterns on the pie chart to adjust their habits.

## 📸 Screenshots

<img width="1230" alt="Screenshot 2025-06-11 at 10 17 42 PM" src="https://github.com/user-attachments/assets/48ccfdf2-13cd-4682-8ee0-93fb9619eaff" />
<img width="1238" alt="Screenshot 2025-06-11 at 10 16 43 PM" src="https://github.com/user-attachments/assets/35f5defe-cd92-46e1-bc70-66215fd12713" />
<img width="1191" alt="Screenshot 2025-06-11 at 10 14 47 PM" src="https://github.com/user-attachments/assets/0ae4a934-ab9b-46a1-a8ed-0cb8985a3c1a" />
<img width="1181" alt="Screenshot 2025-06-11 at 10 15 46 PM" src="https://github.com/user-attachments/assets/c1d32c06-eebe-464f-b775-3b5d0674e9a1" />
<img width="1182" alt="Screenshot 2025-06-11 at 10 16 26 PM" src="https://github.com/user-attachments/assets/ef6603ea-f906-4712-9fe5-57c2030a10da" />
<img width="1237" alt="Screenshot 2025-06-11 at 10 17 35 PM" src="https://github.com/user-attachments/assets/16f93623-6b4b-423c-9bd2-a9d9c46e17d7" />
