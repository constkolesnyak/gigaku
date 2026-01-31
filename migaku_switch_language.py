#!/usr/bin/env python3
"""
Migaku Extension Language Switcher

Automates switching the learning language in the Migaku Chrome extension.
Uses Selenium with a copy of your Chrome profile so you don't need to close Chrome.

Usage:
    python migaku_switch_language.py [language]

Examples:
    python migaku_switch_language.py Japanese
    python migaku_switch_language.py German
    python migaku_switch_language.py  # defaults to Japanese

Available languages:
    Cantonese, English, French, German, Italian, Japanese,
    Korean, Mandarin, Portuguese, Spanish, Vietnamese
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import shutil
import tempfile
import glob
import time
import sys

# Configuration
MIGAKU_EXTENSION_ID = "dmeppfcidcpcocleneopiblmpnbokhep"
DEFAULT_TARGET_LANGUAGE = "Japanese"

# Chrome paths - adjust if using a different profile
CHROME_USER_DATA = os.path.expanduser("~/Library/Application Support/Google/Chrome")
CHROME_PROFILE = "Profile 1"

AVAILABLE_LANGUAGES = [
    "Cantonese", "English", "French", "German", "Italian",
    "Japanese", "Korean", "Mandarin", "Portuguese", "Spanish", "Vietnamese"
]


def get_extension_path() -> str:
    ext_base = os.path.join(CHROME_USER_DATA, CHROME_PROFILE, "Extensions", MIGAKU_EXTENSION_ID)
    versions = glob.glob(os.path.join(ext_base, "*"))
    if not versions:
        raise FileNotFoundError(f"Migaku extension not found at {ext_base}")
    return sorted(versions)[-1]


def copy_profile_data(temp_dir: str) -> str:
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


def switch_language(target_language: str = DEFAULT_TARGET_LANGUAGE):
    if target_language not in AVAILABLE_LANGUAGES:
        print(f"Error: '{target_language}' is not available.")
        print(f"Choose from: {', '.join(AVAILABLE_LANGUAGES)}")
        return False

    ext_path = get_extension_path()
    temp_dir = tempfile.mkdtemp(prefix="migaku_")
    driver = None

    try:
        print("Setting up...")
        copy_profile_data(temp_dir)

        options = Options()
        options.add_argument(f"--user-data-dir={temp_dir}")
        options.add_argument("--profile-directory=Profile")
        options.add_argument(f"--load-extension={ext_path}")
        options.add_argument("--no-first-run")
        options.add_argument("--no-default-browser-check")
        options.add_argument("--headless=new")

        driver = webdriver.Chrome(options=options)
        wait = WebDriverWait(driver, 15)

        # Open extension window
        app_url = f"chrome-extension://{MIGAKU_EXTENSION_ID}/pages/app-window/index.html"
        driver.get(app_url)
        time.sleep(3)

        # Click language selector
        lang_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".LangSelectButton")))
        lang_btn.click()
        time.sleep(2)

        # Select language
        print(f"Switching to {target_language}...")
        lang_option = wait.until(
            EC.element_to_be_clickable((By.XPATH, f"//button[.//p[text()='{target_language}']]"))
        )
        lang_option.click()
        time.sleep(5)

        print(f"✓ Switched to {target_language}")
        return True

    except Exception as e:
        print(f"Error: {e}")
        return False

    finally:
        if driver:
            driver.quit()
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_TARGET_LANGUAGE
    switch_language(target)
