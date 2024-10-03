from flask import Flask, render_template, request, redirect, url_for
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait  # <-- Add this import
from selenium.webdriver.support import expected_conditions as EC  # <-- Add this import
import time

app = Flask(__name__)

# Initialize WebDriver (example with Chrome)
def init_driver():
    # Specify the path to the ChromeDriver
    service = Service('/opt/homebrew/bin/chromedriver')  # Path to chromedriver
    driver = webdriver.Chrome(service=service)
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

    # Wait for the lecture elements to be present before interacting with them
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'xnmb-module_item-wrapper')))

    # Locate the lectures after they have loaded
    lecture_elements = driver.find_elements(By.CLASS_NAME, 'xnmb-module_item-wrapper')
    print(f"Number of lecture elements found: {len(lecture_elements)}")

    watched = []
    unwatched = []

    for lecture_element in lecture_elements:
        try:
            # Locate the title and link
            title_element = lecture_element.find_element(By.CLASS_NAME, 'xnmb-module_item-left-title')
            title = title_element.text
            link = title_element.get_attribute('href')
            print(f"Title: {title}, Link: {link}")

            # Locate the completion status
            completion_status = lecture_element.find_element(By.CLASS_NAME, 'xnmb-module_item-completed')
            status_class = completion_status.get_attribute('class')
            print(f"Status class: {status_class}")

            if "incomplete" in status_class:
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
