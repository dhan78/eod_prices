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

def check_exists_by_xpath(x_path):
    try:
        # driver.find_element(By.XPATH,x_path)
        element = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.XPATH, x_path)))
    except:
        return False
    return True

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

field_of_dentistry_url = 'https://boosterprep.com/inbde/classroom/patient-management?tab=QuestionBanks'
start_practice_xpath='(//*[text()="Prevention of Oral Diseases" and @data-testid="qb-title"]/parent::div)[1]/parent::div/following-sibling::div/a'
study_now_link_xpath = '//a[@data-testid="qb-start-btn-on-preview"]' # Study Now link

response_radio_button_xpath = '(//div[@data-testid="answer-text"])[1]'
check_response_xpath =  '//button[@data-testid="qb-check-button"]'
Player_play_button_xpath =  '//button[@data-play-button="true"]'
Full_screen_btn_xpath= '//*[@id="fullscreen-control-bar-button"]'
Solution_video_coming_soon_xpath = '//strong[contains(text(),"Coming Soon")]'
Leftslider_icon_xpath='//div[contains(@class,"iconWrapper")]'

driver.get(field_of_dentistry_url)
click(start_practice_xpath)
click(study_now_link_xpath)
current_q, total_q = 0,0
# click(Q_i_of_n_xpath)
if check_exists_by_xpath(Leftslider_icon_xpath):    click(Leftslider_icon_xpath)

while current_q <= total_q:
    current_q, total_q = extract_question_number()
    print(f'processing {current_q} of {total_q}')
    click(response_radio_button_xpath)
    click(check_response_xpath)
    if check_exists_by_xpath(iframe_xpath):
        driver.switch_to.frame(WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, iframe_xpath))
        ))

        click(Player_play_button_xpath)
        click(Full_screen_btn_xpath)

        Detect_finish_till_play_button_xpath='//div[contains(@class,"PlayButton_module_playButtonWrapper") and @style="opacity: 1;"]'
        wait_and_click(Detect_finish_till_play_button_xpath,1200)
        click(Full_screen_btn_xpath)
        driver.switch_to.default_content()

    Next_Question_xpath= '//button[@data-testid="qb-next-button"]'
    current_q +=1
    click(Next_Question_xpath)
    time.sleep(2)
