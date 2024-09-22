import random

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
from selenium import webdriver
from dotenv import load_dotenv
load_dotenv()

inbde_url= "https://boosterprep.com/sign-in"
login_xpath =  '//input[@id="email"]'
pass_xpath =  '//input[@id="password"]'
login_button_xpath='//button[@type="submit"]'
import re
Q_i_of_n_xpath = '//h3[@data-testid="qb-title"]'
def extract_question_number():
    # Define the regular expression pattern

    obj = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, Q_i_of_n_xpath)))
    pattern = r'Question (\d+) of (\d+)'

    # Search for the pattern in the text
    match = re.search(pattern, obj.text)

    if match:
        # Extract the question number and the total number of questions
        question_number = int(match.group(1))
        total_questions = int(match.group(2))
        return question_number, total_questions
    else:
        return None
def wait_for_element(x_path):
    obj = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, x_path)))
    return True
def enter_keys(x_path,p_keys):
    obj = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, x_path)))
    obj.send_keys(p_keys)

def click(x_path, **kwargs):
    obj = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, x_path)))
    obj.click()
def wait_and_click(x_path,delay):
    obj = WebDriverWait(driver, delay).until(EC.element_to_be_clickable((By.XPATH, x_path)))
    obj.click()

def check_exists_by_xpath(x_path,p_delay=3):
    try:
        # driver.find_element(By.XPATH,x_path)
        element = WebDriverWait(driver, p_delay).until(EC.presence_of_element_located((By.XPATH, x_path)))
    except:
        return False
    return True

def check_visibility_by_xpath(x_path,p_delay=3):
    try:
        # driver.find_element(By.XPATH,x_path)
        element = WebDriverWait(driver, p_delay).until(EC.visibility_of_element_located((By.XPATH, x_path)))
    except:
        return False
    return True

def get_played_percentage(p_style_str):
    number = re.findall(r"\d+\.\d+|\d+", p_style_str)
    # Since findall returns a list, get the first element if the list is not empty
    if number:
        extracted_number = number[0]
        return float(extracted_number)
    else:
        raise

def open_firefox_flatpak():
    # Set up Firefox options
    options = Options()
    #options.binary_location = firefox_binary_path

    # Create a Firefox webdriver with the specified options
    browser = webdriver.Firefox(options=options)
    browser.get(inbde_url)

    return browser

driver = open_firefox_flatpak()
enter_keys(login_xpath,'jaya.umd@gmail.com')
enter_keys(pass_xpath,'Simba-2024')
time.sleep(4.5)
# click(login_button_xpath)
iframe_xpath='//iframe[contains(@src,"vimeo")]'
# iframe =
# driver.switch_to.frame(iframe)

field_of_dentistry_url = 'https://boosterprep.com/inbde/classroom/fields-of-dentistry?tab=VideoContent&item-id=8fa5240a-72b3-43b6-8244-79537a4fba0c'

response_radio_button_xpath = '(//div[@data-testid="answer-text"])[1]'
check_response_xpath =  '//button[@data-testid="qb-check-button"]'
Player_play_button_xpath =  '//button[@data-play-button="true"]'
Full_screen_btn_xpath= '//*[@id="fullscreen-control-bar-button"]'
Solution_video_coming_soon_xpath = '//strong[contains(text(),"Coming Soon")]'
Leftslider_icon_xpath='//div[contains(@class,"iconWrapper")]'
next_button_xpath = '//div[@class="mui-style-tuci2j"]/div[2]/button'
video_preview_xpath='(//li[@class="mui-style-sh3y94"])[1]/a'

driver.get(field_of_dentistry_url)
click(video_preview_xpath)
click(Leftslider_icon_xpath)
from selenium.webdriver.common.action_chains import ActionChains
ac=ActionChains(driver)

next_video_exists = True
while next_video_exists:

    if check_exists_by_xpath(iframe_xpath):
        driver.switch_to.frame(WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, iframe_xpath))
        ))

    click(Full_screen_btn_xpath)
    # click(Player_play_button_xpath)
    elem_play_icon = driver.find_element(By.XPATH,Player_play_button_xpath)
    ac.move_to_element(elem_play_icon).move_by_offset(39,-20).click().perform()
    ac.move_to_element(elem_play_icon).pause(2).move_by_offset(39,-20).click().perform()
    time.sleep(10)
    slider=driver.find_element(By.XPATH,'//div[@data-progress-bar-played="true"]')
    slider_percentage=0.
    while(slider_percentage<99.99):
        slider_str=driver.find_element(By.XPATH,'//div[@data-progress-bar-played="true"]').get_attribute('style')
        slider_percentage=get_played_percentage(slider_str)
        time.sleep(3)
        print(slider_percentage)
    Exit_full_screen_xpath='//button[@id="fullscreen-control-bar-button"]'
    wait_and_click(Exit_full_screen_xpath,3)
    # click(Full_screen_btn_xpath)
    driver.switch_to.default_content()

    next_video_exists = check_exists_by_xpath(Leftslider_icon_xpath)

    # next_button_xpath = '//div[@class="mui-style-tuci2j"]/div[2]/button'

    time.sleep(2)
    click(next_button_xpath)
