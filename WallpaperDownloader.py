import flet as ft
import subprocess
import threading
import base64
import re
import os
import winreg  # Required for Windows registry access
import json
import sys

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

def ensure_icon_compatibility(icon_path):
    """Ensure the icon is compatible with Windows taskbar and app icon requirements."""
    if not icon_path or not os.path.exists(icon_path):
        return None
    
    # For Windows, .ico files work best for taskbar icons
    if icon_path.endswith('.ico'):
        return icon_path
    
    # If it's a PNG, we might need to convert it or use it as is
    # Flet should handle PNG icons, but .ico is more reliable for Windows
    return icon_path

def create_windows_icon():
    """Create a Windows-compatible icon file for the application."""
    try:
        # Check if we have the required assets
        assets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
        ico_path = os.path.join(assets_dir, "favicon.ico")
        png_path = os.path.join(assets_dir, "favicon.png")
        
        if os.path.exists(ico_path):
            return ico_path
        elif os.path.exists(png_path):
            # Try to convert PNG to ICO if PIL is available
            try:
                from PIL import Image
                img = Image.open(png_path)
                # Create a proper ICO file with multiple sizes
                icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
                img.save(ico_path, format='ICO', sizes=icon_sizes)
                print(f"Created ICO file: {ico_path}")
                return ico_path
            except ImportError:
                print("PIL not available, using PNG as fallback")
                return png_path
            except Exception as e:
                print(f"Error converting PNG to ICO: {e}")
                return png_path
        else:
            print("No icon files found in assets directory")
            return None
    except Exception as e:
        print(f"Error creating Windows icon: {e}")
        return None

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
        # Use os.path.join to properly handle paths with spaces
        wallpaper_path = os.path.join(steam_path, "steamapps", "common", "wallpaper_engine", "projects", "myprojects")
        if os.path.isdir(wallpaper_path):
            return wallpaper_path
        # Alternative: try to find the path even if some components have spaces
        try:
            # Check if the path exists by testing each component
            test_path = steam_path
            for component in ["steamapps", "common", "wallpaper_engine", "projects", "myprojects"]:
                test_path = os.path.join(test_path, component)
                if not os.path.exists(test_path):
                    break
            if os.path.isdir(test_path):
                return test_path
        except Exception:
            pass
    return None

# Load save location from config file
def load_save_location():
    global save_location
    try:
        with open('lastsavelocation.cfg', 'r', encoding='utf-8') as file:
            target_directory = file.read().strip()
            # Handle paths with spaces and validate the structure
            if target_directory and os.path.isdir(target_directory):
                # Validate that it contains the required projects/myprojects structure
                normalized_path = target_directory.replace("\\", "/")
                if 'projects' in normalized_path and 'myprojects' in normalized_path:
                    path_parts = normalized_path.split('/')
                    try:
                        projects_index = path_parts.index('projects')
                        myprojects_index = path_parts.index('myprojects')
                        if myprojects_index > projects_index:
                            save_location = target_directory
                        else:
                            save_location = get_default_wallpaper_path() or "Not set"
                    except ValueError:
                        save_location = get_default_wallpaper_path() or "Not set"
                else:
                    save_location = get_default_wallpaper_path() or "Not set"
            else:
                save_location = get_default_wallpaper_path() or "Not set"
    except (FileNotFoundError, UnicodeDecodeError, Exception):
        save_location = get_default_wallpaper_path() or "Not set"

load_save_location()

def open_SteamWorkshop(e):
    subprocess.Popen(['explorer', 'https://steamcommunity.com/app/431960/workshop/'])
  
def open_wallpaper_folder(e, page):
    # Define output_column and console_text_color as global to ensure they are accessible
    global output_column, console_text_color
    wallpaper_path = get_default_wallpaper_path()
    if wallpaper_path:
        try:
            # Use shell=True to properly handle paths with spaces in Windows Explorer
            subprocess.Popen(f'explorer "{wallpaper_path}"', shell=True)
        except Exception as e:
            printlog(page, f"Error opening folder: {str(e)}", output_column, console_text_color)
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

    # Use sys._MEIPASS for asset paths if running as a bundled app
    if hasattr(sys, "_MEIPASS"):
        BASE_DIR = sys._MEIPASS
    else:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    ASSETS_DIR = os.path.join(BASE_DIR, "assets")
    favicon_path = os.path.join(ASSETS_DIR, "favicon.ico")
    
    # Fallback paths for favicon - prioritize .ico files for Windows
    favicon_fallback_paths = [
        os.path.join(ASSETS_DIR, "favicon.png"),
        os.path.join(BASE_DIR, "favicon.ico"),
        os.path.join(BASE_DIR, "favicon.png"),
        os.path.join(os.path.dirname(BASE_DIR), "assets", "favicon.ico"),
        os.path.join(os.path.dirname(BASE_DIR), "assets", "favicon.png")
    ]

    # Find the best available icon - prioritize .ico files for Windows
    icon_path = None
    
    # Try to create or find a Windows-compatible icon
    icon_path = create_windows_icon()
    
    # If no icon was created, fall back to the original detection method
    if not icon_path:
        # First try .ico files (best for Windows taskbar)
        ico_paths = [
            os.path.join(ASSETS_DIR, "favicon.ico"),
            os.path.join(BASE_DIR, "favicon.ico"),
            os.path.join(os.path.dirname(BASE_DIR), "assets", "favicon.ico")
        ]
        
        for ico_path in ico_paths:
            if os.path.exists(ico_path):
                icon_path = ico_path
                break
        
        # Fallback to PNG if no .ico found
        if not icon_path:
            for fallback_path in favicon_fallback_paths:
                if fallback_path.endswith('.png') and os.path.exists(fallback_path):
                    icon_path = fallback_path
                    break

    # Window properties
    page.title = "Wallpaper Engine Workshop Downloader"
    page.window_title = "Wallpaper Engine Workshop Downloader"
    page.window_title_bar_hidden = False
    page.window_title_bar_buttons_hidden = False
    page.window_width = 900
    page.window_height = 850
    page.window_min_width = 600
    page.window_min_height = 600
    page.window_resizable = True
    page.window_center = True
    page.window_maximizable = True
    page.window_always_on_top = False
    
    # Set window icon, app icon, and tray icon (if supported)
    if icon_path:
        # Ensure icon compatibility for Windows
        compatible_icon = ensure_icon_compatibility(icon_path)
        print(f"Setting icon to: {icon_path} (compatible: {compatible_icon})")
        
        page.window_icon = compatible_icon
        page.icon = compatible_icon
        
        # Set taskbar icon explicitly for Windows
        try:
            page.tray_icon = compatible_icon  # For Flet >=0.14.0, sets Windows tray/taskbar icon
        except Exception as e:
            print(f"Error setting tray icon: {e}")
        
        # Additional Windows-specific icon settings for taskbar
        try:
            # Set the app icon for the taskbar using Windows API
            import ctypes
            myappid = 'wallpaper.engine.workshop.downloader.1.0'  # arbitrary string
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
            
            # Also try to set the icon using the icon path
            if compatible_icon and compatible_icon.endswith('.ico'):
                try:
                    # Load the icon and set it for the process
                    import win32api
                    import win32con
                    import win32gui
                    win32gui.SetClassLong(win32gui.GetForegroundWindow(), win32con.GCL_HICON, 
                                        win32api.LoadImage(0, compatible_icon, win32con.IMAGE_ICON, 0, 0, win32con.LR_LOADFROMFILE))
                except ImportError:
                    # win32api not available, skip this method
                    pass
                except Exception as e:
                    print(f"Error setting Windows icon: {e}")
        except Exception as e:
            print(f"Error setting Windows app ID: {e}")
    else:
        print("No icon found!")
    
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
        # Update page gradient
        page.gradient = ft.LinearGradient(
            begin=ft.alignment.top_left,
            end=ft.alignment.bottom_right,
            colors=[ft.Colors.WHITE, ft.Colors.BLUE_100] if page.theme_mode == ft.ThemeMode.LIGHT else [ft.Colors.BLACK, ft.Colors.BLUE_GREY_900],
        )
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
            # Normalize path separators and check if it contains the required structure
            normalized_path = e.path.replace("\\", "/")
            if 'projects' in normalized_path and 'myprojects' in normalized_path:
                # Additional validation: ensure the path structure is correct
                path_parts = normalized_path.split('/')
                try:
                    projects_index = path_parts.index('projects')
                    myprojects_index = path_parts.index('myprojects')
                    # Check if myprojects is a subdirectory of projects
                    if myprojects_index > projects_index:
                        save_location = e.path
                        save_location_text.value = f"Save Location: {save_location}"
                        with open('lastsavelocation.cfg', 'w') as file:
                            file.write(save_location)
                        printlog(page, f"Save location set to: {save_location}", output_column, console_text_color)
                        page.update()
                    else:
                        printlog(page, f"Invalid directory structure: 'myprojects' must be a subdirectory of 'projects'.", output_column, console_text_color)
                except ValueError:
                    printlog(page, f"Invalid directory: '{e.path}' does not contain the required 'projects/myprojects' structure.", output_column, console_text_color)
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
        
        # Properly handle paths with spaces by using os.path.join and proper quoting
        target_dir = os.path.join(save_location, str(pubfileid))
        dir_option = f"-dir \"{target_dir}\""
        
        # Build command as a list to avoid shell parsing issues with spaces
        command = [
            exe_path,
            "-app", "431960",
            "-pubfile", str(pubfileid),
            "-verify-all",
            "-username", username.value,
            "-password", passwords[username.value],
            "-dir", target_dir
        ]
        
        try:
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            for line in process.stdout:
                printlog(page, line.strip(), output_column, console_text_color)
            process.stdout.close()
            process.wait()
            printlog(page, f"-------------Download finished-----------", output_column, console_text_color)
        except Exception as e:
            printlog(page, f"Error running download command: {str(e)}", output_column, console_text_color)

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

if __name__ == "__main__":
    # For proper Windows taskbar icon support, build with:
    # flet build --name "Wallpaper Engine Workshop Downloader" --icon assets/favicon.ico --product-name "Wallpaper Engine Workshop Downloader" --product-version "1.0.0" --company-name "Your Company" --file-description "Wallpaper Engine Workshop Downloader" --copyright "Copyright (c) 2024" --targets windows
    
    ft.app(target=main)