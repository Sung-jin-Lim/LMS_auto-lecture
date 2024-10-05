# LMS Auto-Lecture Viewer

LMS Auto-Lecture Viewer is a Python Flask application designed to automate the process of watching lectures on a Learning Management System (LMS), specifically tailored for Hanyang University's LMS. This tool automatically logs in, identifies unwatched lectures, and plays them while skipping preloader and intro videos.

## Features

- **Automated Login**: Logs into Hanyang University's LMS with your credentials.
- **Lecture Scraping**: Identifies watched and unwatched lectures in a course.
- **Automatic Video Playback**: Auto-plays unwatched videos and handles common popups (e.g., confirmation buttons).
- **Multi-course Support**: Allows users to input multiple course URLs for batch processing.
- **Skip Preloader and Intro**: Automatically skips short preloader or intro videos and plays the main lecture.

## Easy Use: Precompiled ZIP Files

For ease of use, you can download the precompiled **Windows** or **Mac** zip file from the [Releases](https://github.com/Sung-jin-Lim/LMS_auto-lecture/releases) section, extract it, and run the executable directly:

- **Windows**: Simply run the `app.exe` file inside the extracted folder.
- **Mac**: Run the `app` file from the extracted zip.

No Python or additional installation is required when using the precompiled executables.

---
