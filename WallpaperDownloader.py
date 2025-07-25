import flet as ft
import subprocess
import threading
import base64
import re
import os
import winreg  # Required for Windows registry access
import json

# Global Variables
save_location = "Not set"
max_log_lines = 18  # Maximum number of lines to display in the console log
THEME_CONFIG_FILE = "theme.cfg"

def load_theme_mode():
    try:
        with open(THEME_CONFIG_FILE, "r") as f:
            data = json.load(f)
            return data.get("theme_mode", "dark")
    except Exception:
        return "dark"

def save_theme_mode(theme_mode):
    with open(THEME_CONFIG_FILE, "w") as f:
        json.dump({"theme_mode": theme_mode}, f)

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
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\\WOW6432Node\\Valve\\Steam") as key:
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

def open_SteamWorkshop(e):
    subprocess.Popen(['explorer', 'https://steamcommunity.com/app/431960/workshop/'])
  
def open_wallpaper_folder(e, page):
    # Define output_column and console_text_color as global to ensure they are accessible
    global output_column, console_text_color
    wallpaper_path = get_default_wallpaper_path()
    if wallpaper_path:
        subprocess.Popen(['explorer', wallpaper_path])
    else:
        printlog(page, "Error: Unable to find the Wallpaper Engine projects folder.", output_column, console_text_color)

# Remove printlog from inside main and define it globally, passing output_column and console_text_color as arguments

def printlog(page, text, output_column, console_text_color):
    output_column.controls.append(ft.Text(text, font_family="Roboto Mono", size=13, color=console_text_color))
    if len(output_column.controls) > max_log_lines:
        output_column.controls.pop(0)
    page.update()

def main(page: ft.Page):
    global save_location, output, output_column, console_text_color

    # --- Theme Mode ---
    theme_mode = load_theme_mode()
    page.theme_mode = ft.ThemeMode.DARK if theme_mode == "dark" else ft.ThemeMode.LIGHT
    page.theme = ft.Theme(
        color_scheme_seed=ft.Colors.BLUE,
        visual_density=ft.VisualDensity.COMFORTABLE,
    )

    # Window properties
    page.title = "Wallpaper Engine Workshop Downloader"
    page.window_title_bar_hidden = False
    page.window_title_bar_buttons_hidden = False
    page.window_width = 900
    page.window_height = 850
    page.window_min_width = 600
    page.window_min_height = 600
    page.window_icon = os.path.abspath("./assets/favicon.png")  # Ensure absolute path for icon
    page.icon = os.path.abspath("./assets/favicon.png")  # Set taskbar icon (Flet uses this for general app icon)
    page.padding = 0
    page.spacing = 0

    # --- Modern Card Layout ---
    def get_card(content, padding=14, margin=8, bgcolor=None):
        return ft.Card(
            content=ft.Container(
                content=content,
                padding=padding,
                bgcolor=None,  # No background, let the page gradient show
                border_radius=10,
            ),
            elevation=3,
            margin=margin,
        )

    # --- Output Console ---
    # Set console background color based on theme mode
    def get_console_bg():
        return ft.Colors.WHITE if page.theme_mode == ft.ThemeMode.LIGHT else ft.Colors.BLACK

    console_bg = get_console_bg()
    console_text_color = None  # Use default text color for theme

    output_column = ft.Column(
        scroll=ft.ScrollMode.ALWAYS,
        height=180,
        expand=True,
    )
    output = ft.Container(
        content=output_column,
        border=ft.border.all(1, ft.Colors.OUTLINE),
        border_radius=8,
        padding=7,
        bgcolor=console_bg,
        expand=True,
        alignment=ft.alignment.center,
    )

    # --- Theme Toggle ---
    def on_theme_toggle(e):
        new_mode = "light" if page.theme_mode == ft.ThemeMode.DARK else "dark"
        page.theme_mode = ft.ThemeMode.LIGHT if new_mode == "light" else ft.ThemeMode.DARK
        save_theme_mode(new_mode)
        # Update console background color after theme change
        output.bgcolor = get_console_bg()
        page.update()

    theme_toggle = ft.Switch(
        label="Dark Mode",
        value=page.theme_mode == ft.ThemeMode.DARK,
        on_change=on_theme_toggle,
        thumb_color=ft.Colors.BLUE,
        track_color=ft.Colors.BLUE_100,
        scale=0.8,
    )

    # --- UI Controls ---
    username = ft.Dropdown(
        options=[ft.dropdown.Option(account) for account in accounts],
        value=list(accounts.keys())[0],
        width=140,
        border_radius=6,
        label="Account",
        filled=True,
        dense=True,
        text_size=13,
    )

    link_input = ft.TextField(
        multiline=True,
        height=60,
        hint_text="Enter workshop items (one per line)",
        border_radius=6,
        filled=True,
        label="Workshop Items",
        dense=True,
        text_size=13,
    )

    save_location_text = ft.Text(
        f"Save Location: {save_location}",
        size=11,
        color=ft.Colors.SECONDARY,
    )

    # FilePicker must be initialized AFTER set_save_location is defined
    def set_save_location(e: ft.FilePickerResultEvent):
        global save_location
        if e.path and os.path.isdir(e.path):
            if 'projects' in e.path.replace("\\", "/") and 'myprojects' in e.path.replace("\\", "/"):
                save_location = e.path
                save_location_text.value = f"Save Location: {save_location}"
                with open('lastsavelocation.cfg', 'w') as file:
                    file.write(save_location)
                printlog(page, f"Save location set to: {save_location}", output_column, console_text_color)
                page.update()
            else:
                printlog(page, f"Invalid directory: '{e.path}' does not contain 'projects/myprojects'.", output_column, console_text_color)
        else:
            printlog(page, "Invalid save location: The selected directory is not valid.", output_column, console_text_color)
        page.update()

    file_picker = ft.FilePicker(on_result=set_save_location)
    page.overlay.append(file_picker)

    def select_save_location(e):
        file_picker.get_directory_path()

    def run_command(pubfileid):
        printlog(page, f"----------Downloading {pubfileid}--------", output_column, console_text_color)
        if save_location == "Not set" or not os.path.isdir(save_location):
            printlog(page, "Error: Save location is not set correctly.", output_column, console_text_color)
            return
        exe_path = "DepotdownloaderMod/DepotDownloadermod.exe"
        if not os.path.isfile(exe_path):
            printlog(page, f"Error: Downloader executable not found at '{exe_path}'.", output_column, console_text_color)
            return
        dir_option = f"-dir \"{save_location}/{pubfileid}\""
        command = f"{exe_path} -app 431960 -pubfile {pubfileid} -verify-all -username {username.value} -password {passwords[username.value]} {dir_option}"
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
        for line in process.stdout:
            printlog(page, line.strip(), output_column, console_text_color)
        process.stdout.close()
        process.wait()
        printlog(page, f"-------------Download finished-----------", output_column, console_text_color)

    def run_commands():
        links = link_input.value.splitlines()
        for link in links:
            if link:
                match = re.search(r'\b\d{8,10}\b', link.strip())
                if match:
                    run_command(match.group(0))
                else:
                    printlog(page, f"Invalid link: {link}", output_column, console_text_color)

    def start_thread(e):
        run_commands()

    run_button = ft.FilledButton(
        text="Download",
        icon=ft.Icons.FILE_DOWNLOAD_OUTLINED,
        on_click=start_thread,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=6),
            padding=10,
            text_style=ft.TextStyle(size=13),
        ),
    )

    select_button = ft.OutlinedButton(
        text="Select Save Location",
        icon=ft.Icons.MY_LOCATION,
        on_click=select_save_location,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=6),
            padding=10,
            text_style=ft.TextStyle(size=13),
        ),
    )

    manage_button = ft.OutlinedButton(
        text="Manage Downloaded Wallpapers",
        icon=ft.Icons.LIBRARY_BOOKS_SHARP,
        on_click=lambda e: open_wallpaper_folder(e, page),
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=6),
            padding=10,
            text_style=ft.TextStyle(size=13),
        ),
    )

    search_button = ft.OutlinedButton(
        text="Search for Wallpapers",
        icon=ft.Icons.LIBRARY_BOOKS_SHARP,
        on_click=open_SteamWorkshop,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=6),
            padding=10,
            text_style=ft.TextStyle(size=13),
        ),
    )

    # --- Layout ---
    # Remove card/container backgrounds so the gradient shows through
    def get_card(content, padding=14, margin=8, bgcolor=None):
        return ft.Card(
            content=ft.Container(
                content=content,
                padding=padding,
                bgcolor=None,  # No background, let the page gradient show
                border_radius=10,
            ),
            elevation=3,
            margin=margin,
        )

    # Set the page background gradient
    page.bgcolor = None
    page.gradient = ft.LinearGradient(
        begin=ft.alignment.top_left,
        end=ft.alignment.bottom_right,
        colors=[ft.Colors.WHITE, ft.Colors.BLUE_100] if page.theme_mode == ft.ThemeMode.LIGHT else [ft.Colors.BLACK, ft.Colors.BLUE_GREY_900],
    )

    page.add(
        ft.Column([
            ft.Row([
                ft.Text(
                    "Wallpaper Engine Workshop Downloader",
                    size=24,
                    weight=ft.FontWeight.BOLD,
                    text_align=ft.TextAlign.CENTER,
                    color=ft.Colors.BLUE_900 if page.theme_mode == ft.ThemeMode.LIGHT else ft.Colors.BLUE_100,
                    expand=True,
                ),
                theme_toggle,
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER, expand=True),
            get_card(
                ft.Column([
                    ft.Row([
                        username,
                        select_button,
                    ], spacing=10),
                    save_location_text,
                ], spacing=8),
            ),
            get_card(
                ft.Column([
                    link_input,
                    ft.Row([
                        run_button,
                        manage_button,
                        search_button,
                    ], alignment=ft.MainAxisAlignment.SPACE_EVENLY, spacing=10),
                ], spacing=10),
            ),
            get_card(
                ft.Column([
                    ft.Text("Console Output", size=13, weight=ft.FontWeight.BOLD),
                    output,
                ], spacing=6, expand=True),
            ),
        ], spacing=0, expand=True),
    )

ft.app(target=main)
