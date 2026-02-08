"""Step 6: Switch Migaku extension language via Selenium."""

import glob
import os
import shutil
import sys
import tempfile
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from lib.config import (
    AVAILABLE_LANGUAGES,
    CHROME_PROFILE,
    CHROME_USER_DATA,
    MIGAKU_EXTENSION_ID,
)


class LanguageSwitchError(Exception):
    """Raised when the Selenium language switch fails."""


def _get_extension_path() -> str:
    ext_base = os.path.join(CHROME_USER_DATA, CHROME_PROFILE, "Extensions", MIGAKU_EXTENSION_ID)
    versions = glob.glob(os.path.join(ext_base, "*"))
    if not versions:
        raise FileNotFoundError(f"Migaku extension not found at {ext_base}")
    return sorted(versions)[-1]


def _copy_profile_data(temp_dir: str) -> str:
    source_profile = os.path.join(CHROME_USER_DATA, CHROME_PROFILE)
    dest_profile = os.path.join(temp_dir, "Profile")
    os.makedirs(dest_profile, exist_ok=True)

    for dir_name in ["Extensions", "Local Extension Settings", "Sync Extension Settings",
                     "IndexedDB", "Local Storage", "Extension State"]:
        src = os.path.join(source_profile, dir_name)
        dst = os.path.join(dest_profile, dir_name)
        if os.path.exists(src):
            shutil.copytree(src, dst, dirs_exist_ok=True)

    for file_name in ["Preferences", "Secure Preferences"]:
        src = os.path.join(source_profile, file_name)
        dst = os.path.join(dest_profile, file_name)
        if os.path.exists(src):
            shutil.copy2(src, dst)

    return dest_profile


def run(language: str = "German") -> None:
    """Switch Migaku to the given language. Raises LanguageSwitchError on failure."""
    if language not in AVAILABLE_LANGUAGES:
        raise LanguageSwitchError(
            f"'{language}' is not available. Choose from: {', '.join(AVAILABLE_LANGUAGES)}"
        )

    ext_path = _get_extension_path()
    temp_dir = tempfile.mkdtemp(prefix="migaku_")
    driver = None

    try:
        print("Setting up...")
        _copy_profile_data(temp_dir)

        options = Options()
        options.add_argument(f"--user-data-dir={temp_dir}")
        options.add_argument("--profile-directory=Profile")
        options.add_argument(f"--load-extension={ext_path}")
        options.add_argument("--no-first-run")
        options.add_argument("--no-default-browser-check")
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")

        driver = webdriver.Chrome(options=options)
        wait = WebDriverWait(driver, 15)

        app_url = f"chrome-extension://{MIGAKU_EXTENSION_ID}/pages/app-window/index.html"
        driver.get(app_url)
        time.sleep(3)

        lang_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".LangSelectButton")))
        lang_btn.click()
        time.sleep(2)

        print(f"Switching to {language}...")
        lang_option = wait.until(
            EC.element_to_be_clickable((By.XPATH, f"//button[.//p[text()='{language}']]"))
        )
        lang_option.click()
        time.sleep(5)

        print(f"Switched to {language}")

    except Exception as e:
        raise LanguageSwitchError(str(e)) from e

    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "German"
    run(target)
