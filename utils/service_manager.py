"""
Utility to manage Lyra services and instances
Helps with stopping, starting, and detecting running instances
"""

import os
import sys
import time
import socket
import psutil
import argparse
import subprocess
from pathlib import Path

# Windows service management
if sys.platform == 'win32':
    import win32serviceutil
    import win32service
    import win32con
    import pywintypes

LYRA_SERVICE_NAME = "LyraAIService"

def find_lyra_processes():
    """Find running Lyra processes"""
    lyra_processes = []
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            # Check if this is a Python process
            if proc.info['name'] in ('python.exe', 'pythonw.exe') or 'lyra' in proc.info['name'].lower():
                cmdline = proc.info['cmdline']
                if cmdline:
                    # Check if any of the command line arguments contain 'lyra'
                    if any('lyra' in str(arg).lower() for arg in cmdline):
                        process_info = {
                            'pid': proc.pid,
                            'name': proc.info['name'],
                            'cmdline': ' '.join(cmdline) if cmdline else "",
                            'process': proc,
                            'type': 'process'
                        }
                        lyra_processes.append(process_info)
                        
            # Also look for any process with 'lyra' in the name
            elif 'lyra' in proc.info['name'].lower():
                process_info = {
                    'pid': proc.pid,
                    'name': proc.info['name'],
                    'cmdline': ' '.join(proc.info['cmdline'] if proc.info['cmdline'] else []),
                    'process': proc,
                    'type': 'process'
                }
                lyra_processes.append(process_info)
                
            # Check for NSSM process running Lyra service
            elif 'nssm' in proc.info['name'].lower():
                cmdline = proc.info['cmdline']
                if cmdline and any('lyra' in str(arg).lower() for arg in cmdline):
                    process_info = {
                        'pid': proc.pid,
                        'name': proc.info['name'],
                        'cmdline': ' '.join(cmdline) if cmdline else "",
                        'process': proc,
                        'type': 'nssm'
                    }
                    lyra_processes.append(process_info)
                
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    
    # Check if Lyra is running as a Windows service
    if sys.platform == 'win32':
        try:
            lyra_service = get_service_info(LYRA_SERVICE_NAME)
            if lyra_service:
                lyra_processes.append(lyra_service)
        except:
            pass
    
    return lyra_processes

def get_service_info(service_name):
    """Get information about a Windows service"""
    if sys.platform != 'win32':
        return None
        
    try:
        import win32serviceutil
        import win32service
        
        # Try multiple methods to detect the service
        try:
            service_status = win32serviceutil.QueryServiceStatus(service_name)
            running_state = service_status[1]
            
            if running_state == win32service.SERVICE_RUNNING:
                state = "Running"
            elif running_state == win32service.SERVICE_STOPPED:
                state = "Stopped"
            elif running_state == win32service.SERVICE_PAUSED:
                state = "Paused"
            elif running_state == win32service.SERVICE_START_PENDING:
                state = "Starting"
            elif running_state == win32service.SERVICE_STOP_PENDING:
                state = "Stopping"
            else:
                state = f"Unknown ({running_state})"
                
            # Get service configuration
            schService = win32service.OpenService(
                win32service.OpenSCManager(None, None, win32service.SC_MANAGER_ALL_ACCESS),
                service_name,
                win32service.SERVICE_ALL_ACCESS
            )
            
            service_config = win32service.QueryServiceConfig(schService)
            binary_path = service_config[3]
            
            # Get service PID if running
            pid = None
            try:
                if running_state == win32service.SERVICE_RUNNING:
                    # Look for the NSSM process controlling the service
                    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                        if proc.info['name'].lower() == 'nssm.exe':
                            cmd = proc.info['cmdline']
                            if cmd and any(service_name.lower() in str(arg).lower() for arg in cmd):
                                pid = proc.pid
                                break
            except:
                pass
            
            # Try to get the display name, use service_name as fallback if it fails
            try:
                display_name = win32serviceutil.GetServiceDisplayName(service_name)
            except pywintypes.error:
                display_name = service_name  # Fallback to using the service name
                
            return {
                'name': service_name,
                'display_name': display_name,
                'binary_path': binary_path,
                'state': state,
                'pid': pid,
                'type': 'service',
                'service_name': service_name
            }
        except pywintypes.error as e:
            # The service might not exist in registry, but could still have processes
            # Try to find NSSM processes that might be related
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                if proc.info['name'].lower() == 'nssm.exe':
                    cmd = proc.info['cmdline']
                    if cmd and any(service_name.lower() in str(arg).lower() for arg in cmd):
                        return {
                            'name': service_name,
                            'display_name': f"NSSM Service (Not in registry): {service_name}",
                            'binary_path': "Unknown - NSSM process only",
                            'state': "Zombie (Registry entry missing but process running)",
                            'pid': proc.pid,
                            'type': 'zombie_service',
                            'service_name': service_name,
                            'process': proc
                        }
            return None
            
    except Exception as e:
        print(f"Error getting service info: {e}")
        return None

def stop_windows_service(service_name):
    """Stop a Windows service"""
    if sys.platform != 'win32':
        print("Not running on Windows, can't stop Windows service")
        return False
        
    try:
        # First try standard service stopping
        service_info = get_service_info(service_name)
        if not service_info:
            print(f"Service {service_name} not found.")
            return False
            
        if service_info.get('type') == 'zombie_service':
            print(f"Found zombie service process. Attempting to kill directly...")
            try:
                proc = service_info.get('process')
                if proc:
                    proc.terminate()
                    try:
                        proc.wait(timeout=5)
                        print(f"Successfully terminated zombie service process.")
                        return True
                    except psutil.TimeoutExpired:
                        proc.kill()
                        print(f"Had to forcefully kill zombie service process.")
                        return True
            except Exception as proc_e:
                print(f"Error killing zombie service process: {proc_e}")
                return False
        
        print(f"Stopping Windows service: {service_name}...")
        
        # Try using SC.exe command for more forceful stop
        try:
            # First try the Windows API
            win32serviceutil.StopService(service_name)
            print("Service stop command sent. Waiting for it to stop...")
        except Exception as api_e:
            print(f"Error using Windows API to stop service: {api_e}")
            print("Trying SC.EXE command...")
            
            # Try SC command as a fallback
            try:
                subprocess.run(["sc", "stop", service_name], check=True, text=True, capture_output=True)
                print("Service stop command sent via SC. Waiting for it to stop...")
            except subprocess.CalledProcessError as sc_e:
                print(f"SC command failed: {sc_e}")
                print("Service might need manual intervention.")
                return False
        
        # Wait for service to stop
        stopped = False
        for i in range(30):  # Wait up to 30 seconds
            try:
                status = win32serviceutil.QueryServiceStatus(service_name)
                if status[1] == win32service.SERVICE_STOPPED:
                    print(f"Service {service_name} stopped successfully.")
                    stopped = True
                    break
                elif status[1] == win32service.SERVICE_STOP_PENDING:
                    print(f"Service is stopping... ({i+1}/30 sec)")
                else:
                    print(f"Service in state {status[1]}... ({i+1}/30 sec)")
                time.sleep(1)
            except pywintypes.error:
                # Service might not exist anymore
                print(f"Service {service_name} no longer exists in registry.")
                stopped = True
                break
        
        if not stopped:
            print(f"Timed out waiting for service {service_name} to stop.")
            
            # As a last resort, look for NSSM processes and kill them directly
            print("Looking for NSSM processes to terminate forcefully...")
            killed_any = False
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                if proc.info['name'].lower() == 'nssm.exe':
                    cmd = proc.info['cmdline']
                    if cmd and any(service_name.lower() in str(arg).lower() for arg in cmd):
                        print(f"Found NSSM process (PID: {proc.pid}) for service. Attempting to kill...")
                        try:
                            proc.terminate()
                            try:
                                proc.wait(timeout=5)
                                print(f"Successfully terminated NSSM process.")
                                killed_any = True
                            except psutil.TimeoutExpired:
                                proc.kill()
                                print(f"Had to forcefully kill NSSM process.")
                                killed_any = True
                        except Exception as proc_e:
                            print(f"Error killing NSSM process: {proc_e}")
            
            if killed_any:
                print("Service processes forcefully terminated.")
                return True
            else:
                print("Could not find any service processes to terminate.")
                return False
        
        return stopped
    except Exception as e:
        print(f"Error stopping service: {e}")
        return False

def start_windows_service(service_name):
    """Start a Windows service"""
    if sys.platform != 'win32':
        print("Not running on Windows, can't start Windows service")
        return False
        
    try:
        win32serviceutil.StartService(service_name)
        print(f"Started service {service_name}.")
        return True
    except Exception as e:
        print(f"Error starting service: {e}")
        return False

def remove_windows_service(service_name):
    """Remove a Windows service"""
    if sys.platform != 'win32':
        print("Not running on Windows, can't remove Windows service")
        return False
        
    try:
        # Stop the service first
        try:
            win32serviceutil.StopService(service_name)
            time.sleep(2)  # Give it time to stop
        except:
            pass  # Might already be stopped
            
        # Remove the service
        win32serviceutil.RemoveService(service_name)
        print(f"Removed service {service_name}.")
        return True
    except Exception as e:
        print(f"Error removing service: {e}")
        return False

def check_instance_running():
    """Check if a Lyra instance is already running via socket connection"""
    try:
        # Try to connect to the Lyra instance port
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(('localhost', 37849))  # Port used by persistent_module
        client.close()
        return True
    except:
        return False

def focus_running_instance():
    """Send a request to bring the running instance to the foreground"""
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(('localhost', 37849))
        client.send(b'SHOW_WINDOW')
        client.close()
        return True
    except:
        return False

def stop_all_instances():
    """Stop all running Lyra instances"""
    processes = find_lyra_processes()
    if not processes:
        print("No Lyra processes or services found.")
        return False
    
    print(f"Found {len(processes)} Lyra instances:")
    for i, proc in enumerate(processes):
        if proc['type'] == 'service':
            print(f"{i+1}. Windows Service: {proc['name']} - {proc['state']} - {proc['binary_path']}")
        else:
            print(f"{i+1}. Process: PID {proc['pid']} - {proc['name']} - {proc['cmdline']}")
    
    try:
        choice = input("Stop all these instances? (y/n): ").strip().lower()
        if choice != 'y':
            return False
        
        for proc in processes:
            if proc['type'] == 'service':
                # Stop Windows service
                stop_windows_service(proc['service_name'])
            else:
                # Stop regular process
                try:
                    print(f"Stopping process {proc['pid']}...")
                    proc['process'].terminate()
                    
                    # Wait for termination
                    try:
                        proc['process'].wait(timeout=5)
                    except psutil.TimeoutExpired:
                        print(f"Process {proc['pid']} didn't terminate, trying to kill...")
                        proc['process'].kill()
                except:
                    print(f"Failed to terminate process {proc['pid']}, trying to kill...")
                    try:
                        proc['process'].kill()
                    except:
                        print(f"Failed to kill process {proc['pid']}. You may need admin rights.")
        
        # Wait a moment and check if processes are gone
        time.sleep(2)
        remaining_processes = [p for p in processes if p['type'] != 'service' and psutil.pid_exists(p['pid'])]
        
        # Check if services are stopped
        remaining_services = []
        if sys.platform == 'win32':
            for proc in processes:
                if proc['type'] == 'service':
                    try:
                        status = win32serviceutil.QueryServiceStatus(proc['service_name'])
                        if status[1] != win32service.SERVICE_STOPPED:
                            remaining_services.append(proc)
                    except:
                        pass  # Service might have been removed
        
        if remaining_processes or remaining_services:
            print(f"{len(remaining_processes)} processes and {len(remaining_services)} services could not be stopped.")
            return False
        else:
            print("All Lyra instances stopped successfully.")
            return True
            
    except KeyboardInterrupt:
        print("\nOperation cancelled.")
        return False

def manage_windows_service():
    """Manage the Lyra Windows service"""
    if sys.platform != 'win32':
        print("Not running on Windows, can't manage Windows services")
        return
    
    try:
        # Check if service exists
        service_info = get_service_info(LYRA_SERVICE_NAME)
        
        if service_info:
            print(f"Lyra Windows service found: {LYRA_SERVICE_NAME}")
            print(f"Display name: {service_info['display_name']}")
            print(f"Status: {service_info['state']}")
            print(f"Binary path: {service_info['binary_path']}")
            print("\nOptions:")
            print("1. Stop service")
            print("2. Start service")
            print("3. Remove service")
            print("4. Back to main menu")
            
            choice = input("\nEnter choice (1-4): ").strip()
            
            if choice == "1":
                stop_windows_service(LYRA_SERVICE_NAME)
            elif choice == "2":
                start_windows_service(LYRA_SERVICE_NAME)
            elif choice == "3":
                confirm = input("Are you sure you want to remove the service? (y/n): ").strip().lower()
                if confirm == 'y':
                    remove_windows_service(LYRA_SERVICE_NAME)
            else:
                return
        else:
            print(f"Lyra Windows service ({LYRA_SERVICE_NAME}) not found.")
    except Exception as e:
        print(f"Error managing Windows service: {e}")

def start_lyra_tray():
    """Start the Lyra tray application"""
    script_dir = Path(__file__).parent.parent
    tray_script = script_dir / "modules" / "persistent_module.py"
    
    if not tray_script.exists():
        print(f"Error: Could not find {tray_script}")
        return False
    
    try:
        subprocess.Popen([sys.executable, str(tray_script)], 
                         cwd=str(script_dir),
                         creationflags=subprocess.CREATE_NEW_CONSOLE)
        print("Lyra tray application started.")
        return True
    except Exception as e:
        print(f"Error starting Lyra tray: {e}")
        return False

def restart_lyra_tray():
    """Restart the Lyra tray application"""
    if stop_all_instances():
        time.sleep(1)  # Give it a moment to clean up
        return start_lyra_tray()
    return False

def force_kill_service_processes(service_name):
    """Forcefully kill all processes related to a service"""
    print(f"Attempting to forcefully kill all processes related to {service_name}...")
    
    # Look for NSSM processes
    killed_any = False
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = " ".join(proc.info['cmdline']) if proc.info['cmdline'] else ""
            if (
                (proc.info['name'].lower() == 'nssm.exe' and service_name.lower() in cmdline.lower()) or
                ('lyra' in proc.info['name'].lower() and 'service' in cmdline.lower()) or
                (service_name.lower() in cmdline.lower())
            ):
                print(f"Found related process (PID: {proc.pid}, Name: {proc.info['name']}). Killing...")
                try:
                    proc.terminate()
                    try:
                        proc.wait(timeout=3)
                    except psutil.TimeoutExpired:
                        proc.kill()
                    killed_any = True
                except Exception as proc_e:
                    print(f"Error killing process: {proc_e}")
        except:
            continue
    
    return killed_any

def install_as_service():
    """Install Lyra as a Windows service using NSSM"""
    if sys.platform != 'win32':
        print("Service installation is only supported on Windows.")
        return False
    
    try:
        # Check if NSSM is available
        nssm_path = Path("tools/nssm.exe")
        if not nssm_path.exists():
            print("NSSM not found. Download it from http://nssm.cc/ and place it in tools/nssm.exe")
            return False
        
        # Check if service already exists
        service_info = get_service_info(LYRA_SERVICE_NAME)
        if service_info:
            print(f"Service {LYRA_SERVICE_NAME} already exists. Remove it first.")
            return False
        
        # Get path to Python and the script to run
        python_path = sys.executable
        script_path = Path(__file__).parent.parent / "modules" / "persistent_module.py"
        
        if not script_path.exists():
            print(f"Script {script_path} not found.")
            return False
        
        # Set up service parameters
        service_cmd = [
            str(nssm_path.absolute()),
            "install",
            LYRA_SERVICE_NAME,
            python_path,
            str(script_path.absolute())
        ]
        
        # Install service
        print(f"Installing service {LYRA_SERVICE_NAME}...")
        result = subprocess.run(service_cmd, check=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            # Configure service
            subprocess.run([
                str(nssm_path.absolute()),
                "set",
                LYRA_SERVICE_NAME,
                "DisplayName",
                "Lyra AI Background Service"
            ], check=True)
            
            subprocess.run([
                str(nssm_path.absolute()),
                "set",
                LYRA_SERVICE_NAME,
                "Description",
                "Provides persistent background operation for Lyra AI"
            ], check=True)
            
            print("Service installed successfully. Starting service...")
            start_windows_service(LYRA_SERVICE_NAME)
            return True
        else:
            print(f"Error installing service: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"Error installing service: {e}")
        return False

def emergency_service_killer(service_name):
    """
    Nuclear option - kill the service using every method available
    """
    print(f"Attempting emergency cleanup of {service_name}...")
    success = False
    
    try:
        # 1. Try SC.exe delete
        try:
            print("Trying SC DELETE command...")
            subprocess.run(["sc", "delete", service_name], check=False, capture_output=True)
        except:
            pass
            
        # 2. Kill NSSM processes
        killed = False
        print("Looking for NSSM processes...")
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if 'nssm' in proc.info['name'].lower():
                    cmdline = " ".join(proc.info['cmdline']) if proc.info['cmdline'] else ""
                    print(f"Found NSSM process: {proc.pid} - {cmdline}")
                    # If this is related to our service or we're being aggressive
                    if service_name.lower() in cmdline.lower() or 'lyra' in cmdline.lower():
                        print(f"Killing process {proc.pid}")
                        try:
                            proc.kill()
                            killed = True
                        except:
                            print(f"Failed to kill process, may need manual intervention")
            except:
                continue
                
        if killed:
            print("Successfully killed NSSM processes")
            success = True
            
        # 3. Registry cleanup
        if sys.platform == 'win32':
            try:
                import winreg
                service_key = f"SYSTEM\\CurrentControlSet\\Services\\{service_name}"
                
                try:
                    print(f"Checking registry key: {service_key}")
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, service_key, 0, winreg.KEY_READ)
                    winreg.CloseKey(key)
                    
                    # Key exists, try to delete it
                    print("Found registry key, attempting deletion...")
                    # This requires admin rights so might fail
                    try:
                        subprocess.run(["reg", "delete", f"HKLM\\{service_key}", "/f"], check=False)
                        print("Registry cleanup attempted")
                        success = True
                    except:
                        print("Could not delete registry key, may need manual cleanup")
                except:
                    print("Service key not found in registry")
            except:
                print("Registry checks failed")
    except Exception as e:
        print(f"Error during emergency cleanup: {e}")
    
    return success

def main():
    parser = argparse.ArgumentParser(description='Manage Lyra services and instances')
    parser.add_argument('action', nargs='?', 
                      choices=['start', 'stop', 'restart', 'status', 'focus', 'service', 'interactive',
                              'install-service', 'uninstall-service', 'kill', 'emergency-kill'],
                      default='interactive', help='Action to perform')
    
    args = parser.parse_args()
    
    # Check if pywin32 is installed
    if sys.platform == 'win32':
        try:
            import win32serviceutil
        except ImportError:
            print("WARNING: pywin32 is not installed. Windows service management functionality is limited.")
            print("To enable full functionality, install pywin32: pip install pywin32")
            print()
    
    if args.action == 'interactive':
        # Interactive menu
        while True:
            print("\nLyra Service Manager")
            print("===================")
            print("1. View status of all Lyra instances")
            print("2. Stop all Lyra instances")
            print("3. Start Lyra tray application")
            print("4. Focus existing Lyra window")
            if sys.platform == 'win32':
                print("5. Manage Lyra Windows service")
                print("6. Install Lyra as a Windows service")
                print("7. Forcefully kill all Lyra processes")
            print("0. Exit")
            
            choice = input("\nEnter choice: ").strip()
            
            if choice == "1":
                processes = find_lyra_processes()
                if processes:
                    print(f"\nFound {len(processes)} Lyra instances:")
                    for i, proc in enumerate(processes):
                        if proc['type'] == 'service':
                            print(f"{i+1}. Windows Service: {proc['name']} - {proc['state']} - {proc['binary_path']}")
                        else:
                            print(f"{i+1}. Process: PID {proc['pid']} - {proc['name']} - {proc['cmdline']}")
                else:
                    print("No Lyra processes or services found.")
                    
                socket_running = check_instance_running()
                if socket_running:
                    print("\nLyra tray application is running and accepting connections.")
                else:
                    print("\nNo Lyra tray application detected on the expected port.")
            elif choice == "2":
                stop_all_instances()
            elif choice == "3":
                if check_instance_running():
                    print("Lyra is already running. Use option 4 to bring it to the foreground.")
                else:
                    start_lyra_tray()
            elif choice == "4":
                if focus_running_instance():
                    print("Sent request to focus Lyra window.")
                else:
                    print("Failed to focus Lyra window. Is it running?")
            elif choice == "5" and sys.platform == 'win32':
                manage_windows_service()
            elif choice == "6" and sys.platform == 'win32':
                install_as_service()
            elif choice == "7" and sys.platform == 'win32':
                if force_kill_service_processes(LYRA_SERVICE_NAME):
                    print("Successfully killed Lyra processes.")
                else:
                    print("No Lyra processes found or couldn't kill them all.")
            elif choice == "0":
                break
            else:
                print("Invalid choice. Please try again.")
            
            input("\nPress Enter to continue...")
    
    elif args.action == 'status':
        processes = find_lyra_processes()
        if processes:
            print(f"Found {len(processes)} Lyra instances:")
            for i, proc in enumerate(processes):
                if proc['type'] == 'service':
                    print(f"{i+1}. Windows Service: {proc['name']} - {proc['state']} - {proc['binary_path']}")
                else:
                    print(f"{i+1}. Process: PID {proc['pid']} - {proc['name']} - {proc['cmdline']}")
        else:
            print("No Lyra processes or services found.")
            
        socket_running = check_instance_running()
        if socket_running:
            print("Lyra tray application is running and accepting connections.")
        else:
            print("No Lyra tray application detected on the expected port.")
            
    elif args.action == 'stop':
        stop_all_instances()
        
    elif args.action == 'start':
        if check_instance_running():
            print("Lyra is already running. Use 'focus' to bring it to the foreground.")
        else:
            start_lyra_tray()
            
    elif args.action == 'restart':
        restart_lyra_tray()
        
    elif args.action == 'focus':
        if focus_running_instance():
            print("Sent request to focus Lyra window.")
        else:
            print("Failed to focus Lyra window. Is it running?")
            
    elif args.action == 'service' and sys.platform == 'win32':
        manage_windows_service()
    
    elif args.action == 'install-service' and sys.platform == 'win32':
        install_as_service()
    
    elif args.action == 'uninstall-service' and sys.platform == 'win32':
        # First stop the service
        stop_windows_service(LYRA_SERVICE_NAME)
        # Then remove it
        remove_windows_service(LYRA_SERVICE_NAME)
        
    elif args.action == 'kill' and sys.platform == 'win32':
        force_kill_service_processes(LYRA_SERVICE_NAME)
    
    elif args.action == 'emergency-kill' and sys.platform == 'win32':
        print("WARNING: Emergency kill will attempt to forcefully remove the service")
        print("This is a last resort when normal methods fail")
        confirm = input("Continue? (y/n): ").strip().lower()
        if confirm == 'y':
            emergency_service_killer(LYRA_SERVICE_NAME)
        else:
            print("Operation cancelled")

if __name__ == "__main__":
    main()
