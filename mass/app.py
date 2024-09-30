from flask import Flask, render_template, request, redirect, url_for
from selenium import webdriver
from selenium.webdriver.common.by import By
import time

app = Flask(__name__)

# Initialize WebDriver (Chrome example)
def init_driver():
    # Make sure to specify the path to chromedriver if it's not in your PATH
    driver = webdriver.Chrome(executable_path='/opt/homebrew/bin/chromedriver')
    return driver

@app.route('/')
def index():
    return render_template('index.html')

# Route to handle login and start automation
@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    driver = init_driver()

    # Login to the university site
    driver.get('https://api.hanyang.ac.kr/oauth/login')  # Replace with your university's login URL
    driver.find_element(By.ID, 'uid').send_keys(username)
    driver.find_element(By.ID, 'upw').send_keys(password)
    driver.find_element(By.ID, 'login_btn').click()  # Adjust this to match your site's button ID

    # Wait for the page to load, adjust sleep as necessary
    time.sleep(5)

    # Scrape watched/unwatched lectures (you will need to adapt this to your university's website)
    lectures = driver.find_elements(By.CLASS_NAME, 'lecture')  # Adjust this selector
    watched = []
    unwatched = []

    for lecture in lectures:
        status = lecture.find_element(By.CLASS_NAME, 'status').text
        title = lecture.find_element(By.CLASS_NAME, 'title').text
        if 'Watched' in status:
            watched.append(title)
        else:
            unwatched.append(title)

    driver.quit()

    return render_template('lectures.html', watched=watched, unwatched=unwatched)

@app.route('/watch', methods=['POST'])
def watch_lecture():
    lecture_title = request.form['lecture_title']
    driver = init_driver()

    # Navigate to the lecture page (you'll need to adjust this URL and logic based on your website)
    driver.get(f'https://universitywebsite.com/lectures/{lecture_title}')  # Adjust this
    play_button = driver.find_element(By.ID, 'play_button')  # Adjust this selector
    play_button.click()

    # Simulate watching the video by waiting (adjust time based on the video length)
    time.sleep(60)  # Simulate watching for 60 seconds (adjust as needed)

    driver.quit()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
