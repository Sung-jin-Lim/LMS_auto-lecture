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
    WebDriverWait(driver, 10).until(EC.frame_to_be_available_and_switch_to_it((By.ID, 'tool_content')))
    print("Switched to iframe 'tool_content'")

    # Wait for the lecture elements to be present
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CLASS_NAME, 'xnmb-module_item-wrapper')))

    # Locate the parent elements that contain both the title and the completion status
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

            # Locate the completion status
            completion_status_element = lecture_element.find_element(By.CLASS_NAME, 'xnmb-module_item-completed')
            status_class = completion_status_element.get_attribute('class')

            # Check if the status is "incomplete" or "complete"
            if 'incomplete' in status_class:
                unwatched.append({'title': title, 'link': link})
            else:
                watched.append({'title': title, 'link': link})

        except Exception as e:
            print(f"Error processing lecture: {e}")

    print(f"Watched lectures: {len(watched)}")
    print(f"Unwatched lectures: {len(unwatched)}")

    # Automatically "watch" unwatched lectures
    for lecture in unwatched:
        print(f"Auto-watching lecture: {lecture['title']}")
        driver.get(lecture['link'])

        # Wait for the video player or content to load (adjust wait and selectors as needed)
        try:
            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, 'video')))
            video = driver.find_element(By.TAG_NAME, 'video')

            # Simulate watching the video by waiting for its duration or by fast-forwarding (if applicable)
            driver.execute_script("arguments[0].play();", video)  # Simulate clicking the play button
            time.sleep(5)  # Adjust this to wait for the video duration or the necessary time

            # Optionally, you can also fast-forward or mark the video as complete if it's allowed
            # driver.execute_script("arguments[0].currentTime = arguments[0].duration;", video)  # Fast-forward to the end

            print(f"Finished watching: {lecture['title']}")

        except Exception as e:
            print(f"Error watching lecture: {e}")

    driver.quit()

    # Render the watched/unwatched lectures in the template
    return render_template('lectures.html', watched=watched, unwatched=unwatched)

if __name__ == '__main__':
    app.run(debug=True)
