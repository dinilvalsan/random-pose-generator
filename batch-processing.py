import os
import random
from PyQt5 import QtWidgets, QtGui, QtCore
import base64
import requests
import validators
from PyQt5.QtWidgets import QMessageBox

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


def generate_image():
    hint_label.setText("")
    folder_path = folder_path_label.text()
    if not folder_path:
        QtWidgets.QMessageBox.warning(window, "Warning", "Please select a folder first")
        return

    image_extensions = [".png", ".jpg", ".jpeg"]
    image_files = [f for f in os.listdir(folder_path) if f.endswith(tuple(image_extensions))]
    if not image_files:
        QtWidgets.QMessageBox.warning(window, "Warning", "No image files found in the selected folder")
        return

    if len(image_files):
        generate_image_button.setEnabled(False)
        for n in range(len(image_files)):
            current_image_path = os.path.join(folder_path, image_files[n])

            # Get the API endpoint from the QLineEdit widget
            api_endpoint_value = api_endpoint.text().rstrip('/')

            # Get the image from the bottom_left_section_label
            pixmap = QtGui.QPixmap(current_image_path)
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

            # Make the POST request to the API endpoint
            try:
                response = requests.post(api_endpoint_value + "/sdapi/v1/txt2img", json=data).json()

                generated_folder_path = os.path.join(folder_path, "generated")

                if not os.path.exists(generated_folder_path):
                    os.makedirs(generated_folder_path)

                with open(generated_folder_path + "/output_" + image_files[n], "wb") as fh:
                    try:
                        file_content = base64.b64decode(response["images"][0])
                        fh.write(file_content)
                    except Exception as e:
                        print(str(e))
                with open(generated_folder_path + "/" + image_files[n], "wb") as fh:
                    try:
                        file_content = base64.b64decode(response["images"][1])
                        fh.write(file_content)
                    except Exception as e:
                        print(str(e))

                if os.path.exists(current_image_path):
                    os.remove(current_image_path)
            except Exception as e:
                hint_label.setText(str(e))
                msg_box = QMessageBox()
                msg_box.setIcon(QMessageBox.Warning)
                msg_box.setText("An error occurred, App will close. Please check for automatic 1111 console for more "
                                "info")
                msg_box.setStandardButtons(QMessageBox.Ok)
                return_value = msg_box.exec()
                if return_value == QMessageBox.Ok:
                    app.quit()
        QtWidgets.QMessageBox.information(window, "Success", "All images generated")
        generate_image_button.setEnabled(True)
    else:
        QtWidgets.QMessageBox.warning(window, "Error", "No images in folder")


def browse_folder():
    folder_path = QtWidgets.QFileDialog.getExistingDirectory()
    if folder_path:
        folder_path_label.setText(folder_path)


app = QtWidgets.QApplication([])

window = QtWidgets.QWidget()
window.setWindowTitle("Batch processing by Controlnetposes.com")
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

generate_image_button = QtWidgets.QPushButton("Generate Images")
generate_image_button.clicked.connect(generate_image)

right_layout.addWidget(generate_image_button)
hint_label = QtWidgets.QLabel("")
right_layout.addWidget(hint_label)

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

window.showMaximized()
app.exec_()
