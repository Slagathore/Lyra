"""
Desktop notification utilities for Lyra
"""
import os
import platform

def send_notification(title, message, icon_path=None):
    """Send a desktop notification, platform-aware"""
    try:
        system = platform.system()
        
        if system == "Windows":
            show_notification(title, message)
            return True
            
        elif system == "Darwin":  # macOS
            os.system(f"""
                osascript -e 'display notification "{message}" with title "{title}"'
                """)
            return True
            
        elif system == "Linux":
            if icon_path:
                os.system(f'notify-send "{title}" "{message}" -i "{icon_path}"')
            else:
                os.system(f'notify-send "{title}" "{message}"')
            return True
            
        return False
    except Exception as e:
        print(f"Failed to send notification: {e}")
        return False

def show_notification(title, message):
    """Show a system notification."""
    try:
        from win10toast import ToastNotifier
        toaster = ToastNotifier()
        toaster.show_toast(title, message, duration=5)
    except ImportError:
        print(f"Notification: {title} - {message}")
        print("(win10toast not installed, showing notification in console only)")

def notify_new_message(from_name="Lyra"):
    """Send notification for new message"""
    icon_path = os.path.join("G:/AI/Lyra/assets", "lyra_icon.png")
    if not os.path.exists(icon_path):
        icon_path = None
        
    return send_notification(
        f"New message from {from_name}",
        "You have received a new message in Lyra chat",
        icon_path
    )

if __name__ == "__main__":
    # Test notification
    notify_new_message()
