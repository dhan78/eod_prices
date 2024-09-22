from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import sys
import glob, os
import time
import subprocess
import fnmatch
from itertools import count
from selenium.webdriver.firefox.options import Options


counter = count()
pcode = sys.argv[1]
JPM_USER = os.getenv('JPM_USER')
JPM_PASSWORD = os.getenv('JPM_PASSWORD')
JPM_LOGIN_URL = 'http://myworkspace.jpmchase.com'
download_folder = '/home/admin/Downloads'

from selenium import webdriver

'''
Generic function to delete all the files from a given directory based on matching pattern
'''


def removeFilesByMatchingPattern(dirPath, pattern):
    [os.remove(fn) for fn in glob.glob(f'{dirPath}/{pattern}')]


def download_wait(poll_folder, pattern):
    while not (ica_file := glob.glob(f'{poll_folder}/{pattern}')):
        print(f'{next(counter)} Waiting for ica file in {poll_folder}...')
        time.sleep(1)
    return ica_file[0]


def wait_and_click(x_path, **kwargs):
    obj = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, x_path)))
    if 'send_key' in kwargs:
        obj.send_keys(kwargs.get('send_key'))
    elif 'click' in kwargs:
        obj.click()
    else:
        raise

def open_firefox_flatpak():
    # Set up Firefox options
    options = Options()
    #options.binary_location = firefox_binary_path

    # Create a Firefox webdriver with the specified options
    browser = webdriver.Firefox(options=options)
    browser.get(JPM_LOGIN_URL)
    return browser



removeFilesByMatchingPattern(download_folder, '*.ica')

# driver = open_chrome_browser()
# driver = open_firefox_browser()
driver = open_firefox_flatpak()


wait_and_click('//*[@id="login"]', send_key=JPM_USER)
wait_and_click('(//input[@type="password"])[1]', send_key=JPM_PASSWORD)
wait_and_click('(//input[@type="password"])[2]', send_key=pcode)

wait_and_click('//*[@id="loginBtn"]', click=True)

wait_and_click('//*[@id="protocolhandler-welcome-installButton"]', click=True)
wait_and_click('//*[@id="protocolhandler-detect-alreadyInstalledLink"]', click=True)

wait_and_click('//*[@id="jpmcAcceptDisclaimerBtn"]', click=True)

wait_and_click('//*[@class="storeapp-name"  and contains(text(),"WorkSpace Enterprise_CDC1")]',click=True)
wait_and_click('//*[@class="theme-highlight-color appDetails-actions-text" and contains(text(),"Open") ]',click=True)

ica_file = download_wait(download_folder, '*.ica')

cmd_line = '/opt/Citrix/ICAClient/wfica.sh ' + ica_file

subprocess.Popen(cmd_line, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

driver.quit()
print(f'{next(counter)} Opened ica window. Close this terminal')