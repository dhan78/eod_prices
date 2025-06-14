"""
JPMorgan Workspace Login Automation Module.
Handles automated login and ICA client launch for JPM Workspace.
"""

import os
import sys
import time
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


@dataclass
class WorkspaceConfig:
    """Configuration settings for JPM workspace."""
    username: str = ""
    password: str = ""
    url: str = "http://myworkspace.jpmchase.com"
    download_dir: Path = Path.home() / "Downloads"
    ica_path: Path = Path("/opt/Citrix/ICAClient/wfica.sh")

    def __post_init__(self):
        """Initialize after dataclass creation, source env vars if needed."""
        self.username = os.getenv("JPM_USER", "")
        self.password = os.getenv("JPM_PASSWORD", "")
        
        if not self.username or not self.password:
            self._source_bashrc()

    def _source_bashrc(self) -> None:
        """Source credentials from .bashrc file."""
        bashrc_path = Path.home() / ".bashrc"
        if not bashrc_path.exists():
            return

        try:
            with open(bashrc_path, 'r') as f:
                bashrc_content = f.read()
            
            # Parse JPM credentials from bashrc
            for line in bashrc_content.splitlines():
                if line.startswith("export JPM_USER="):
                    self.username = line.split("=")[1].strip('"\'')
                elif line.startswith("export JPM_PASSWORD="):
                    self.password = line.split("=")[1].strip('"\'')

        except Exception as e:
            print(f"Error reading .bashrc: {e}")

    def validate(self) -> None:
        """Validate configuration settings."""
        if not self.username or not self.password:
            raise ValueError("JPM_USER and JPM_PASSWORD not found in environment or .bashrc")
        if not self.ica_path.exists():
            raise FileNotFoundError(f"ICA client not found at {self.ica_path}")


class WorkspaceAutomation:
    """Handles JPMorgan Workspace automation."""

    XPATHS = {
        "login": '//*[@id="login"]',
        "password1": '(//input[@type="password"])[1]',
        "password2": '(//input[@type="password"])[2]',
        "submit": '//*[@id="loginBtn"]',
        "install": '//*[@id="protocolhandler-welcome-installButton"]',
        "detect": '//*[@id="protocolhandler-detect-alreadyInstalledLink"]',
        "disclaimer": '//*[@id="jpmcAcceptDisclaimerBtn"]',
        "workspace": '//*[@class="storeapp-name" and contains(text(),"CDC2")]',
        "open": '//*[@class="theme-highlight-color appDetails-actions-text" and contains(text(),"Open")]',
    }

    def __init__(self, config: WorkspaceConfig, passcode: str):
        """Initialize automation with configuration and passcode."""
        self.config = config
        self.passcode = passcode
        self.driver: Optional[webdriver.Firefox] = None
        self.config.validate()

    def _print(self, message: str) -> None:
        """Print status message with timestamp."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}")

    def _wait_for_element(self, xpath: str, timeout: int = 20) -> WebElement:
        """Wait for element and return when clickable."""
        return WebDriverWait(self.driver, timeout).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        )

    def _clean_ica_files(self) -> None:
        """Remove existing ICA files from download directory."""
        for ica_file in self.config.download_dir.glob("*.ica"):
            ica_file.unlink()
            self._print(f"Removed ICA file: {ica_file}")

    def _wait_for_download(self) -> Path:
        """Wait for and return new ICA file."""
        self._print("Waiting for ICA file download...")
        while True:
            ica_files = list(self.config.download_dir.glob("*.ica"))
            if ica_files:
                self._print(f"Found ICA file: {ica_files[0]}")
                return ica_files[0]
            time.sleep(1)

    def _setup_driver(self) -> None:
        """Initialize Firefox webdriver."""
        self._print("Initializing Firefox webdriver...")
        options = Options()
        self.driver = webdriver.Firefox(options=options)
        self.driver.get(self.config.url)
        self._print("Browser opened and navigated to workspace URL")

    def _login(self) -> None:
        """Execute login sequence."""
        self._print("Starting login sequence...")
        self._wait_for_element(self.XPATHS["login"]).send_keys(self.config.username)
        self._wait_for_element(self.XPATHS["password1"]).send_keys(self.config.password)
        self._wait_for_element(self.XPATHS["password2"]).send_keys(self.passcode)
        self._wait_for_element(self.XPATHS["submit"]).click()
        self._print("Login completed")

    def _setup_and_launch(self) -> None:
        """Configure protocol handlers and launch workspace application."""
        self._print("Setting up handlers and launching workspace...")
        
        # Configure protocol handlers
        handlers = ["install", "detect", "disclaimer"]
        for action in handlers:
            self._wait_for_element(self.XPATHS[action]).click()
        
        # Launch workspace
        self._wait_for_element(self.XPATHS["workspace"]).click()
        self._wait_for_element(self.XPATHS["open"]).click()
        self._print("Workspace setup and launch completed")

    def _start_ica_client(self, ica_file: Path) -> None:
        """Launch ICA client with downloaded file."""
        self._print(f"Starting ICA client with file: {ica_file}")
        subprocess.Popen(
            [str(self.config.ica_path), str(ica_file)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def run(self) -> None:
        """Execute complete automation sequence."""
        self._print("Starting workspace automation...")
        try:
            self._clean_ica_files()
            self._setup_driver()
            self._login()
            self._setup_and_launch()  # Using the combined method
            ica_file = self._wait_for_download()
            self._start_ica_client(ica_file)
            self._print("Workspace automation completed successfully")
        except Exception as e:
            self._print(f"Error during automation: {e}")
            raise
        finally:
            if self.driver:
                self.driver.quit()
                self._print("Browser closed")


def main() -> None:
    """Script entry point."""
    if len(sys.argv) != 2:
        print("Usage: python jpm_login.py <passcode>")
        sys.exit(1)

    try:
        config = WorkspaceConfig()
        automation = WorkspaceAutomation(config, sys.argv[1])
        automation.run()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()