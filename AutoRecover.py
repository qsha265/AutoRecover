import subprocess
import os
import time
import logging
import pexpect
import plotly.graph_objects as go
from collections import defaultdict
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
            ForensicsTool.scalpel: "scalpel -v",
            ForensicsTool.photorec: "photorec -v"
        }
        return command.get(tool)

class ForensicsTool(Enum):
    foremost = 1
    scalpel = 2,
    photorec = 3

# Pre-check
print("Pre-check:")
PreChecker.root_user_check()
tool_list = [ForensicsTool.foremost, ForensicsTool.scalpel, ForensicsTool.photorec]
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
logging.info(f"Executing command: {hash_usb_command}")
usb_drive_hash = subprocess.run(hash_usb_command, shell=True, stdout=subprocess.PIPE, text=True).stdout
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
logging.info(f"Executing command: {image_command}")
completed_process = subprocess.run(image_command, shell=True, stdout=subprocess.PIPE, text=True)
print(completed_process.stdout)
logging.info("USB drive image copying is completed.")

# Hash the USB image copy
hash_image_command = f"sha256sum {dd_path}"
logging.info(f"Executing command: {hash_image_command}")
usb_drive_hash = subprocess.run(hash_image_command, shell=True, stdout=subprocess.PIPE, text=True).stdout
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
logging.info(f"Executing command: {foremost_execution}")
try:
    subprocess.run(foremost_execution, shell=True, stdout=subprocess.PIPE, check=True)
except subprocess.CalledProcessError:
    print("Foremost execution failed!")
    logging.info("Foremost recovery is failed.")
print("Foremost recovery is completed.")
logging.info("Foremost recovery is completed.")

# Scalpel
scalpel_execution = f"scalpel {dd_path} -o {file_path}/scalpel"
logging.info(f"Executing command: {scalpel_execution}")
try:
    subprocess.run(scalpel_execution, shell=True, stdout=subprocess.PIPE, check=True)
except subprocess.CalledProcessError:
    print("Scalpel execution failed!")
    logging.info("Scalpel recovery is failed.")
print("Scalpel recovery is completed.")
logging.info("Scalpel recovery is completed.")

# Photorec
photorec_path = f"{file_path}/photorec"
os.makedirs(photorec_path)
os.chdir(photorec_path)
logging.info(f"Photorec recovery is started...")
child = pexpect.spawn(f'photorec {dd_path}')
child.expect('Proceed')
child.sendline('')
child.expect('Search')
child.sendline('')
child.expect('Other')
child.sendline('')
child.expect('Free')
child.sendline('2\r')
child.send('c')
child.expect('Quit')
child.sendline('')
child.sendintr()
child.expect(pexpect.EOF)
logging.info(f"Photorec recovery is completed.")

# Report Generation
def list_files(file_path):
    """List all child files in the given path."""
    for dirpath, _, filenames in os.walk(file_path):
        for filename in filenames:
            yield os.path.join(dirpath, filename)

def categorize_files(file_list):
    """Categorize files based on their names and extensions."""
    file_types = set()
    counts = {
        "foremost": defaultdict(int),
        "scalpel": defaultdict(int),
        "recup": defaultdict(int)
    }

    for file in file_list:
        base_name = os.path.basename(file.strip())
        file_name, extension = os.path.splitext(base_name)
        extension = extension.lstrip('.')

        if file_name not in ('audit', 'photorec', 'report'):
            file_types.add(extension)
            if 'foremost' in file:
                counts["foremost"][extension] += 1
            elif 'scalpel' in file:
                counts["scalpel"][extension] += 1
            elif 'recup' in file:
                counts["recup"][extension] += 1

    return file_types, counts

file_list = list_files(file_path)
file_types, counts = categorize_files(file_list)

for category, count_dict in counts.items():
    for file_type in file_types:
        count_dict[file_type] += 0

output_counts = {category: dict(count_dict) for category, count_dict in counts.items()}
output_counts["foremost"]["Total"] = sum(output_counts["foremost"].values())
output_counts["scalpel"]["Total"] = sum(output_counts["scalpel"].values())
output_counts["recup"]["Total"] = sum(output_counts["recup"].values())
if "recup" in output_counts:
    output_counts["photorec"] = output_counts.pop("recup")

def dict_to_table(output_counts, chart_js):
    # Extract unique headers (which are the unique keys from the inner dictionaries)
    headers = sorted(set(key for subdict in output_counts.values() for key in subdict.keys()))

    # Construct the table headers
    table_headers = "<th>Key</th>" + "".join(f"<th>{header}</th>" for header in headers)

    # Construct the table rows based on the data
    table_rows = ""
    for key, subdict in output_counts.items():
        row_data = "".join(f"<td>{subdict.get(header, '')}</td>" for header in headers)
        table_rows += f"<tr><td>{key}</td>{row_data}</tr>"

    # HTML template with placeholders
    html_template = """
    <html>
    <head>
        <title>Case File Recovery Result</title>
    </head>
    <body>
        <table border="1">
            <thead>
                <tr>
                    {table_headers}
                </tr>
            </thead>
            <tbody>
                {table_rows}
            </tbody>
        </table>
        {chart_js}
        <div id="radar-chart"></div>
    </body>
    </html>
    """

    # Fill the placeholders with actual data
    return html_template.format(table_headers=table_headers, table_rows=table_rows, chart_js=chart_js)

categories = list(file_types)
foremost_value = []
scalpel_value = []
photorec_value = []
for category in categories:
    foremost_value.append(output_counts["foremost"][category])
    scalpel_value.append(output_counts["scalpel"][category])
    photorec_value.append(output_counts["photorec"][category])

fig = go.Figure()
fig.add_trace(go.Scatterpolar(
      r=foremost_value,
      theta=categories,
      fill='toself',
      name='foremost'
))
fig.add_trace(go.Scatterpolar(
      r=scalpel_value,
      theta=categories,
      fill='toself',
      name='scalpel'
))
fig.add_trace(go.Scatterpolar(
      r=photorec_value,
      theta=categories,
      fill='toself',
      name='photorec'
))
fig.update_layout(
  polar=dict(
    radialaxis=dict(
      visible=True,
      range=[0, 10]
    )),
  showlegend=True
)

chart_js = fig.to_html(full_html=False, include_plotlyjs='cdn')

# Get the HTML content
html_content = dict_to_table(output_counts, chart_js)

# Write the content to an HTML file
report_name = f"{case_id}Result.html"
with open(f"{file_path}/{report_name}", "w") as html_file:
    html_file.write(html_content)
logging.info(f"Report named {report_name} is generated.")

end_time = time.time()
logging.info(f"Ending time: {end_time}")
duration = end_time - start_time
logging.info(f"Process duration: {duration}")
