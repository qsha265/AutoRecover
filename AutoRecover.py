import subprocess
import os
import time
import logging
from enum import Enum

class PreChecker:
    @staticmethod
    def root_user_check():
        user_info = subprocess.run("whoami", shell=True, stdout=subprocess.PIPE, text=True).stdout.strip()
        if user_info == "root":
            print("Root user check: Successful")
        else:
            print("Root user check: Failed. Current version only supports root user.")
            exit()
    @staticmethod
    def recovery_tools_check(tool_list):
        for tool in tool_list:
            tool_command = PreChecker.check_tool_installation_command(tool)
            tool_info = subprocess.run(tool_command, shell=True, stdout=subprocess.PIPE, text=True).stdout
            if "command not found" not in tool_info:
                print(f"{tool.name} is installed.")
            else:
                print(f"{tool.name} is not installed.")
                exit()
    @staticmethod
    def check_tool_installation_command(tool):
        command = {
            ForensicsTool.foremost: "foremost -version",
            ForensicsTool.scalpel: "scalpel -v"
        }
        return command.get(tool)

class ForensicsTool(Enum):
    foremost = 1
    scalpel = 1

# Pre-check
print("Pre-check:")
PreChecker.root_user_check()
tool_list = [ForensicsTool.foremost, ForensicsTool.scalpel]
PreChecker.recovery_tools_check(tool_list)
print("Pre-check is completed.")
print('\n')

# Get user information, and create path for the file locations
user_name = input("Please enter your name: ")
case_id = input("Please enter the case id: ")
log_file_name = "/process.log"
file_path = f"/root/Documents/{user_name}_{case_id}"
try:
    os.makedirs(file_path)
    print(f"Directory {file_path} created successfully")
except OSError as error:
    print(f"Directory {file_path} can not be created. Error: {error}")
    exit()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', filename=file_path+log_file_name, filemode='a')

# Hash the USB drive
print("The automated file recovery process is started.")
start_time = time.time()
logging.info("The automated file recovery process is started.")
logging.info(f"Starting time: {start_time}")
home_directory = os.path.expanduser("~")
os.chdir(home_directory)
logging.info("Move to home directory.")
hash_usb_command = "sha256sum /dev/sdb"
usb_drive_hash = subprocess.run(hash_usb_command, shell=True, stdout=subprocess.PIPE, text=True).stdout
logging.info(f"Execute command: {hash_usb_command}")
print("USB drive is hashed.")
logging.info("USB drive hashing is completed.")
hash_value_file = file_path + "/hash_values.txt"
with open(hash_value_file, 'w') as file:
    file.writelines(usb_drive_hash)
drive_hash = usb_drive_hash.split(' ')[0]
print(drive_hash)
print(f"Hash value added to {hash_value_file}")
logging.info(f"USB drive hash values is saved to {hash_value_file}.")

# Image the USB drive
dd_path = f"{file_path}/{case_id}.dd"
image_command = f"dd if=/dev/sdb of={dd_path}"
completed_process = subprocess.run(image_command, shell=True, stdout=subprocess.PIPE, text=True)
logging.info(f"Execute command: {image_command}")
print(completed_process.stdout)
logging.info("USB drive image copying is completed.")

# Hash the USB image copy
hash_image_command = f"sha256sum {dd_path}"
usb_drive_hash = subprocess.run(hash_image_command, shell=True, stdout=subprocess.PIPE, text=True).stdout
logging.info(f"Execute command: {hash_image_command}")
print("USB image copy is hashed.")
with open(hash_value_file, 'a') as file:
    file.writelines(usb_drive_hash)
image_hash = usb_drive_hash.split(' ')[0]
print(image_hash)
logging.info("USB image hashing is completed.")
print(f"Hash value added to {hash_value_file}")
print('\n')
logging.info(f"USB image hash values is saved to {hash_value_file}.")

# Compare hash
if drive_hash == image_hash:
    print("Drive and image hash values match.")
    logging.info("USB drive and image hash values match.")
else:
    print("Drive and image hash values do not match.")
    logging.info("USB drive and image hash values are mismatching.")
    exit()

# Foremost
foremost_execution = f"foremost {dd_path} -o {file_path}/foremost"
subprocess.run(foremost_execution, shell=True, stdout=subprocess.PIPE, text=True)
logging.info(f"Execute command: {foremost_execution}")
print("Foremost recovery is completed.")
logging.info("Foremost recovery is completed.")

# Scalpel
scalpel_execution = f"scalpel {dd_path} -o {file_path}/scalpel"
subprocess.run(scalpel_execution, shell=True, stdout=subprocess.PIPE, text=True)
logging.info(f"Execute command: {scalpel_execution}")
print("Scalpel recovery is completed.")
logging.info("Scalpel recovery is completed.")

# Report Generation


end_time = time.time()
logging.info(f"Ending time: {end_time}")
duration = end_time - start_time
logging.info(f"Process duration: {duration}")
