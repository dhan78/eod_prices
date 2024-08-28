import pyautogui
import pygetwindow as gw
import time

def find_window(title):
    windows = gw.getWindowsWithTitle(title)
    if windows:
        return windows[0]
    return None

def click_window(window):
    if window:
        window.activate()
        x, y = window.center
        pyautogui.click(x, y)
        print(f"Clicked on window '{window.title}' at position ({x}, {y})")
    else:
        print("Window not found")

def type_in_window(window, text):
    if window:
        window.activate()
        pyautogui.write(text)
        print(f"Typed '{text}' in window '{window.title}'")
    else:
        print("Window not found")

window_title = "Your Window Title Here"
text_to_type = "Your text here"

while True:
    window = find_window(window_title)
    click_window(window)
    type_in_window(window, text_to_type)
    time.sleep(60)
