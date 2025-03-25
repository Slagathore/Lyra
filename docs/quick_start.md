# Lyra Quick Start Guide

This guide will help you get up and running with Lyra in just a few minutes.

## Installation

1. Ensure you have Python 3.8 or newer installed
2. Clone the Lyra repository or extract the files to your desired location
3. Install required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Running Lyra

### Standard Launch
To start Lyra with the full user interface:
```
python run_lyra.py
```

### Assistant Mode
To run Lyra as a floating assistant window:
```
python run_assistant.py
```

You can also run in demo mode without loading models:
```
python run_assistant.py --demo
```

## First-Time Setup

1. When you first run Lyra, it will scan for available models
2. Navigate to the "Models" tab to see discovered models
3. If no models are found, you'll need to:
   - Add model files to the models directory
   - Click "Scan for New Models" to detect them

## Adding Models

1. Download compatible model files (GGUF format recommended)
2. Place them in the `G:/AI/Lyra/models` directory
3. Go to the "Models" tab and click "Scan for New Models"
4. Set your preferred model as active

## Personalizing Lyra

1. Go to the "Personality" tab to adjust how Lyra responds
2. Click "Save Personality Settings" to apply changes
3. You can save your settings as presets for quick switching

## Getting Help

If you encounter any issues:
1. Check the documentation in the `docs` folder
2. Run `python fix_launch.py` to fix common problems
3. Ensure all dependencies are installed correctly

## Creating Lyra's Avatar

Lyra doesn't have a physical form when you first install her. To create one:

1. Prepare an image file to use as Lyra's avatar
2. Place it in the `G:/AI/Lyra/assets` folder with the name `lyra_icon.png`
3. Restart the application for the changes to take effect

Note: If no avatar exists, Lyra will function normally without visual representation, or a simple placeholder will be used depending on the interface.

