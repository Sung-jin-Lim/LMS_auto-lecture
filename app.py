from flask import Flask, render_template, request, redirect, url_for
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

app = Flask(__name__)

# Initialize WebDriver (example with Chrome)
def init_driver():
    chrome_options = Options()
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    chrome_options.add_argument("start-maximized")
    
    service = Service('/opt/homebrew/bin/chromedriver')
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

@app.route('/')
def index():
    return render_template('index.html')

# Route to handle login and scrape class 161529's lecture data
@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    driver = init_driver()

    # Log into the university's LMS
    driver.get('https://learning.hanyang.ac.kr/login')
    driver.find_element(By.ID, 'uid').send_keys(username)
    driver.find_element(By.ID, 'upw').send_keys(password)
    driver.find_element(By.ID, 'login_btn').click()

    # Wait for the login process to complete
    time.sleep(5)

    # Navigate to the specific course's lecture page (class 161529)
    driver.get('https://learning.hanyang.ac.kr/courses/161529/external_tools/140')

    # Switch to the iframe where the lecture content is loaded
    try:
        WebDriverWait(driver, 10).until(EC.frame_to_be_available_and_switch_to_it((By.ID, 'tool_content')))
        print("Switched to iframe 'tool_content'")
    except Exception as e:
        print(f"Error switching to iframe: {e}")
        driver.quit()
        return "Error: Could not switch to iframe", 500

    # Print the page source to verify if the content is loaded
    print(driver.page_source)

    # Wait for the lecture elements to be present
    try:
        WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.CLASS_NAME, 'xnmb-module_item-left-title')))
    except Exception as e:
        print(f"Timeout waiting for lecture elements: {e}")
        driver.quit()
        return "Error: Timeout while waiting for lecture elements to load", 500

    # Locate the lectures after they have loaded
    lecture_elements = driver.find_elements(By.CLASS_NAME, 'xnmb-module_item-left-title')
    print(f"Number of lecture elements found: {len(lecture_elements)}")

    watched = []
    unwatched = []

    for lecture_element in lecture_elements:
        try:
            title = lecture_element.text
            link = lecture_element.get_attribute('href')
            print(f"Title: {title}, Link: {link}")

            # Locate the completion status (adjust class selector if needed)
            status_element = lecture_element.find_element(By.XPATH, '../..')  # Assuming status is a parent element
            if 'incomplete' in status_element.get_attribute('class'):
                unwatched.append(title)
            else:
                watched.append(title)
        
        except Exception as e:
            print(f"Error processing lecture: {e}")

    print(f"Watched lectures: {len(watched)}")
    print(f"Unwatched lectures: {len(unwatched)}")

    driver.quit()

    # Render the watched/unwatched lectures in the template
    return render_template('lectures.html', watched=watched, unwatched=unwatched)

if __name__ == '__main__':
    app.run(debug=True)
