# Rhythm Canvas Sync Extension

This Chrome extension automatically detects assignments from Canvas LMS and syncs them to your Rhythm account.

## Features

- Automatically scans Canvas dashboard and course pages for assignments
- Detects assignment details including title, due date, and course
- One-click sync to Rhythm

## Installation

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable "Developer mode" using the toggle in the top-right corner
3. Click "Load unpacked" and select the extension folder
4. The Rhythm extension will now appear in your browser toolbar

## Usage

1. Log in to your Rhythm account at [rhythm.flyonthewalldev.com](https://rhythm.flyonthewalldev.com)
2. Visit Canvas at [canvas.instructure.com](https://canvas.instructure.com) and navigate to your dashboard or courses
3. The extension will automatically scan for assignments
4. Click the Rhythm icon in your browser toolbar to open the extension popup
5. Click "Sync to Rhythm" to send the assignments to your Rhythm account

## Development

The extension consists of the following components:

- `manifest.json`: Configuration file for the extension
- `content.js`: Scrapes assignment data from Canvas pages
- `popup.html`: User interface for the extension
- `popup.js`: Handles popup UI logic
- `upload.js`: Background service worker that sends data to the Rhythm API

## Authentication

The extension uses a JWT token stored in `chrome.storage` to authenticate with the Rhythm API.
Make sure you're logged in to Rhythm before attempting to sync.
