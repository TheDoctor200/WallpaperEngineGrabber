import flet as ft
import subprocess
import threading
import base64
import re
import os
import winreg  # Required for Windows registry access

# Global Variables
save_location = "Not set"
max_log_lines = 18  # Maximum number of lines to display in the console log

accounts = {
    'ruiiixx': 'UzY3R0JUQjgzRDNZ',
    'premexilmenledgconis': 'M3BYYkhaSmxEYg==',
    'vAbuDy': 'Qm9vbHE4dmlw',
    'adgjl1182': 'UUVUVU85OTk5OQ==',
    'gobjj16182': 'enVvYmlhbzgyMjI=',
    '787109690': 'SHVjVXhZTVFpZzE1'
}
passwords = {account: base64.b64decode(accounts[account]).decode('utf-8') for account in accounts}

def get_steam_path():
    """Fetch the Steam install path from the Windows registry."""
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam") as key:
            steam_path, _ = winreg.QueryValueEx(key, "InstallPath")
            return steam_path
    except FileNotFoundError:
        return None

def get_default_wallpaper_path():
    """Determine the default Wallpaper Engine projects folder."""
    steam_path = get_steam_path()
    if steam_path:
        wallpaper_path = os.path.join(steam_path, "steamapps", "common", "wallpaper_engine", "projects", "myprojects")
        if os.path.isdir(wallpaper_path):
            return wallpaper_path
    return None

# Load save location from config file
def load_save_location():
    global save_location
    try:
        with open('lastsavelocation.cfg', 'r') as file:
            target_directory = file.read().strip()
            if os.path.isdir(target_directory):
                save_location = target_directory
            else:
                save_location = get_default_wallpaper_path() or "Not set"
    except FileNotFoundError:
        save_location = get_default_wallpaper_path() or "Not set"

load_save_location()

def printlog(page, text):
    """Function to log output into the console and update UI."""
    # Add the new message to the log
    output.controls.append(ft.Text(text))  # Append new text control to the output column
    # If we have more than max_log_lines messages, remove the first (oldest) one
    if len(output.controls) > max_log_lines:
        output.controls.pop(0)
    page.update()  # Ensure the UI updates to reflect changes

def open_wallpaper_folder(e):  # Accept the event argument
    """Open the Wallpaper Engine 'myprojects' folder in the file explorer."""
    wallpaper_path = get_default_wallpaper_path()
    if wallpaper_path:
        subprocess.Popen(['explorer', wallpaper_path])
    else:
        printlog("Error: Unable to find the Wallpaper Engine projects folder.")

def main(page: ft.Page):
    global save_location, output

    page.title = "Wallpaper Engine Workshop Downloader"
    page.window_width = 600
    page.window_height = 600
    
    # Create a scrollable output field to display log messages
    output = ft.Column(scroll=ft.ScrollMode.ALWAYS, height=300)  # Make the log area bigger
    username = ft.Dropdown(options=[ft.dropdown.Option(account) for account in accounts], value=list(accounts.keys())[0])
    link_input = ft.TextField(multiline=True, height=150, hint_text="Enter workshop items (one per line)")
    save_location_text = ft.Text(f"Save Location: {save_location}")

    # FilePicker must be initialized AFTER set_save_location is defined
    def set_save_location(e: ft.FilePickerResultEvent):
        global save_location
        if e.path and os.path.isdir(e.path):
            # Check if the selected directory contains 'projects/myprojects' within the path
            if 'projects' in e.path.replace("\\", "/") and 'myprojects' in e.path.replace("\\", "/"):
                save_location = e.path
                save_location_text.value = f"Save Location: {save_location}"
                # Save the valid location to the config file
                with open('lastsavelocation.cfg', 'w') as file:
                    file.write(save_location)
                printlog(page, f"Save location set to: {save_location}")
                page.update()
            else:
                printlog(page, f"Invalid directory: '{e.path}' does not contain 'projects/myprojects'.")
        else:
            printlog(page, "Invalid save location: The selected directory is not valid.")
        page.update()

    file_picker = ft.FilePicker(on_result=set_save_location)
    page.overlay.append(file_picker)

    def select_save_location(e):
        file_picker.get_directory_path()

    def run_command(pubfileid):
        printlog(page, f"----------Downloading {pubfileid}--------")
        if save_location == "Not set" or not os.path.isdir(save_location):
            printlog(page, "Error: Save location is not set correctly.")
            return
        
        dir_option = f"-dir \"{save_location}/{pubfileid}\""
        command = f"DepotdownloaderMod/DepotDownloadermod.exe -app 431960 -pubfile {pubfileid} -verify-all -username {username.value} -password {passwords[username.value]} {dir_option}"
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in process.stdout:
            printlog(page, line.strip())
        process.stdout.close()
        process.wait()
        printlog(page, f"-------------Download finished-----------")
    
    def run_commands():
        links = link_input.value.splitlines()
        for link in links:
            if link:
                match = re.search(r'\b\d{8,10}\b', link.strip())
                if match:
                    run_command(match.group(0))
                else:
                    printlog(page, f"Invalid link: {link}")
    
    def start_thread(e):
        threading.Thread(target=run_commands).start()

    run_button = ft.ElevatedButton(text="Download", icon= ft.Icons.FILE_DOWNLOAD_OUTLINED, on_click=start_thread)
    select_button = ft.ElevatedButton(text="Select Save Location", icon= ft.Icons.MY_LOCATION, on_click=select_save_location)
    manage_button = ft.ElevatedButton(text="Manage Wallpapers", icon= ft.Icons.LIBRARY_BOOKS_SHARP, on_click=open_wallpaper_folder)  # Added Manage Wallpapers Button
    
    # Placing the buttons side by side
    buttons_row = ft.Row([run_button, manage_button])

    # Add the buttons and other elements
    page.add(
    ft.Text("Wallpaper Engine Workshop Downloader", size=20, weight=ft.FontWeight.BOLD),
    ft.Row([ft.Text("Select Account:"), username]),
    select_button, save_location_text,
    ft.Text("Enter workshop items (one per line):"), link_input,
    buttons_row,  # Add the buttons side by side
        ft.Container(
            content=ft.Text(
                "Made by TheDoctor",
                color=ft.colors.WHITE,
                weight=ft.FontWeight.BOLD,
                size=16,
            ),
            margin=ft.margin.only(top=20),  # Add some space from the content above
            padding=ft.padding.only(right=20, bottom=10),
            alignment=ft.alignment.center_right,
            expand=True,  # Allow container to expand
        ),
    )
    
ft.app(target=main)
