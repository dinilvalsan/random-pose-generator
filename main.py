import random
from PyQt5 import QtWidgets, QtGui, QtCore
import base64
import requests
import validators
import os
from PyQt5.QtWidgets import QMessageBox
import configparser
import re
from PIL import Image
import io




def is_valid_folder(folder_path):
    filenames = os.listdir(folder_path)
    if 'negative_prompt.txt' not in filenames:
        QtWidgets.QMessageBox.warning(window, "Warning", f'Alert: Folder does not contain negative_prompt.txt')
        return False
    for filename in filenames:
        if filename == 'negative_prompt.txt':
            continue
        if not re.match(r'^\d+_(comma|blank).*\.txt$', filename):
            QtWidgets.QMessageBox.warning(window, "Warning",
                                          f'Alert: Folder contains non-supported filenames: {filename}')
            return False
    return True


def get_random_lines_from_files(current_folder_context):
    lines = {}
    folder_path = os.path.join(data_dir, current_folder_context)
    if not is_valid_folder(folder_path):
        return lines
    filenames = os.listdir(folder_path)
    filenames.sort(key=lambda x: (int(x.split('_')[0]) if x[0].isdigit() else float('inf'), x))
    for filename in filenames:
        if filename == 'negative_prompt.txt':
            continue
        with open(os.path.join(folder_path, filename), 'r') as f:
            file_lines = [line.strip() for line in f.readlines() if line.strip()]
            if file_lines:
                lines[filename] = random.choice(file_lines)
            else:
                lines[filename] = None
    if not lines:
        QtWidgets.QMessageBox.warning(window, "Warning",
                                      f'Alert: Folder does not contain randomizer txt files')
    return lines


def get_prompt():
    prompt = ''
    negative_prompt = ''
    if not get_right_list_values():
        QtWidgets.QMessageBox.warning(window, "Warning", "Please select atleast one prompt data folder")
    else:
        current_folder_context = random.choice(get_right_list_values()).rstrip()
        lines = get_random_lines_from_files(current_folder_context)
        if lines:
            for filename, line in lines.items():
                if 'comma' in filename:
                    prompt += line + ', '
                elif 'blank' in filename:
                    prompt += line + ' '

            prompt = prompt.strip().rstrip(',')

            with open(os.path.join(data_dir, current_folder_context, 'negative_prompt.txt'), 'r') as f:
                negative_prompt = f.read().strip()
    return prompt, negative_prompt


def generate_image():

    folder_path = folder_path_label.text()
    if not folder_path:
        QtWidgets.QMessageBox.warning(window, "Warning", "Please select a controlnet images folder first")
        return

    image_extensions = [".png", ".jpg", ".jpeg"]
    image_files = [f for f in os.listdir(folder_path) if f.endswith(tuple(image_extensions))]
    if not image_files:
        QtWidgets.QMessageBox.warning(window, "Warning", "No image files found in the selected folder")
        return

    sampler_value = sampler_dropdown.currentText()
    model_name = controlnet_dropdown.currentText()
    prompt, negative_prompt = get_prompt()

    if prompt == '':
        return

    if not model_name:
        QtWidgets.QMessageBox.warning(window, "Warning", "Please select a controlnet model")
        return

    if not sampler_value:
        QtWidgets.QMessageBox.warning(window, "Warning", "Please select a sampler")
        return

    if len(image_files):
        generate_image_button.setEnabled(False)
        generation_success = True

        for n in range(len(image_files)):
            if not generation_success:
                break
            prompt, negative_prompt = get_prompt()
            current_image_path = os.path.join(folder_path, image_files[n])

            # Get the API endpoint from the QLineEdit widget
            api_endpoint_value = api_endpoint.text().rstrip('/')
            pixmap = QtGui.QPixmap(current_image_path)
            if not pixmap:
                QtWidgets.QMessageBox.warning(window, "Warning", "No image loaded")
                return
            if not validators.url(api_endpoint_value):
                QtWidgets.QMessageBox.warning(window, "Warning", "Please enter valid api end point")
                return
            # Get the width and height of the image
            image_width = pixmap.width()
            image_height = pixmap.height()
            # Convert the QPixmap to a QImage and then to a base64 encoded string
            qimage = pixmap.toImage()
            byte_array = QtCore.QByteArray()
            buffer = QtCore.QBuffer(byte_array)
            qimage.save(buffer, "PNG")
            image_base64 = base64.b64encode(byte_array.data()).decode("utf-8")

            # Get the values from the other form widgets
            cfg_scale_value = cfg_scale.value()
            steps_value = steps.value()
            restore_face_value = restore_face.isChecked()
            save_generated_prompts_value = save_generated_prompts.isChecked()

            # Create the data for the POST request
            data = {
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "cfg_scale": cfg_scale_value,
                "steps": steps_value,
                "width": image_width,
                "height": image_height,
                "sampler_name": sampler_value,
                "sampler_index": sampler_value,
                "restore_faces": restore_face_value,
                "alwayson_scripts": {
                    "controlnet": {
                        "args": [
                            {
                                "input_image": image_base64,
                                "module": "none",
                                "model": model_name
                            }
                        ]
                    }
                }
            }

            # Make the POST request to the API endpoint
            try:
                response = requests.post(api_endpoint_value + "/sdapi/v1/txt2img", json=data).json()
                generated_folder_path = os.path.join(folder_path, "generated")
                if not os.path.exists(generated_folder_path):
                    os.makedirs(generated_folder_path)
                if not os.path.exists(generated_folder_path):
                    os.makedirs(generated_folder_path)

                try:
                    file_content = base64.b64decode(response["images"][0])
                    # create an image object from the decoded data
                    image = Image.open(io.BytesIO(file_content))

                    # generate a filename using the index variable
                    filename, file_extension = os.path.splitext(image_files[n])
                    if generation_filename_suffix.text():
                        filename = f"{filename}_{generation_filename_suffix.text()}.{image_extension}"
                    else:
                        filename = f"{filename}_preview.{image_extension}"

                    # save the image using the settings from the config file or the default values
                    image.save(os.path.join(generated_folder_path, filename), image_format, quality=image_quality)
                except Exception as e:
                    print(str(e))
                if save_generated_prompts_value:
                    # generate a filename using the index variable
                    filename, file_extension = os.path.splitext(image_files[n])
                    if generation_filename_suffix.text():
                        filename = f"{filename}_prompt_{generation_filename_suffix.text()}.txt"
                    else:
                        filename = f"{filename}_prompt.txt"
                    with open(os.path.join(generated_folder_path, filename), "w") as fh:
                        try:
                            file_content = prompt
                            fh.write(file_content)
                        except Exception as e:
                            print(str(e))

                with open(os.path.join(generated_folder_path, image_files[n]), "wb") as fh:
                    try:
                        file_content = base64.b64decode(response["images"][1])
                        fh.write(file_content)
                    except Exception as e:
                        print(str(e))
                if os.path.exists(current_image_path):
                    os.remove(current_image_path)
            except Exception as e:
                msg_box = QMessageBox()
                msg_box.setIcon(QMessageBox.Warning)
                msg_box.setText("An error occurred. Please check the automatic console for more info.")
                msg_box.setStandardButtons(QMessageBox.Retry | QMessageBox.Ok)
                msg_box_return_value = msg_box.exec()
                generation_success = False
                if msg_box_return_value == QMessageBox.Retry:
                    generate_image()
                else:
                    break
        if generation_success:
            QtWidgets.QMessageBox.information(window, "Success", "All images generated")
        generate_image_button.setEnabled(True)
    else:
        QtWidgets.QMessageBox.warning(window, "Error", "No images in folder")


def get_right_list_values():
    values = []
    for index in range(right_list.count()):
        values.append(right_list.item(index).text())
    return values


def update_samplers():
    url = api_endpoint.text().rstrip('/')
    try:
        response = requests.get(url + "/sdapi/v1/samplers")
        samplers = response.json()
        sampler_dropdown.clear()
        updated_samplers = []
        for sampler in samplers:
            updated_samplers.append(sampler["name"])
        sampler_dropdown.addItems(updated_samplers)
        sampler_dropdown.setCurrentIndex(0)
        QtWidgets.QMessageBox.information(window, "Success", "Samplers updated successfully")
    except requests.exceptions.RequestException:
        QtWidgets.QMessageBox.warning(window, "Error", "Invalid API endpoint")


def update_controlnet_models():
    url = api_endpoint.text().rstrip('/')
    try:
        response = requests.get(url + "/controlnet/model_list")
        models = response.json()
        controlnet_dropdown.clear()
        updated_models = []
        for model in models['model_list']:
            updated_models.append(model)
        controlnet_dropdown.addItems(updated_models)
        controlnet_dropdown.setCurrentIndex(0)
        QtWidgets.QMessageBox.information(window, "Success", "Controlnet models updated successfully")
    except requests.exceptions.RequestException:
        QtWidgets.QMessageBox.warning(window, "Error", "Invalid API endpoint")


def browse_folder():
    folder_path = QtWidgets.QFileDialog.getExistingDirectory()
    if folder_path:
        folder_path_label.setText(folder_path)


def move_item_to_right():
    for item in left_list.selectedItems():
        right_list.addItem(item.text())
        left_list.takeItem(left_list.row(item))


def move_item_to_left():
    for item in right_list.selectedItems():
        left_list.addItem(item.text())
        right_list.takeItem(right_list.row(item))


def get_random_prompt_sample():
    prompt, negative_prompt = get_prompt()
    output_label.setText(f'Prompt: {prompt}\nNegative Prompt: {negative_prompt}')


app = QtWidgets.QApplication([])
window = QtWidgets.QWidget()
window.setWindowTitle("Batch processing by Controlnetposes.com")
layout = QtWidgets.QVBoxLayout()

form_layout = QtWidgets.QFormLayout()

config = configparser.ConfigParser()
config.read('config.ini')
running_instance_url = config.get('Settings', 'running_instance_url')
# set default values for the image format and quality
default_format = 'JPEG'
default_quality = 75

# try to read the image format and quality settings from the config file
try:
    image_format = config.get('ImageSettings', 'format')
    if image_format not in ['JPEG', 'PNG']:
        msg = f"Invalid format: {image_format}. Using default format: {default_format}"
        QtWidgets.QMessageBox.warning(None, "Invalid Format", msg)
        image_format = default_format
except (configparser.NoSectionError, configparser.NoOptionError):
    msg = f"Format not found in config file. Using default format: {default_format}"
    QtWidgets.QMessageBox.warning(None, "Format Not Found", msg)
    image_format = default_format

try:
    image_quality = config.getint('ImageSettings', 'quality')
    if image_format == 'JPEG' and not (1 <= image_quality <= 95):
        msg = f"Invalid quality for JPEG: {image_quality}. Using default quality: {default_quality}"
        QtWidgets.QMessageBox.warning(None, "Invalid Quality", msg)
        image_quality = default_quality
    elif image_format == 'PNG' and not (1 <= image_quality <= 9):
        msg = f"Invalid quality for PNG: {image_quality}. Using default quality: {default_quality}"
        QtWidgets.QMessageBox.warning(None, "Invalid Quality", msg)
        image_quality = default_quality
except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
    msg = f"Quality not found or invalid in config file. Using default quality: {default_quality}"
    QtWidgets.QMessageBox.warning(None, "Quality Not Found or Invalid", msg)
    image_quality = default_quality

# infer the image extension from the image format
if image_format == 'JPEG':
    image_extension = 'jpg'
elif image_format == 'PNG':
    image_extension = 'png'
else:
    # default to jpg if the format is not recognized
    image_extension = 'jpg'


api_endpoint = QtWidgets.QLineEdit()
api_endpoint.setText(running_instance_url)
api_endpoint.setFixedWidth(500)
form_layout.addRow("API Endpoint:", api_endpoint)

browse_folder_button = QtWidgets.QPushButton("Browse Folder Containing Controlnet Input Images")
browse_folder_button.setStyleSheet("background-color: blue; color: white;")
browse_folder_button.setFixedWidth(500)
folder_path_label = QtWidgets.QLabel()
form_layout.addRow("Select Folder:", browse_folder_button)
form_layout.addRow(folder_path_label)
browse_folder_button.clicked.connect(browse_folder)

cfg_scale = QtWidgets.QSpinBox()
cfg_scale.setValue(7)
cfg_scale.setFixedWidth(250)
form_layout.addRow("Cfg Scale:", cfg_scale)

steps = QtWidgets.QSpinBox()
steps.setValue(10)
steps.setFixedWidth(250)
form_layout.addRow("Steps:", steps)

restore_face = QtWidgets.QCheckBox()
form_layout.addRow("Restore Face:", restore_face)

save_generated_prompts = QtWidgets.QCheckBox()
form_layout.addRow("Save prompts (batch processing):", save_generated_prompts)

sampler_dropdown = QtWidgets.QComboBox()
sampler_dropdown.setFixedWidth(250)
sampler_dropdown.addItems([""])

fetch_latest_sampler_button = QtWidgets.QPushButton("Fetch Samplers")
fetch_latest_sampler_button.setFixedWidth(250)
fetch_latest_sampler_button.clicked.connect(update_samplers)

sampler_layout = QtWidgets.QHBoxLayout()
sampler_layout.addWidget(sampler_dropdown, stretch=4)
sampler_layout.addWidget(fetch_latest_sampler_button, stretch=1)

form_layout.addRow("Sampler:", sampler_layout)

controlnet_dropdown = QtWidgets.QComboBox()
controlnet_dropdown.setFixedWidth(250)
controlnet_dropdown.addItems([""])

fetch_latest_controlnet_button = QtWidgets.QPushButton("Fetch Controlnet Models")
fetch_latest_controlnet_button.setFixedWidth(250)
fetch_latest_controlnet_button.clicked.connect(update_controlnet_models)

controlnet_layout = QtWidgets.QHBoxLayout()
controlnet_layout.addWidget(controlnet_dropdown, stretch=4)
controlnet_layout.addWidget(fetch_latest_controlnet_button, stretch=1)

form_layout.addRow("Controlnet Model:", controlnet_layout)

data_dir = './data'

if not os.path.exists(data_dir):
    msg_box = QtWidgets.QMessageBox()
    msg_box.setIcon(QtWidgets.QMessageBox.Warning)
    msg_box.setText("Folder named 'data' must exist.")
    msg_box.setStandardButtons(QtWidgets.QMessageBox.Ok)
    return_value = msg_box.exec()
    if return_value == QtWidgets.QMessageBox.Ok:
        app.quit()

sub_folders = [name for name in os.listdir(data_dir) if os.path.isdir(os.path.join(data_dir, name))]

left_label = QtWidgets.QLabel('Available prompt configs')
left_list = QtWidgets.QListWidget()
left_list.addItems(sub_folders)
left_list.itemDoubleClicked.connect(move_item_to_right)

right_label = QtWidgets.QLabel('Selected prompt config for generation')
right_list = QtWidgets.QListWidget()
right_list.itemDoubleClicked.connect(move_item_to_left)

sub_layout = QtWidgets.QGridLayout()
sub_layout.addWidget(left_label, 0, 0)
sub_layout.addWidget(left_list, 1, 0)
sub_layout.addWidget(right_label, 0, 1)
sub_layout.addWidget(right_list, 1, 1)

form_layout.addRow(sub_layout)

prompt_layout = QtWidgets.QHBoxLayout()

output_label = QtWidgets.QLabel('Output string')
output_label.setWordWrap(True)
test_random_prompt_button = QtWidgets.QPushButton('Test random prompt generation')
test_random_prompt_button.clicked.connect(get_random_prompt_sample)
prompt_layout.addWidget(test_random_prompt_button, stretch=1)
prompt_layout.addWidget(output_label, stretch=3)

form_layout.addRow(prompt_layout)

generation_filename_suffix = QtWidgets.QLineEdit()
generation_filename_suffix.setText("")
generation_filename_suffix.setFixedWidth(500)
form_layout.addRow("Generation file name suffix:", generation_filename_suffix)

generate_image_button = QtWidgets.QPushButton("Generate Images")
generate_image_button.clicked.connect(generate_image)
form_layout.addRow(generate_image_button)

layout.addLayout(form_layout)

window.setLayout(layout)

screen_size = QtWidgets.QDesktopWidget().screenGeometry()
window_width = int(screen_size.width() * 0.5)
window.resize(window_width, 500)

window.show()
app.exec_()
