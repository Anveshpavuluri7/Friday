"""
modules/browser_control.py — Browser control via Selenium + Brave.

Opens URLs in Brave browser using Selenium WebDriver.
Falls back to webbrowser module if Selenium/chromedriver isn't available.
"""

import os
import yaml
import webbrowser
import subprocess


class BrowserControl:
    """Opens URLs in Brave or the default browser."""

    def __init__(self, config_path="config.yaml"):
        """Load browser config."""
        config_file = config_path
        if not os.path.isabs(config_path):
            config_file = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                config_path,
            )

        with open(config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        browser_config = config.get("browser", {})
        self.default_browser = browser_config.get("default", "brave")
        self.brave_exe = browser_config.get(
            "brave_exe",
            r"C:/Program Files/BraveSoftware/Brave-Browser/Application/brave.exe",
        )
        self.chromedriver_path = browser_config.get("chromedriver", "drivers/chromedriver.exe")

        # Make chromedriver path absolute
        if not os.path.isabs(self.chromedriver_path):
            project_root = os.path.dirname(
                os.path.dirname(os.path.abspath(__file__))
            )
            self.chromedriver_path = os.path.join(project_root, self.chromedriver_path)

        # Selenium driver instance (lazy-loaded)
        self._driver = None

        print(f"[Browser] Default: {self.default_browser}")

    def open_url(self, url: str, browser: str = None) -> str:
        """
        Open a URL in the browser.

        Tries Brave directly via subprocess first (fastest + most reliable).
        Falls back to webbrowser module.

        Args:
            url: The URL to open.
            browser: Which browser to use ('brave' or 'default').

        Returns:
            Result message string.
        """
        if not url:
            return "No URL provided."

        browser = (browser or self.default_browser).lower().strip()

        # Try opening directly with Brave executable
        if browser == "brave" and os.path.exists(self.brave_exe):
            try:
                subprocess.Popen(
                    [self.brave_exe, url],
                    shell=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return f"Opened {url} in Brave."
            except Exception as e:
                print(f"[Browser] Brave launch failed: {e}, falling back...")

        # Fallback: use the webbrowser module (opens in default browser)
        try:
            webbrowser.open(url)
            return f"Opened {url} in default browser."
        except Exception as e:
            return f"Failed to open {url}: {e}"

    def open_url_selenium(self, url: str) -> str:
        """
        Open a URL using Selenium WebDriver with Brave.

        This gives more control (tab management, page interaction)
        but requires chromedriver to be set up.

        Args:
            url: The URL to open.

        Returns:
            Result message string.
        """
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.service import Service
            from selenium.webdriver.chrome.options import Options

            if self._driver is None:
                if not os.path.exists(self.chromedriver_path):
                    return f"ChromeDriver not found at {self.chromedriver_path}. Using direct launch."

                options = Options()
                options.binary_location = self.brave_exe

                service = Service(self.chromedriver_path)
                self._driver = webdriver.Chrome(service=service, options=options)

            self._driver.get(url)
            return f"Opened {url} via Selenium in Brave."

        except ImportError:
            return "Selenium not installed. Using direct launch instead."
        except Exception as e:
            # Fall back to direct launch
            print(f"[Browser] Selenium failed: {e}, using direct launch.")
            return self.open_url(url)

    def new_tab(self, url: str) -> str:
        """Open a URL in a new tab (Selenium only)."""
        if self._driver:
            try:
                self._driver.execute_script(f"window.open('{url}', '_blank');")
                return f"Opened {url} in new tab."
            except Exception as e:
                return f"Failed to open new tab: {e}"
        else:
            return self.open_url(url)

    def close(self):
        """Close the Selenium browser if open."""
        if self._driver:
            try:
                self._driver.quit()
                self._driver = None
                return "Browser closed."
            except Exception:
                pass
        return "No browser to close."
