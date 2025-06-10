# PulsePlan Canvas Sync Extension

This Chrome extension uses AI-powered smart extraction to automatically detect assignments from Canvas LMS and syncs them to your PulsePlan account.

## Features

- 🤖 **AI-Powered Smart Extraction**: Uses Google's Gemini AI to intelligently extract assignment data from any Canvas page layout
- 🎯 **Intelligent Content Recognition**: Automatically identifies assignments, due dates, courses, and priorities
- 📊 **Adaptive Scraping**: Works with all Canvas page types (dashboard, course pages, assignment lists, etc.)
- 🔄 **Automatic Sync**: One-click sync to PulsePlan with real-time status updates
- 🛡️ **Secure Authentication**: Encrypted token-based authentication
- 💾 **Smart Caching**: Intelligent caching to reduce API calls and improve performance
- 🔍 **Fallback Support**: Falls back to pattern-based extraction if AI service is unavailable

## Installation

1. Download the extension from the Chrome Web Store
2. Click "Add to Chrome"
3. Grant the requested permissions
4. The PulsePlan extension will now appear in your browser toolbar

## Usage

1. Log in to your PulsePlan account at [pulseplan.flyonthewalldev.com](https://pulseplan.app)
2. Navigate to any Canvas LMS page (dashboard, course pages, assignment lists, etc.)
3. The extension will automatically use AI to intelligently extract assignment data
4. Click the PulsePlan icon in your browser toolbar to open the extension popup
5. Review the AI-extracted assignments and click "Sync to PulsePlan" to send them to your account

### How AI Extraction Works

The extension uses Google's Gemini AI to:

- Analyze the entire page structure and content
- Identify assignment titles, due dates, courses, and other relevant information
- Extract data even from complex or non-standard Canvas layouts
- Provide confidence scores for each extracted assignment
- Fall back to traditional pattern matching if AI service is unavailable

## Development

The extension consists of several key components:

- `manifest.json`: Extension configuration and permissions
- `popup.html/js`: User interface for the extension popup with AI status indicators
- `content.js`: **AI-powered content script** that uses Gemini API for intelligent extraction
- `upload.js`: Background service worker that sends data to the PulsePlan API

### AI-Powered Architecture

The new AI-powered extraction system:

1. **Smart Page Analysis**: Determines Canvas page type (dashboard, assignments, courses, etc.)
2. **Content Area Detection**: Identifies relevant content areas that likely contain assignment data
3. **Gemini API Integration**: Sends page content to Google's Gemini AI for intelligent extraction
4. **Result Processing**: Converts AI responses into structured assignment data
5. **Caching System**: Intelligently caches results to minimize API calls
6. **Fallback Support**: Uses traditional pattern matching if AI service is unavailable

### Key Features

- **Adaptive Scraping**: Works with any Canvas layout or theme
- **Confidence Scoring**: AI provides confidence scores for extracted data
- **Error Handling**: Robust error handling with graceful fallbacks
- **Performance Optimization**: Smart caching and request throttling

## Authentication

The extension uses a JWT token stored in `chrome.storage` to authenticate with the PulsePlan API.
Make sure you're logged in to PulsePlan before attempting to sync.
