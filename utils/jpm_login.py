from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium import webdriver
from itertools import count
import subprocess
import glob
import time
import sys
import os


def remove_files_by_matching_pattern(dir_path: str, pattern: str) -> None:
    """Delete all files from a given directory based on matching pattern."""
    [os.remove(fn) for fn in glob.glob(f'{dir_path}/{pattern}')]


def download_wait(poll_folder: str, pattern: str) -> str:
    """Wait for and return the first matching file in the poll folder."""
    while not (ica_file := glob.glob(f'{poll_folder}/{pattern}')):
        print(f'{next(counter)} Waiting for ica file in {poll_folder}...')
        time.sleep(1)
    return ica_file[0]


def wait_and_click(x_path: str, **kwargs) -> None:
    """Wait for element to be clickable and perform action."""
    obj = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.XPATH, x_path))
    )
    if 'send_key' in kwargs:
        obj.send_keys(kwargs.get('send_key'))
    elif 'click' in kwargs:
        obj.click()
    else:
        raise ValueError("Either 'send_key' or 'click' must be provided")


def open_firefox_flatpak() -> webdriver.Firefox:
    """Initialize and return Firefox webdriver."""
    options = Options()
    browser = webdriver.Firefox(options=options)
    browser.get(JPM_LOGIN_URL)
    return browser


# Constants and configuration
counter = count()
pcode = sys.argv[1]
JPM_USER = os.getenv('JPM_USER')
JPM_PASSWORD = os.getenv('JPM_PASSWORD')
JPM_LOGIN_URL = 'http://myworkspace.jpmchase.com'
DOWNLOAD_FOLDER = '/home/admin/Downloads'
ICA_CLIENT_PATH = '/opt/Citrix/ICAClient/wfica.sh'

# Main execution
if __name__ == "__main__":
    remove_files_by_matching_pattern(DOWNLOAD_FOLDER, '*.ica')
    driver = open_firefox_flatpak()

    # Login sequence
    wait_and_click('//*[@id="login"]', send_key=JPM_USER)
    wait_and_click('(//input[@type="password"])[1]', send_key=JPM_PASSWORD)
    wait_and_click('(//input[@type="password"])[2]', send_key=pcode)
    wait_and_click('//*[@id="loginBtn"]', click=True)

    # Protocol handler setup
    wait_and_click('//*[@id="protocolhandler-welcome-installButton"]', click=True)
    wait_and_click('//*[@id="protocolhandler-detect-alreadyInstalledLink"]', click=True)
    wait_and_click('//*[@id="jpmcAcceptDisclaimerBtn"]', click=True)

    # Workspace selection
    wait_and_click('//*[@class="storeapp-name"  and contains(text(),"CDC2")]',click=True)
    wait_and_click('//*[@class="theme-highlight-color appDetails-actions-text" and contains(text(),"Open") ]',click=True)
    # Handle ICA file
    ica_file = download_wait(DOWNLOAD_FOLDER, '*.ica')
    cmd_line = f'{ICA_CLIENT_PATH} {ica_file}'
    subprocess.Popen(
        cmd_line,
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    driver.quit()
    print(f'{next(counter)} Opened ica window. Close this terminal')