from flask import Flask, render_template, request, redirect, url_for, jsonify, make_response
from selenium import webdriver
from selenium.webdriver.chrome.service import Service

from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import time
import os
import webbrowser
import threading
from webdriver_manager.chrome import ChromeDriverManager

app = Flask(__name__,
            template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
            static_folder=os.path.join(os.path.dirname(__file__), 'static'))

# Global variables with a lock for thread safety
progress_status_lock = threading.Lock()
progress_status = {
    'current_task': 'Starting...',
    'progress': 0,
    'is_complete': False  # Added is_complete flag
}

# Add a threading.Event to signal the automation to stop
automation_stop_event = threading.Event()

# Initialize WebDriver (example with Chrome)
def init_driver():
    chrome_options = Options()
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    chrome_options.add_argument("start-maximized")
    # Add headless mode if desired
    # chrome_options.add_argument("--headless")
    # Set window size to avoid issues in headless mode
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("start-maximized")
    # Use ChromeDriverManager to auto-manage chromedriver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/completion', methods = ['GET', 'POST'])
def completion():
    return render_template('completion.html')

@app.route('/restart', methods=['POST'])
def restart():
    global progress_status
    with progress_status_lock:
        progress_status['current_task'] = 'Starting...'
        progress_status['progress'] = 0
        progress_status['is_complete'] = False  # Reset the flag
    # Redirect to the main page
    return redirect(url_for('index'))


@app.route('/start_watching', methods=['GET', 'POST'])
def start_watching():
    # Assuming user login and setup is done, start watching videos
    return render_template('progress.html')

@app.route('/login', methods=['POST'])
def login():
    global progress_status, automation_stop_event
    username = request.form['username']
    password = request.form['password']
    course_urls = request.form.getlist('course_urls[]')
    # Filter out empty URLs
    course_urls = [url for url in course_urls if url.strip()]
    if not course_urls:
        return "No course URLs provided.", 400

    # Reset the automation stop event
    automation_stop_event.clear()

    # Start the Selenium automation in a background thread
    threading.Thread(target=run_selenium_automation, args=(username, password, course_urls)).start()

    # Redirect to the progress page
    return redirect(url_for('start_watching'))

@app.route('/cancel', methods=['POST'])
def cancel():
    global automation_stop_event
    # Set the event to signal the automation thread to stop
    automation_stop_event.set()
    # Optionally reset progress_status
    with progress_status_lock:
        progress_status['current_task'] = 'Automation canceled'
        progress_status['progress'] = 0
    return ('', 204)  # Return an empty response with HTTP status 204 (No Content)

@app.route('/progress')
def get_progress():
    global progress_status
    with progress_status_lock:
        current_status = progress_status.copy()
    return jsonify(current_status)


def run_selenium_automation(username, password, course_urls):
    global progress_status
    driver = init_driver()
    
    # Check for cancellation before starting
    if automation_stop_event.is_set():
        driver.quit()
        return

    with progress_status_lock:
        progress_status['current_task'] = 'Logging into the LMS'
        progress_status['progress'] = 5

    driver.get('https://learning.hanyang.ac.kr/login')
    driver.find_element(By.ID, 'uid').send_keys(username)
    driver.find_element(By.ID, 'upw').send_keys(password)
    driver.find_element(By.ID, 'login_btn').click()

    # Wait for the login process to complete
    time.sleep(5)

    # Check for cancellation
    if automation_stop_event.is_set():
        driver.quit()
        return

    with progress_status_lock:
        progress_status['current_task'] = 'Logged in successfully'
        progress_status['progress'] = 10

    total_courses = len(course_urls)
    course_counter = 0

    for course_url in course_urls:
        # Check for cancellation
        if automation_stop_event.is_set():
            driver.quit()
            return

        course_counter += 1
        with progress_status_lock:
            progress_status['current_task'] = f'Processing course {course_counter}/{total_courses}'
            # Update progress (10% to 90% allocated to courses)
            progress_status['progress'] = 10 + int((course_counter - 1) * 80 / total_courses)

        # Ensure the course URL is properly formatted
        course_url = course_url.strip().rstrip('/')

        # Navigate to the specific course's lecture page
        lecture_page_url = course_url + '/external_tools/140'
        driver.get(lecture_page_url)

        # Process the course lectures
        process_course_lectures(driver, course_counter, total_courses)

    # Check for cancellation before finishing
    if automation_stop_event.is_set():
        driver.quit()
        return

    with progress_status_lock:
        progress_status['current_task'] = 'All courses processed'
        progress_status['progress'] = 100
        progress_status['is_complete'] = True  # Set completion flag

    driver.quit()

def process_course_lectures(driver, course_number, total_courses):
    global progress_status

    # Check for cancellation
    if automation_stop_event.is_set():
        return

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
        # Check for cancellation
        if automation_stop_event.is_set():
            return

        try:
            # First, check if the lecture has the mp4 icon
            try:
                lecture_element.find_element(By.CLASS_NAME, 'xnmb-module_item-icon.mp4')
            except:
                print("No MP4 icon found, skipping this item...")
                continue  # Skip if the lecture does not have the MP4 icon

            # Check if the lecture is marked as 'absent' (due date has passed)
            try:
                lecture_element.find_element(By.CLASS_NAME, 'xnmb-module_item-meta_data-attendance_status.absent')
                print("Lecture has passed its due date, skipping...")
                continue  # Skip if the lecture's due date has passed
            except:
                pass  # No absent status found, continue with the lecture processing

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

    # Check if there are no unwatched lectures
    if len(unwatched) == 0:
        print("All lectures have been watched for this course.")
        with progress_status_lock:
            progress_status['current_task'] = 'All courses processed'
            progress_status['progress'] = 100
            progress_status['is_complete'] = True  # Set completion flag
        driver.quit()
        return


    # Automatically "watch" unwatched lectures
    lecture_counter = 0
    total_lectures = len(unwatched)
    for lecture in unwatched:
        # Check for cancellation
        if automation_stop_event.is_set():
            return

        lecture_counter += 1
        with progress_status_lock:
            progress_status['current_task'] = f"Auto-watching lecture {lecture_counter}/{total_lectures} in course {course_number}"
            # Update progress within the course (distribute remaining progress for the course)
            course_progress = 10 + int((course_number - 1) * 80 / total_courses)
            lecture_progress = int(80 / total_courses * lecture_counter / total_lectures)
            progress_status['progress'] = course_progress + lecture_progress

        print(f"Auto-watching lecture: {lecture['title']}")
        driver.get(lecture['link'])

        # Check for cancellation
        if automation_stop_event.is_set():
            return

        try:
            # First, switch to the 'tool_content' iframe
            WebDriverWait(driver, 60).until(EC.frame_to_be_available_and_switch_to_it((By.ID, 'tool_content')))
            print("Switched to 'tool_content' iframe")

            # Switch to the iframe where the play button is located
            WebDriverWait(driver, 7).until(EC.frame_to_be_available_and_switch_to_it((By.CLASS_NAME, 'xnlailvc-commons-frame')))
            print("Switched to video iframe")

            # Wait for the play button to appear and click it
            play_button = WebDriverWait(driver, 60).until(
                EC.element_to_be_clickable((By.CLASS_NAME, 'vc-front-screen-play-btn'))
            )
            play_button.click()
            print("Clicked the play button")

            # Check for confirmation pop-up and click "OK" if it appears
            try:
                confirm_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CLASS_NAME, 'confirm-ok-btn'))
                )
                confirm_button.click()
                print("Clicked confirmation button")
            except:
                print("No confirmation pop-up found")

            # Wait for the video elements to appear
            video_element = WebDriverWait(driver, 60).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'vc-vplay-video1'))
            )

            # Check if the src is the intro video
            video_src = video_element.get_attribute('src')
            if '/settings/viewer/uniplayer/intro.mp4' in video_src:
                print("Skipping intro video...")

                # Check for confirmation pop-up and click "OK" if it appears
                try:
                    confirm_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CLASS_NAME, 'confirm-ok-btn'))
                    )
                    confirm_button.click()
                    print("Clicked confirmation button")
                except:
                    print("No confirmation pop-up found")
                # Now wait for the actual video to appear after the intro
                video_element = WebDriverWait(driver, 60).until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'vc-vplay-video1'))
                )
                video_src = video_element.get_attribute('src')
                print(f"Actual video src: {video_src}")

            duration = driver.execute_script("return arguments[0].duration;", video_element)
            print(duration)  # Prints preloader duration

            # Check for confirmation pop-up and click "OK" if it appears
            try:
                confirm_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CLASS_NAME, 'confirm-ok-btn'))
                )
                confirm_button.click()
                print("Clicked confirmation button")
            except:
                print("No confirmation pop-up found")

            # Get video duration using JavaScript
            duration = driver.execute_script("return arguments[0].duration;", video_element)
            print(f"Video duration: {duration} seconds for lecture: {lecture['title']}")

            if duration < 2:
                print("Preloader video found, switching to the real video...")
                print(video_src)
                # Switch to the real video inside the 'video-play-video2' container
                video_element = WebDriverWait(driver, 60).until(
                    EC.presence_of_element_located((By.XPATH, "//div[@id='video-play-video2']//video[@class='vc-vplay-video1']"))
                )
                video_src = video_element.get_attribute('src')
                print(f"Real video src: {video_src}")

            # Play the second video
            driver.execute_script("arguments[0].play();", video_element)
            print(f"Playing video: {lecture['title']}")

            # Check video progress periodically
            while True:
                # Check for cancellation
                if automation_stop_event.is_set():
                    return

                current_time = driver.execute_script("return arguments[0].currentTime;", video_element)
                print(f"Current video time: {current_time} / {duration} seconds")

                if current_time >= duration:
                    print(f"Finished watching: {lecture['title']}")
                    break

                time.sleep(10)  # Check every 10 seconds

                # Check for cancellation after sleep
                if automation_stop_event.is_set():
                    return

        except Exception as e:
            # Log page source for debugging if an error occurs
            page_source = driver.page_source
            print(f"Error watching video for lecture: {lecture['title']}, Error: {e}")
            with open('error_page_source.html', 'w') as f:
                f.write(page_source)
            continue

    print("Finished processing lectures for this course.")

    # Switch back to the default content
    driver.switch_to.default_content()

def open_browser():
    time.sleep(1)  # Wait for Flask to start
    webbrowser.open("http://127.0.0.1:5003")

if __name__ == '__main__':
    threading.Thread(target=open_browser).start()
    app.run(debug=False, port=5003)
