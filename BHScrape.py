import os
import time
import requests
import piexif
from datetime import datetime
from PIL import Image  # Pillow is used for the most robust fallback
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium_stealth import stealth
from mutagen.mp4 import MP4

# ==============================================================================
# SCRIPT SETTINGS
# ==============================================================================
DEBUG_MODE = False
FOLDERS = False
# ==============================================================================

# --- Import credentials from a config.py file ---
try:
    from config import USERNAME, PASSWORD, DEPENDENT_NAME
except ImportError:
    print("Error: config.py not found. Please create it with USERNAME, PASSWORD, and DEPENDENT_NAME.")
    exit()


def login_and_navigate_to_photos(username, password, dependent_name):
    # (This function remains unchanged)
    options = webdriver.ChromeOptions()
    options.add_argument("start-maximized")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    try:
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
    except Exception as e:
        print(f"Error initializing WebDriver: {e}")
        return None
    stealth(driver, languages=["en-US", "en"], vendor="Google Inc.", platform="Win32",
            webgl_vendor="Intel Inc.", renderer="Intel Iris OpenGL Engine", fix_hairline=True)
    try:
        driver.get("https://familyinfocenter.brighthorizons.com/")
        print("Successfully navigated to the login page.")
        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='username']"))).send_keys(username)
        driver.find_element(By.CSS_SELECTOR, "input[name='password']").send_keys(password)
        driver.find_element(By.ID, "btnLogin").click()
        print("Logged in. Waiting for dashboard...")
        original_window = driver.current_window_handle
        wait.until(EC.visibility_of_element_located((By.XPATH, f"//h1[text()='{dependent_name}']")))
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, f"//h1[text()='{dependent_name}']/ancestor::section//a[contains(., 'Actions')]"))).click()
        wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[.//span[contains(text(), 'My Bright Day')]]"))).click()
        wait.until(EC.number_of_windows_to_be(2))
        for window_handle in driver.window_handles:
            if window_handle != original_window:
                driver.switch_to.window(window_handle)
                break
        wait.until(EC.url_contains("mybrightday.brighthorizons.com"))
        print(f"Successfully switched to the photos page: {driver.current_url}")
        return driver
    except Exception as e:
        print(f"\nAn error occurred during login/navigation: {e}")
        if 'driver' in locals() and driver:
            driver.save_screenshot("error_screenshot.png")
            driver.quit()
        return None


def add_metadata_to_photo_robust(filepath, file_date_obj, comment):
    """
    Adds metadata to a JPEG with a 3-tiered fallback system.
    1. Tries piexif.insert() (fastest).
    2. Falls back to piexif.transplant() (rebuilds malformed JPEGs).
    3. Falls back to Pillow (handles RGBA conversion and other issues).
    """
    date_taken_str = file_date_obj.strftime("%Y:%m:%d %H:%M:%S")

    exif_dict = {"Exif": {piexif.ExifIFD.DateTimeOriginal: date_taken_str}}
    if comment:
        print(f"    - Preparing comment metadata: '{comment}'")
        exif_dict["Exif"][piexif.ExifIFD.UserComment] = (b'UNICODE\x00' + comment.encode('utf-16-be'))

    exif_bytes = piexif.dump(exif_dict)

    # --- Tier 1: Try the fast 'insert' method ---
    try:
        piexif.insert(exif_bytes, filepath)
        print(f"    - Successfully saved metadata to photo.")
        return
    except Exception as e1:
        print(f"    - Initial metadata insert failed: {e1}. Attempting fallback method 1...")

        # --- Tier 2: Try the 'transplant' method for malformed JPEGs ---
        try:
            temp_filepath = filepath + ".tmp"
            piexif.transplant(filepath, temp_filepath, exif_bytes)
            os.remove(filepath)
            os.rename(temp_filepath, filepath)
            print(f"    - Fallback 1 (transplant) successful. Metadata saved.")
            return
        except Exception as e2:
            print(f"    - Fallback 1 failed: {e2}. Attempting final fallback method 2...")

            # --- Tier 3: Use Pillow for RGBA conversion and ultimate robustness ---
            try:
                img = Image.open(filepath)
                if img.mode == 'RGBA':
                    print("    - Converting RGBA image to RGB...")
                    img = img.convert('RGB')

                img.save(filepath, "jpeg", exif=exif_bytes)
                print(f"    - Fallback 2 (Pillow) successful. Metadata saved.")
            except Exception as e3:
                print(f"    - FINAL FAILED: Could not save metadata. Error: {e3}")


def scrape_all_content(driver):
    # (This function remains unchanged)
    wait = WebDriverWait(driver, 10)
    month_list_container_xpath = "//h2[text()='months']/following-sibling::ul"
    wait.until(EC.visibility_of_element_located((By.XPATH, month_list_container_xpath)))

    num_months = len(driver.find_elements(By.XPATH, f"{month_list_container_xpath}/li"))
    print(f"\nFound {num_months} months to process.")

    month_map = {
        'JAN': 1, 'FEB': 2, 'MAR': 3, 'APR': 4, 'MAY': 5, 'JUN': 6,
        'JUL': 7, 'AUG': 8, 'SEP': 9, 'OCT': 10, 'NOV': 11, 'DEC': 12
    }

    base_directory = "photos"
    os.makedirs(base_directory, exist_ok=True)

    req_session = requests.Session()
    for cookie in driver.get_cookies():
        req_session.cookies.set(cookie['name'], cookie['value'])

    for i in range(num_months):
        month_elements = driver.find_elements(By.XPATH, f"{month_list_container_xpath}/li")

        target_directory = ""
        year = month_elements[i].find_element(By.CSS_SELECTOR, "span[data-bind*='caption']").text

        if FOLDERS:
            month_name_str = month_elements[i].find_element(By.CSS_SELECTOR,
                                                            "span[data-bind*='displayName']").text.upper()
            month_number = month_map.get(month_name_str, 0)
            folder_name = f"{year}-{month_number}-{month_name_str}"
            print(f"\n--- Processing Month: {folder_name} ---")
            target_directory = os.path.join(base_directory, folder_name)
            os.makedirs(target_directory, exist_ok=True)
        else:
            if i == 0:
                print(f"\n--- Processing all months, saving to '{base_directory}' folder ---")
            target_directory = base_directory

        month_elements[i].click()

        spinner_xpath = "//div[contains(@data-bind, 'visible:$root.processing()') and contains(@style, 'display: none;')]"
        try:
            time.sleep(1)
            wait.until(EC.presence_of_element_located((By.XPATH, spinner_xpath)))
        except Exception:
            time.sleep(2)

        scrape_current_month_content(driver, req_session, target_directory, year)

        if DEBUG_MODE:
            print("\nDEBUG MODE is ON. Stopping after the first page.")
            break


def scrape_current_month_content(driver, req_session, target_directory, year):
    # (This function remains unchanged)
    base_url = "https://mybrightday.brighthorizons.com"
    content_tiles_xpath = "//ul[contains(@data-bind, 'tiles: {bricks: $root.selectedEvents()')]/li"

    time.sleep(2)
    content_tiles = driver.find_elements(By.XPATH, content_tiles_xpath)
    print(f"  Found {len(content_tiles)} content items for this month.")

    for tile in content_tiles:
        try:
            date_str = tile.find_element(By.CSS_SELECTOR, "span[data-bind*='tinyDate']").text
            file_date_obj = datetime.strptime(f"{date_str}/{year}", "%m/%d/%Y")
            file_date_sortable = file_date_obj.strftime("%Y-%m-%d")

            comment = ""
            try:
                comment_el = tile.find_element(By.CSS_SELECTOR, "span[data-bind*='text: comment()']")
                comment = comment_el.text.strip()
            except:
                pass

            media_url, is_video = "", False
            try:
                fancybox_link = tile.find_element(By.CSS_SELECTOR, "a.fancybox")
                href = fancybox_link.get_attribute("href")
                if '#' in href:
                    is_video = True
                    video_div = tile.find_element(By.ID, href.split('#')[-1])
                    media_url = video_div.get_attribute("rel")
                else:
                    media_url = href
            except Exception:
                continue

            if not media_url.startswith('http'):
                media_url = base_url + media_url

            file_id = media_url.split('obj=')[1].split('&')[0]
            filename = f"{file_date_sortable}_{file_id}{'.mp4' if is_video else '.jpg'}"
            filepath = os.path.join(target_directory, filename)

            if not os.path.exists(filepath):
                print(f"  - Downloading {'Video' if is_video else 'Photo'}: {filename}")
                response = req_session.get(media_url, stream=True)
                if response.status_code == 200:
                    with open(filepath, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)

                    if is_video:
                        try:
                            video = MP4(filepath)
                            video['\xa9day'] = file_date_obj.strftime("%Y-%m-%dT%H:%M:%SZ")
                            video.save()
                            print(f"    - Saved 'Media Created' date to video.")
                        except Exception as e:
                            print(f"    - Warning: Could not save metadata to video. {e}")
                    else:
                        add_metadata_to_photo_robust(filepath, file_date_obj, comment)
                else:
                    print(f"  - Failed to download {filename}. Status code: {response.status_code}")
            else:
                print(f"  - Skipping {filename}, already exists.")
        except Exception as e:
            print(f"  - An error occurred processing a content tile. Skipping. Error: {e}")


if __name__ == '__main__':
    driver = login_and_navigate_to_photos(USERNAME, PASSWORD, DEPENDENT_NAME)
    if driver:
        try:
            scrape_all_content(driver)
            print("\nScraping process complete.")
        except Exception as e:
            print(f"\nA critical error occurred during scraping: {e}")
            if 'driver' in locals() and driver and driver.service.is_connectable():
                driver.save_screenshot("scraping_error_screenshot.png")
        finally:
            if 'driver' in locals() and driver:
                driver.quit()
            print("Browser closed.")
