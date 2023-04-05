import os
import random
from PyQt5 import QtWidgets, QtGui, QtCore
import base64
import requests
import validators

last_loaded_image = None


def update_samplers():
    url = api_endpoint.text().rstrip('/')
    try:
        response = requests.get(url + "/sdapi/v1/samplers")
        samplers = response.json()
        dropdown.clear()
        updated_samplers = []
        for sampler in samplers:
            updated_samplers.append(sampler["name"])
        dropdown.addItems(updated_samplers)
        dropdown.setCurrentIndex(0)
        QtWidgets.QMessageBox.information(window, "Success", "Samplers updated successfully")
    except requests.exceptions.RequestException:
        QtWidgets.QMessageBox.warning(window, "Error", "Invalid API endpoint")


def save_image():
    # Get the image from the bottom_right_section_label
    pixmap = bottom_right_section_label.pixmap()
    if not pixmap:
        QtWidgets.QMessageBox.warning(window, "Warning", "No image to save")
        return

    # Prompt the user for a file name and location
    file_name, _ = QtWidgets.QFileDialog.getSaveFileName(window, "Save Image", "", "Images (*.png *.jpg)")

    # Save the image to the selected file
    if file_name:
        pixmap.save(file_name)


def display_image(image_base64):
    # Convert the base64 encoded string to a QByteArray
    image_data = QtCore.QByteArray.fromBase64(image_base64.encode("utf-8"))

    # Create a QPixmap from the QByteArray
    pixmap = QtGui.QPixmap()
    pixmap.loadFromData(image_data)

    # Set the pixmap of the label in the bottom right section
    bottom_right_section_label.setPixmap(pixmap)


def generate_image():
    # Get the API endpoint from the QLineEdit widget
    api_endpoint_value = api_endpoint.text().rstrip('/')

    # Get the image from the bottom_left_section_label
    pixmap = bottom_left_section_label.pixmap()
    if not pixmap:
        QtWidgets.QMessageBox.warning(window, "Warning", "No image loaded")
        return
    if not validators.url(api_endpoint_value):
        QtWidgets.QMessageBox.warning(window, "Warning", "Please enter valid api end point")
        return
    url = api_endpoint_value + "/controlnet/model_list"
    model_list = requests.get(url).json()
    model_name = ""
    for model in model_list['model_list']:
        if 'openpose' in model:
            model_name = model
            break

    if model_name == "":
        QtWidgets.QMessageBox.warning(window, "Warning", "Openpose controlnet not detected")
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
    prompt_value = prompt.text()
    negative_prompt_value = negative_prompt.text()
    cfg_scale_value = cfg_scale.value()
    dropdown_value = dropdown.currentText()
    steps_value = steps.value()
    restore_face_value = checkbox.isChecked()
    # Create the data for the POST request
    data = {
        "prompt": prompt_value,
        "negative_prompt": negative_prompt_value,
        "cfg_scale": cfg_scale_value,
        "steps": steps_value,
        "width": image_width,
        "height": image_height,
        "sampler_name": dropdown_value,
        "sampler_index": dropdown_value,
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
    generate_image_button.setEnabled(False)
    # Make the POST request to the API endpoint
    response = requests.post(api_endpoint_value + "/sdapi/v1/txt2img", json=data).json()

    display_image(str(response["images"][0]))

    generate_image_button.setEnabled(True)


def browse_folder():
    folder_path = QtWidgets.QFileDialog.getExistingDirectory()
    if folder_path:
        folder_path_label.setText(folder_path)


def load_random_image():
    global last_loaded_image
    folder_path = folder_path_label.text()
    if not folder_path:
        QtWidgets.QMessageBox.warning(window, "Warning", "Please select a folder first")
        return

    image_extensions = [".png", ".jpg", ".jpeg"]
    image_files = [f for f in os.listdir(folder_path) if f.endswith(tuple(image_extensions))]
    if not image_files:
        QtWidgets.QMessageBox.warning(window, "Warning", "No image files found in the selected folder")
        return

    if len(image_files) > 1 and last_loaded_image in image_files:
        image_files.remove(last_loaded_image)

    random_image_file = random.choice(image_files)
    last_loaded_image = random_image_file
    random_image_path = os.path.join(folder_path, random_image_file)
    pixmap = QtGui.QPixmap(random_image_path)
    bottom_left_section_label.setPixmap(pixmap)


app = QtWidgets.QApplication([])

window = QtWidgets.QWidget()
window.setWindowTitle("Random Pose Generator by Controlnetposes.com")
layout = QtWidgets.QVBoxLayout()

top_section = QtWidgets.QFrame()
top_section.setFixedHeight(260)
bottom_section = QtWidgets.QFrame()

top_layout = QtWidgets.QHBoxLayout()
left_side = QtWidgets.QFrame()
right_side = QtWidgets.QFrame()

left_layout = QtWidgets.QVBoxLayout()
browse_folder_button = QtWidgets.QPushButton("Browse Folder Containing Poses")
browse_folder_button.setStyleSheet("background-color: blue; color: white;")
folder_path_label = QtWidgets.QLabel()

left_layout.addWidget(browse_folder_button)
left_layout.addWidget(folder_path_label)

form_layout = QtWidgets.QFormLayout()
api_endpoint = QtWidgets.QLineEdit()
api_endpoint.setText("Paste running instance url Automatic1111")
prompt = QtWidgets.QLineEdit()
negative_prompt = QtWidgets.QLineEdit()
cfg_scale = QtWidgets.QSpinBox()
cfg_scale.setValue(7)
checkbox = QtWidgets.QCheckBox()
steps = QtWidgets.QSpinBox()
steps.setValue(10)

dropdown = QtWidgets.QComboBox()
dropdown.addItems(["Euler a"])
dropdown.setCurrentIndex(0)

form_layout.addRow("API Endpoint:", api_endpoint)
form_layout.addRow("Prompt:", prompt)
form_layout.addRow("Negative Prompt:", negative_prompt)
form_layout.addRow("Cfg Scale:", cfg_scale)
form_layout.addRow("Steps:", steps)
form_layout.addRow("Restore Face:", checkbox)
form_layout.addRow("", dropdown)
fetch_latest_sampler_button = QtWidgets.QPushButton("Fetch Latest Samplers")
fetch_latest_sampler_button.clicked.connect(update_samplers)

sampler_layout = QtWidgets.QHBoxLayout()
sampler_layout.addWidget(dropdown, stretch=4)
sampler_layout.addWidget(fetch_latest_sampler_button, stretch=1)
form_layout.addRow("Sampler:", sampler_layout)


left_layout.addLayout(form_layout)

left_side.setLayout(left_layout)

right_layout = QtWidgets.QVBoxLayout()


load_random_image_button = QtWidgets.QPushButton("Load Random Image")
generate_image_button = QtWidgets.QPushButton("Generate Image")
generate_image_button.clicked.connect(generate_image)
right_layout.addWidget(load_random_image_button)
right_layout.addWidget(generate_image_button)
hint_label = QtWidgets.QLabel("Once Generate Image is clicked, please wait for the image to be generated. You can "
                              "check progress in console.")
right_layout.addWidget(hint_label)
# Connect the clicked signal of the save_image_button to the save_image function
save_image_button = QtWidgets.QPushButton("Save Image")
right_layout.addWidget(save_image_button)
save_image_button.clicked.connect(save_image)

right_side.setLayout(right_layout)

top_layout.addWidget(left_side, 80)
top_layout.addWidget(right_side, 20)

top_section.setLayout(top_layout)

bottom_layout = QtWidgets.QHBoxLayout()
bottom_left_section = QtWidgets.QFrame()
bottom_right_section = QtWidgets.QFrame()

bottom_left_layout = QtWidgets.QVBoxLayout()
bottom_left_section_label = QtWidgets.QLabel()
bottom_left_layout.addWidget(bottom_left_section_label)
bottom_left_section.setLayout(bottom_left_layout)

bottom_right_layout = QtWidgets.QVBoxLayout()
bottom_right_section_label = QtWidgets.QLabel()
bottom_right_layout.addWidget(bottom_right_section_label)
bottom_right_section.setLayout(bottom_right_layout)

bottom_layout.addWidget(bottom_left_section)
bottom_layout.addWidget(bottom_right_section)

bottom_section.setLayout(bottom_layout)

layout.addWidget(top_section)
layout.addWidget(bottom_section)

window.setLayout(layout)

screen_size = QtWidgets.QDesktopWidget().screenGeometry()
window_width = int(screen_size.width() * 0.8)
window.resize(window_width, window.sizeHint().height())

browse_folder_button.clicked.connect(browse_folder)
load_random_image_button.clicked.connect(load_random_image)
window.showMaximized()
app.exec_()
