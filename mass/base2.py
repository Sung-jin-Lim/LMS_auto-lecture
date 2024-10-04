
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

        try:
            # First, switch to the 'tool_content' iframe
            WebDriverWait(driver, 60).until(EC.frame_to_be_available_and_switch_to_it((By.ID, 'tool_content')))
            print("Switched to 'tool_content' iframe")

            # Switch to the iframe where the play button is located
            WebDriverWait(driver, 60).until(EC.frame_to_be_available_and_switch_to_it((By.CLASS_NAME, 'xnlailvc-commons-frame')))
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

            # Wait for the video element to appear
            video_element = WebDriverWait(driver, 60).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'vc-vplay-video1'))
            )
            print(video_element)

            # Check if the src is the preloader video
            video_src = video_element.get_attribute('src')
            
            print(video_src)
            if '/viewer/uniplayer/preloader.mp4' in video_src:
                print("Preloader video found, switching to the real video...")
                print (video_src)
                

                

                # Switch to the real video inside the 'video-play-video2' container
                video_element = WebDriverWait(driver, 60).until(
                    EC.presence_of_element_located((By.XPATH, "//div[@id='video-play-video2']//video[@class='vc-vplay-video1']"))
                )
                video_src = video_element.get_attribute('src')
                print(f"Real video src: {video_src}")
            else:
                # If not a preloader, check if it's an intro video
                if '/settings/viewer/uniplayer/intro.mp4' in video_src:
                    print("Skipping intro video...")
                    try:
                        confirm_button = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.CLASS_NAME, 'confirm-ok-btn'))
                        )
                        confirm_button.click()
                        print("Clicked confirmation button")
                    except:
                        print("No confirmation pop-up found")
                    
                    # Wait for the actual video after the intro
                    video_element = WebDriverWait(driver, 60).until(
                        EC.presence_of_element_located((By.CLASS_NAME, 'vc-vplay-video1'))
                    )
                    video_src = video_element.get_attribute('src')
                    print(f"Actual video src: {video_src}")
                
            print(f"Video element found for lecture: {lecture['title']}")

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

            # Play the video
            driver.execute_script("arguments[0].play();", video_element)
            print(f"Playing video: {lecture['title']}")

            # Check video progress periodically
            while True:
                current_time = driver.execute_script("return arguments[0].currentTime;", video_element)
                print(f"Current video time: {current_time} / {duration} seconds")

                if current_time >= duration:
                    print(f"Finished watching: {lecture['title']}")
                    break

                time.sleep(10)  # Check every 10 seconds

        except Exception as e:
            # Log page source for debugging if an error occurs
            page_source = driver.page_source
            print(f"Error watching video for lecture: {lecture['title']}, Error: {e}")
            with open('error_page_source.html', 'w') as f:
                f.write(page_source)
            continue

    driver.quit()

    # Render the watched/unwatched lectures in the template
    return render_template('lectures.html', watched=watched, unwatched=unwatched)

if __name__ == '__main__':
    app.run(debug=True)
