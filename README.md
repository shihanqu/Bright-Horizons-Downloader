# Bright-Horizons-Downloader
Bright Horizons (Tadpoles) Photo &amp; Video Downloader

A Python script to automatically download all photos and videos for a specific dependent from the Bright Horizons (formerly Tadpoles) parent portal. This script organizes the downloaded media, adds correct "Date Taken" metadata, and embeds any available comments into the photo files.

Features

Automated Login: Uses Selenium and selenium-stealth to log into the portal like a real user.

Full History Download: Iterates through every available month in your child's history to download all content.

Downloads Photos & Videos: Saves both full-resolution images and video files.

Intelligent Organization:

Optionally creates a folder for each month (2025-7-JUL).

Saves files with a sortable YYYY-MM-DD filename convention.

Rich Metadata:

Writes the correct "Date Taken" to photo EXIF data, making them easy to sort in any photo manager.

Writes the correct "Media Created" date to video metadata.

Embeds any teacher-added comments or captions directly into the photo's metadata.

Robust & Resilient:

Includes a three-tiered fallback system to handle and repair non-standard image files that would otherwise fail.

Highly Configurable: Simple flags in the script let you control debug mode and folder organization.

Prerequisites

Before you begin, ensure you have the following installed:

Python 3.8+: You can download it from python.org.

Google Chrome: The script uses Chrome to automate the browser, so it must be installed.

Python Libraries: You will need to install several Python packages. You can install them all with a single command:

Generated bash
pip install selenium webdriver-manager-chrome selenium-stealth requests piexif Pillow mutagen

Installation & Configuration

Clone or Download:

Clone this repository to your local machine using git:

Generated bash
git clone <repository_url>
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
Bash
IGNORE_WHEN_COPYING_END

Or, download the BHScrape.py file directly.

Create the Configuration File:

In the same directory as the script, create a new file named config.py.

Copy and paste the following content into config.py:

Generated python
# -- Bright Horizons Credentials --

# Your username (usually your email address)
USERNAME = "your_email@example.com"

# Your password
PASSWORD = "your_password"

# The first name of the dependent as it appears on the dashboard.
# This must be an EXACT match (case-sensitive).
DEPENDENT_NAME = "DependentFirstName"
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
Python
IGNORE_WHEN_COPYING_END

Update config.py:

Replace the placeholder values in config.py with your actual Bright Horizons login credentials and your child's first name.

Usage

Adjust Script Settings (Optional):

Open the BHScrape.py file in a text editor.

At the top of the file, you can change the settings flags:

Generated python
# ==============================================================================
# SCRIPT SETTINGS
# ==============================================================================

# Set to True to only scrape the first available month (for testing).
# Set to False to scrape all months.
DEBUG_MODE = False

# Set to True to save files in monthly subfolders (e.g., "photos/2025-7-JUL/").
# Set to False to save all files directly into the main "photos" folder.
FOLDERS = True
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
Python
IGNORE_WHEN_COPYING_END

Run the Script:

Open a terminal or command prompt.

Navigate to the directory where you saved the script.

Run the script with the following command:

Generated bash
python BHScrape.py
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
Bash
IGNORE_WHEN_COPYING_END

The script will launch a Chrome browser, log in, and begin downloading all the media. You will see detailed progress in the console.

Output

The script will create a photos folder in the same directory where it is run.

If FOLDERS = True, the structure will be:

Generated code
photos/
├── 2025-7-JUL/
│   ├── 2025-07-28_some_unique_id.jpg
│   └── 2025-07-22_another_id.mp4
├── 2025-6-JUN/
│   └── 2025-06-15_some_other_id.jpg
...
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
IGNORE_WHEN_COPYING_END

If FOLDERS = False, all files will be saved directly inside photos/.

Troubleshooting

Metadata Failures: This script includes a robust, three-stage process to write metadata even to non-standard image files. If you see warnings in the console about metadata failures, the script is automatically trying more powerful methods to fix the files.

StaleElementReferenceException: If the website's structure changes, the script might fail. This script is built to be resilient against this by re-finding elements in each loop, but major changes could require updates to the XPath selectors.

Login Fails: Double-check your USERNAME, PASSWORD, and DEPENDENT_NAME in config.py for typos. Ensure DEPENDENT_NAME is an exact match.

Disclaimer: This script is for personal, educational use only. It is not affiliated with, authorized, or endorsed by Bright Horizons Family Solutions. Please use it responsibly and in accordance with their terms of service.
