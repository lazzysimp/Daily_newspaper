import time
import requests
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

def get_google_drive_link():
    # Set up Chrome options for debugging (no headless mode for now)
    options = Options()
    # Disable headless mode for debugging purposes
    # options.add_argument("--headless")  # Run in headless mode (no GUI)
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")  # Add this to improve stability in headless mode
    options.add_argument("--remote-debugging-port=9222")  # Allow debugging
    
    # Set up the webdriver with more detailed logs
    service = Service(ChromeDriverManager().install())
    service.start()

    driver = webdriver.Chrome(service=service, options=options)

    try:
        # Open the target webpage
        url = "https://epaperwave.com/hindustan-times-epaper-pdf-today/#google_vignette"
        driver.get(url)

        # Wait for the page to load and ensure the Google Drive link is available
        wait = WebDriverWait(driver, 60)  # Wait up to 60 seconds for the element to be found

        # Ensure the link is visible and clickable
        drive_link_element = wait.until(EC.visibility_of_element_located(
            (By.XPATH, "//a[contains(@href, 'https://drive.google.com/file/d/')]")))

        # Scroll to the element to make sure it's in the viewport
        driver.execute_script("arguments[0].scrollIntoView();", drive_link_element)

        # Wait for the element to be clickable before extracting the link
        wait.until(EC.element_to_be_clickable(drive_link_element))

        # Get the link from the element
        drive_link = drive_link_element.get_attribute("href")

        # Extract file ID from the Google Drive link
        file_id = drive_link.split('/d/')[1].split('/')[0]

        # Return the direct download link format
        logging.info(f"Found Google Drive link: {drive_link}")
        return f"https://drive.google.com/uc?export=download&id={file_id}"

    except Exception as e:
        logging.error(f"Error getting Google Drive link: {e}")
        return None
    finally:
        driver.quit()


def download_pdf(pdf_url, destination_folder):
    try:
        # Prepare the filename (using the last part of the URL as the filename)
        file_name = pdf_url.split('id=')[-1] + '.pdf'  # Extract the file ID from the Google Drive URL
        file_path = os.path.join(destination_folder, file_name)

        # Send a GET request to download the PDF
        response = requests.get(pdf_url, stream=True)

        # Handle large file confirmation page (Google Drive "Confirm Download" page)
        if 'Confirm' in response.text:
            logging.info("Download requires confirmation. Handling confirmation...")
            # Handle confirmation if needed (typically when the file is large)
            confirm_url = response.url
            response = requests.get(confirm_url, stream=True)

        if response.status_code == 200:
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
            logging.info(f"PDF downloaded successfully: {file_path}")
        else:
            logging.error(f"Failed to download PDF. Status code: {response.status_code}")

    except Exception as e:
        logging.error(f"Error downloading PDF: {e}")


def monitor_and_download(destination_folder):
    last_downloaded_url = None  # Keep track of the last downloaded PDF URL

    while True:
        # Get the current Google Drive link
        current_url = get_google_drive_link()

        if current_url:
            # If the link has changed (i.e., new PDF uploaded)
            if current_url != last_downloaded_url:
                logging.info(f"New PDF found: {current_url}")
                download_pdf(current_url, destination_folder)
                last_downloaded_url = current_url  # Update the last downloaded URL
            else:
                logging.info("No new PDF uploaded.")

        # Wait for a certain period before checking again (e.g., 5 minutes)
        time.sleep(300)  # Check every 5 minutes


# Specify the folder where the PDF files should be saved
destination_folder = "./downloaded_pdfs"  # Change this to your desired path
if not os.path.exists(destination_folder):
    os.makedirs(destination_folder)

# Run the monitoring function to start downloading PDFs when uploaded
monitor_and_download(destination_folder)