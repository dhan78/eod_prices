from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import sys
import glob, os
import time
import subprocess
import fnmatch
from itertools import count

counter = count()
pcode = sys.argv[1]
JPM_USER = os.getenv('JPM_USER')
JPM_PASSWORD = os.getenv('JPM_PASSWORD')
JPM_LOGIN_URL = 'http://myworkspace.jpmchase.com'

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


def open_chrome_browser():

    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.webdriver.common.by import By

    s=Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=s)

    options = webdriver.ChromeOptions()
    options.add_argument("--incognito")
    options.binary_location="/usr/local/bin/chromium"
    # options.add_argument("--headless")
    browser = webdriver.Chrome(executable_path='/usr/bin/chromedriver', options=options)
    browser.maximize_window()
    browser.get(JPM_LOGIN_URL)
    return browser


def open_firefox_browser():
    from selenium import webdriver
    from selenium.webdriver.firefox.options import Options
    from selenium.webdriver.firefox.service import Service

    options = Options()
    options.binary_location = r'/usr/bin/firefox'
    # options.binary_location = r'/var/lib/flatpak/exports/bin/org.mozilla.firefox'
    # options.add_argument("--profile /home/admin/.mozilla")
    # options.add_argument("--private")


    driverService = Service(r'/usr/bin/geckodriver')
    browser = webdriver.Firefox(service= driverService, options=options,)
    # options.add_argument("--incognito")
    # options.add_argument("--headless")
    # browser = webdriver.Chrome(options=options)
    # browser.maximize_window()
    browser.get(JPM_LOGIN_URL)
    return browser


download_folder = '/home/admin/Downloads'

removeFilesByMatchingPattern(download_folder, '*.ica')

# driver = open_chrome_browser()
driver = open_firefox_browser()


wait_and_click('//*[@id="login"]', send_key=JPM_USER)
wait_and_click('//*[@id="passwd1"]', send_key=JPM_PASSWORD)
wait_and_click('//*[@id="passwd"]', send_key=pcode)
wait_and_click('//*[@id="loginBtn"]', click=True)


wait_and_click('//*[@id="protocolhandler-welcome-installButton"]', click=True)
wait_and_click('//*[@id="protocolhandler-detect-alreadyInstalledLink"]', click=True)

wait_and_click('//*[@id="jpmcAcceptDisclaimerBtn"]', click=True)

wait_and_click('//*[@class="storeapp-name"  and contains(text(),"WorkSpace Enterprise")]',click=True)
wait_and_click('//*[@class="theme-highlight-color appDetails-actions-text" and contains(text(),"Open") ]',click=True)

ica_file = download_wait(download_folder, '*.ica')

cmd_line = '/opt/Citrix/ICAClient/wfica.sh ' + ica_file

subprocess.Popen(cmd_line, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

driver.quit()
print(f'{next(counter)} Opened ica window. Close this terminal')
