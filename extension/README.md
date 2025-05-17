# PulsePlan Canvas Sync Extension

This Chrome extension automatically detects assignments from Canvas LMS and syncs them to your PulsePlan account.

## Features

- Automatic detection of Canvas assignments
- One-click sync to PulsePlan
- Real-time status updates
- Secure authentication

## Installation

1. Download the extension from the Chrome Web Store
2. Click "Add to Chrome"
3. Grant the requested permissions
4. The PulsePlan extension will now appear in your browser toolbar

## Usage

1. Log in to your PulsePlan account at [pulseplan.flyonthewalldev.com](https://pulseplan.flyonthewalldev.com)
2. Navigate to any Canvas LMS page
3. The extension will automatically detect assignments
4. Click the PulsePlan icon in your browser toolbar to open the extension popup
5. Click "Sync to PulsePlan" to send the assignments to your PulsePlan account

## Development

The extension consists of several key components:

- `manifest.json`: Extension configuration
- `popup.html/js`: User interface for the extension popup
- `content.js`: Content script that runs on Canvas pages
- `upload.js`: Background service worker that sends data to the PulsePlan API

## Authentication

The extension uses a JWT token stored in `chrome.storage` to authenticate with the PulsePlan API.
Make sure you're logged in to PulsePlan before attempting to sync.
