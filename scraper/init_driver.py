import tempfile
import platform

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import undetected_chromedriver as uc  #UNDETECTED DRIVER
import platform
import tempfile
from webdriver_manager.chrome import ChromeDriverManager

def init_driver():
    options = uc.ChromeOptions()
    options.headless = True
    #options.headless = False
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")

    options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) " + "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    )

    #block css & images
    prefs = {
        "profile.managed_default_content_settings.images": 2,
        "profile.managed_default_content_settings.stylesheets": 2,
        "profile.managed_default_content_settings.fonts": 2,
    }
    options.add_experimental_option("prefs", prefs)

    if platform.system() == "Windows":
        options.binary_location = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    elif platform.system() == "Linux":
        options.binary_location = "/usr/bin/google-chrome-stable"
        temp_profile = tempfile.mkdtemp(prefix="chrome-userdata-")
        options.add_argument(f"--user-data-dir={temp_profile}")

    #options.add_experimental_option("excludeSwitches", ["enable-automation"])
    #options.add_experimental_option("useAutomationExtension", False)

    driver = uc.Chrome(options=options, use_subprocess=True)
    driver.execute_cdp_cmd(
    "Page.addScriptToEvaluateOnNewDocument",
    {
        "source": """
        Object.defineProperty(navigator, 'webdriver', {
          get: () => undefined
        })
        """
    }
    )
    return driver