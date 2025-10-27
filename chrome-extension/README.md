# LinkedIn Profile AI Assessor - Chrome Extension

A Chrome extension that enables one-click profile bookmarking and AI-powered candidate assessment directly from LinkedIn.

## ⚠️ Important: Compliance Notice

**Please read [COMPLIANCE.md](./COMPLIANCE.md) before using this extension.**

LinkedIn's Terms of Service prohibit scraping or copying profile data, even manually. This extension should be used carefully and at your own risk. We recommend using it primarily as a bookmark manager with AI assessment capabilities rather than a data extraction tool.

## 🚀 Features

- **One-Click Bookmarking**: Save LinkedIn profiles to organized lists
- **AI-Powered Assessment**: Quick candidate evaluation using Claude AI
- **List Management**: Organize candidates into custom lists
- **Job Templates**: Define requirements and weights for consistent evaluation
- **Batch Operations**: Process multiple candidates efficiently
- **Settings Management**: Customize behavior and API connections

## 📦 Installation

### Option 1: Load Unpacked (Development Mode)

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable "Developer mode" (toggle in top right)
3. Click "Load unpacked"
4. Select the `chrome-extension` folder
5. The extension should load successfully!

### Option 2: Build for Production

```bash
# Future: Package as .crx file for distribution
# Not yet implemented
```

## 🔧 Configuration

### First Time Setup

1. Click the extension icon in your toolbar
2. Click "Settings" in the popup
3. Configure:
   - **Backend API URL**: Your Flask backend URL (default: `http://localhost:5001`)
   - **Your Name**: For tracking your activities
   - **Default List**: Where profiles are saved by default
   - **Assessment Settings**: Auto-assess, batch size, etc.

### API Requirements

The extension requires a running backend server. See [../backend/README.md](../backend/README.md) for setup instructions.

Required environment variables:
- `ANTHROPIC_API_KEY` - For AI assessments
- `CORESIGNAL_API_KEY` - For full profile data (optional)
- `SUPABASE_URL` - For data storage
- `SUPABASE_KEY` - For database access

## 📖 Usage

### Basic Workflow

1. **Browse LinkedIn**: Navigate to any LinkedIn profile
2. **Click Extension Icon**: Opens the popup interface
3. **Select a List**: Choose where to save the profile
4. **Add Profile**: Click "Add to List" button
5. **Optional Assessment**: Click "Run Analysis" for AI evaluation

### Keyboard Shortcuts

*(Not yet implemented)*

### Context Menu

Right-click any LinkedIn profile link to:
- Add to LinkedIn AI Assessor
- Quick Assess Profile

## 🛠️ Extension Architecture

```
chrome-extension/
├── manifest.json           # Extension configuration (V3)
├── popup/                  # Extension popup interface
│   ├── popup.html         # UI structure
│   ├── popup.js           # Popup logic
│   └── popup.css          # Styling
├── content/               # LinkedIn page interaction
│   ├── content.js         # Main content script
│   ├── linkedin-parser.js # Profile extraction
│   └── content.css        # Page styling
├── background/            # Background service worker
│   └── service-worker.js  # API communication
├── options/               # Settings page
│   ├── options.html       # Settings UI
│   ├── options.js         # Settings logic
│   └── options.css        # Settings styling
└── icons/                 # Extension icons
    ├── icon16.png
    ├── icon48.png
    └── icon128.png
```

## 🔒 Privacy & Security

### Data Collection

The extension:
- ✅ Only processes profiles you explicitly select
- ✅ Stores data locally or in your configured backend
- ✅ Never sends data to third parties
- ✅ Requires manual action for all operations

### Permissions Explained

- **storage**: Save settings and cache data locally
- **tabs**: Access current tab information
- **activeTab**: Interact with LinkedIn pages
- **contextMenus**: Add right-click menu options
- **notifications**: Show completion notifications
- **scripting**: Inject content scripts

### Host Permissions

- `https://www.linkedin.com/*`: Access LinkedIn pages
- `http://localhost:5001/*`: Connect to local backend (development)
- `http://localhost:3000/*`: Open dashboard (development)

## 🐛 Troubleshooting

### Extension Won't Load

1. Check Chrome version (requires Chrome 88+)
2. Ensure all files are present
3. Check browser console for errors
4. Try reloading the extension

### Can't Add Profiles

1. Verify backend is running (`http://localhost:5001`)
2. Check API configuration in Settings
3. Ensure you're on a LinkedIn profile page
4. Check browser console for error messages

### Context Menus Not Showing

This is normal. Context menus require the `contextMenus` permission which may not be available in all Chrome versions or contexts.

### Assessment Not Working

1. Verify `ANTHROPIC_API_KEY` is set in backend
2. Check backend logs for errors
3. Ensure profile data was extracted successfully
4. Try reloading the extension

## 🔄 Updates & Maintenance

### Updating the Extension

1. Pull latest changes from repository
2. Go to `chrome://extensions/`
3. Click the reload icon on the extension card

### Clearing Cache

1. Open extension popup
2. Click "Settings"
3. Click "Clear Cache" button

## 📝 Development

### Running in Development Mode

```bash
# Terminal 1: Start backend
cd backend
python3 app.py

# Terminal 2: Start frontend (optional)
cd frontend
npm start

# Chrome: Load unpacked extension
# Navigate to chrome://extensions/
# Load the chrome-extension folder
```

### Making Changes

1. Edit files in `chrome-extension/` directory
2. Go to `chrome://extensions/`
3. Click reload icon on extension
4. Test changes on LinkedIn

### Debugging

- **Popup**: Right-click extension icon → Inspect popup
- **Background**: Click "Service worker" link in extension details
- **Content Scripts**: Open DevTools on LinkedIn page
- **Options Page**: Right-click options page → Inspect

## ⚖️ Legal & Compliance

**IMPORTANT**: This extension may violate LinkedIn's Terms of Service. Use at your own risk.

See [COMPLIANCE.md](./COMPLIANCE.md) for detailed information about:
- LinkedIn's Terms of Service
- Legal risks
- Best practices
- Safer alternatives

## 🤝 Contributing

*(Not yet open for contributions)*

## 📄 License

*(License to be determined)*

## 🆘 Support

For issues or questions:
- Check [COMPLIANCE.md](./COMPLIANCE.md) for ToS questions
- Check [../plan.md](../plan.md) for development roadmap
- Review backend logs for API issues

---

**Version**: 1.0.0
**Last Updated**: October 2024
**Status**: Development/Beta