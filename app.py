from flask import Flask, render_template, request, redirect, url_for
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By  # <-- Add this import
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
    driver.get('https://learning.hanyang.ac.kr/login')  # Adjust to your login URL if necessary
    driver.find_element(By.ID, 'uid').send_keys(username)
    driver.find_element(By.ID, 'upw').send_keys(password)
    driver.find_element(By.ID, 'login_btn').click()  # Adjust this selector

    # Wait for the login process to complete
    time.sleep(5)

    # Navigate to the specific course's lecture page (class 161529)
    driver.get('https://learning.hanyang.ac.kr/courses/161529/external_tools/140')

    # Now, we will locate the lecture list based on the iframe or tool content
    driver.switch_to.frame(driver.find_element(By.ID, 'tool_content'))

    # Locate the lectures (modify based on actual lecture structure)
    lecture_elements = driver.find_elements(By.CLASS_NAME, 'lecture')  # Adjust the class selector
    watched = []
    unwatched = []

    for lecture in lecture_elements:
        title = lecture.find_element(By.CLASS_NAME, 'title').text
        status = lecture.find_element(By.CLASS_NAME, 'status').text  # Assuming there’s a status class
        
        if 'Watched' in status:
            watched.append(title)
        else:
            unwatched.append(title)

    driver.quit()

    # Render the watched/unwatched lectures in the template
    return render_template('lectures.html', watched=watched, unwatched=unwatched)

if __name__ == '__main__':
    app.run(debug=True)
