"""
JPMorgan Workspace Login Automation Module.
Handles automated login and ICA client launch for JPM Workspace.
"""

import os
import subprocess
import sys
import time
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
    username: str = os.getenv("JPM_USER", "")
    password: str = os.getenv("JPM_PASSWORD", "")
    url: str = "http://myworkspace.jpmchase.com"
    download_dir: Path = Path.home() / "Downloads"
    ica_path: Path = Path("/opt/Citrix/ICAClient/wfica.sh")

    def validate(self) -> None:
        """Validate configuration settings."""
        if not self.username or not self.password:
            raise ValueError("JPM_USER and JPM_PASSWORD environment variables required")
        if not self.ica_path.exists():
            raise FileNotFoundError(f"ICA client not found at {self.ica_path}")


class WorkspaceAutomation:
    """Automates JPMorgan Workspace login and ICA client launch."""

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

    def _log(self, message: str) -> None:
        """Print status message with timestamp."""
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}")

    def _wait_for_element(self, xpath: str, timeout: int = 20) -> WebElement:
        """Wait for element and return when clickable."""
        return WebDriverWait(self.driver, timeout).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        )

    def _clean_ica_files(self) -> None:
        """Remove existing ICA files from download directory."""
        for ica_file in self.config.download_dir.glob("*.ica"):
            ica_file.unlink(missing_ok=True)
            self._log(f"Removed ICA file: {ica_file}")

    def _wait_for_download(self, timeout: int = 60) -> Path:
        """Wait for and return new ICA file, with timeout."""
        self._log("Waiting for ICA file download...")
        start = time.time()
        while time.time() - start < timeout:
            ica_file = next((f for f in self.config.download_dir.glob("*.ica")), None)
            if ica_file:
                self._log(f"Found ICA file: {ica_file}")
                return ica_file
            time.sleep(1)
        raise TimeoutError("Timed out waiting for ICA file download.")

    def _login(self) -> None:
        """Execute login sequence."""
        self._log("Starting login sequence...")
        self._wait_for_element(self.XPATHS["login"]).send_keys(self.config.username)
        self._wait_for_element(self.XPATHS["password1"]).send_keys(self.config.password)
        self._wait_for_element(self.XPATHS["password2"]).send_keys(self.passcode)
        self._wait_for_element(self.XPATHS["submit"]).click()
        self._log("Login completed")

    def _setup_and_launch_workspace(self) -> None:
        """Configure protocol handlers and launch workspace application."""
        self._log("Setting up handlers and launching workspace...")
        for action in ("install", "detect", "disclaimer"):
            try:
                self._wait_for_element(self.XPATHS[action], timeout=5).click()
            except Exception:
                pass  # Element may not always be present
        self._wait_for_element(self.XPATHS["workspace"]).click()
        self._wait_for_element(self.XPATHS["open"]).click()
        self._log("Workspace setup and launch completed")

    def _start_ica_client(self, ica_file: Path) -> None:
        """Launch ICA client with downloaded file."""
        self._log(f"Starting ICA client with file: {ica_file}")
        subprocess.Popen(
            [str(self.config.ica_path), str(ica_file)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    def _setup_driver_and_run(self) -> None:
        """Setup webdriver, perform login, launch workspace, and cleanup."""
        options = Options()
        with webdriver.Firefox(options=options) as driver:
            self.driver = driver
            driver.get(self.config.url)
            self._log("Browser opened and navigated to workspace URL")
            self._login()
            self._setup_and_launch_workspace()
            ica_file = self._wait_for_download()
            self._start_ica_client(ica_file)
            self._log("Browser closed")

    def run(self) -> None:
        """Execute complete automation sequence."""
        self._log("Starting workspace automation...")
        try:
            self._clean_ica_files()
            self._setup_driver_and_run()
            self._log("Workspace automation completed successfully")
        except Exception as e:
            self._log(f"Error during automation: {e}")
            raise



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