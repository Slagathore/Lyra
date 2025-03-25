# Lyra Assets Directory

This directory contains visual assets used by Lyra, such as icons and images. By default, Lyra doesn't come with a predefined visual appearance - you can customize how she looks!

## Customizing Lyra's Appearance

### Icon/Avatar

To give Lyra a visual identity:

1. Create or select an image to represent Lyra
2. Save it as `lyra_icon.png` in this directory
3. Recommended size: 256x256 pixels (square)
4. PNG format with transparency is ideal

The icon will be used for:
- The application window icon
- The system tray icon
- The assistant window

### Other Customizable Assets

You can also add:

- `lyra_splash.png`: Displayed during startup (recommended size: 800x400)
- `lyra_background.png`: Used as chat background (if enabled)
- `lyra_chat_avatar.png`: Smaller avatar shown in chat messages (64x64)

## Default Behavior

If these files don't exist:
- Lyra will function normally without visual elements
- A simple geometric icon may be generated as a placeholder
- System default icons may be used for application windows

## Creating Your Own Assets

When creating assets for Lyra, consider:

1. **Visual Identity**: Choose imagery that represents how you envision Lyra
2. **Consistency**: Use a consistent style across different assets
3. **Size**: Create images at appropriate resolutions (higher is better)
4. **Format**: PNG format with transparency is recommended

## Asset Attribution

If you use assets created by others, ensure you have proper permission or licenses to use them.

## Technical Notes

- Assets are loaded at startup - changes require restarting Lyra
- If you experience any issues with custom assets, remove them and restart
- PNG, JPG, and GIF formats are supported, but PNG is recommended
