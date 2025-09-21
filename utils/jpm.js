#!/usr/bin/env node
/**
 * Selenium + Node.js automation script for JPM login workflow
 *
 * Usage: JPM_USER=xxx JPM_PASSWORD=xxx node script.js <pcode>
 */

import { Builder, By, until } from "selenium-webdriver";
import firefox from "selenium-webdriver/firefox.js";
import fs from "fs";
import { spawn } from "child_process";
import { execFile } from "child_process";
import { fileURLToPath } from "url";
import path from "path";
import os from "os";

const JPM_LOGIN_URL = "http://myworkspace.jpmchase.com";
const DOWNLOAD_DIR = path.join(os.homedir(), "Downloads");
const ICA_GLOB = /\.ica$/i;
const WAIT_ELEMENT_TIMEOUT = 20000; // ms
const WAIT_DOWNLOAD_TIMEOUT = 60000; // ms
const POLL_INTERVAL = 1000; // ms

const JPM_USER = process.env.JPM_USER;
const JPM_PASSWORD = process.env.JPM_PASSWORD;
if (!JPM_USER || !JPM_PASSWORD) {
  console.error("Environment variables JPM_USER and JPM_PASSWORD must be set");
  process.exit(1);
}
const pcode = process.argv[2];
if (!pcode) {
  console.error("Usage: JPM_USER=xxx JPM_PASSWORD=xxx node script.js <pcode>");
  process.exit(1);
}

/**
 * Utility: remove files by regex from dir
 */
function removeFilesByPattern(dir, regex) {
  for (const f of fs.readdirSync(dir)) {
    if (regex.test(f)) {
      fs.unlinkSync(path.join(dir, f));
    }
  }
}

/**
 * Utility: wait until .ica file appears
 */
async function waitForICA(downloadDir, timeoutMs) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    const files = fs.readdirSync(downloadDir).filter((f) => ICA_GLOB.test(f));
    if (files.length > 0) {
      const filePath = path.join(downloadDir, files[0]);
      console.log(`Found ICA file: ${filePath}`);
      return filePath;
    }
    console.log("Waiting for ICA file...");
    await new Promise((r) => setTimeout(r, POLL_INTERVAL));
  }
  throw new Error("Timed out waiting for ICA file");
}

/**
 * Utility: safe subprocess launch
 */
function launchWfica(icaPath) {
  const wficaBin = "/opt/Citrix/ICAClient/wfica.sh";
  if (!fs.existsSync(wficaBin)) {
    throw new Error(`wfica.sh not found at ${wficaBin}`);
  }

  const child = spawn(wficaBin, [icaPath], {
    detached: true,
    stdio: "ignore"
  });

  // Disconnect the child completely
  child.unref();

  console.log("Launched Citrix client (detached from script)");
}

/**
 * Selenium wait and click/send keys
 */
async function waitAndClick(driver, xpath, { sendKey, click } = {}) {
  const el = await driver.wait(
    until.elementLocated(By.xpath(xpath)),
    WAIT_ELEMENT_TIMEOUT
  );
  await driver.wait(until.elementIsVisible(el), WAIT_ELEMENT_TIMEOUT);
  await driver.wait(until.elementIsEnabled(el), WAIT_ELEMENT_TIMEOUT);
  if (sendKey !== undefined) {
    await el.sendKeys(sendKey);
  } else if (click) {
    await el.click();
  } else {
    throw new Error("Must pass sendKey or click option");
  }
}

async function main() {
  removeFilesByPattern(DOWNLOAD_DIR, ICA_GLOB);

  // Firefox options: custom download dir
  let options = new firefox.Options();
  options.setPreference("browser.download.dir", DOWNLOAD_DIR);
  options.setPreference("browser.download.folderList", 2);
  options.setPreference("browser.helperApps.neverAsk.saveToDisk", "application/x-ica,application/ica");
  options.setPreference("browser.download.manager.showWhenStarting", false);

  const driver = await new Builder()
    .forBrowser("firefox")
    .setFirefoxOptions(options)
    .build();

  try {
    await driver.get(JPM_LOGIN_URL);

    // Login workflow
    await waitAndClick(driver, '//*[@id="login"]', { sendKey: JPM_USER });
    await waitAndClick(driver, '(//input[@type="password"])[1]', { sendKey: JPM_PASSWORD });
    await waitAndClick(driver, '(//input[@type="password"])[2]', { sendKey: pcode });

    await waitAndClick(driver, '//*[@id="loginBtn"]', { click: true });

    await waitAndClick(driver, '//*[@id="protocolhandler-welcome-installButton"]', { click: true });
    await waitAndClick(driver, '//*[@id="protocolhandler-detect-alreadyInstalledLink"]', { click: true });

    await waitAndClick(driver, '//*[@id="jpmcAcceptDisclaimerBtn"]', { click: true });

    await waitAndClick(driver, '//*[@class="storeapp-name"  and contains(text(),"ENT_CDC2_PRD_14")]', { click: true });
    await waitAndClick(driver, '//*[@class="theme-highlight-color appDetails-actions-text" and contains(text(),"Open") ]', { click: true });

    // Wait for ICA download
    const icaFile = await waitForICA(DOWNLOAD_DIR, WAIT_DOWNLOAD_TIMEOUT);
    launchWfica(icaFile);
  } catch (err) {
    console.error("Error during automation:", err);
  } finally {
    await driver.quit();
  }
}

main();

