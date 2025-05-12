from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QLabel, QTextEdit, QHBoxLayout, QPushButton, QComboBox, \
    QMessageBox

from ui.id_generator import shorten_uid


def create_node_id_widget(id_to_names, set_last_index):
    widget = QComboBox()
    for node_id, node_name in id_to_names.items():
        widget.addItem(f"{node_name} (#{shorten_uid(node_id)})", userData=node_id)
    if set_last_index:
        widget.setCurrentIndex(widget.count() - 1)
    return widget

class RegCustomDialog(QDialog):
    def __init__(self, id_to_names, existing_names):
        super().__init__()
        self.setWindowTitle("Create custom node")
        self.id_to_names = id_to_names
        self.node_ids = list(id_to_names.keys())
        self.existing_names = existing_names

        # Name
        name_label = QLabel("Name of custom node:")
        self.name_input = QLineEdit()

        # Description (optional)
        description_label = QLabel("Description (optional):")
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("This will appear over the help icon (?) for your node.")
        self.description_input.setFixedHeight(60)  # Controls the height of the box

        # Start node input
        self.start_node_input = create_node_id_widget(id_to_names, set_last_index=False)
        start_node_layout = QHBoxLayout()
        start_node_layout.addWidget(QLabel("Input node:"))
        start_node_layout.addWidget(self.start_node_input)

        # Stop node input
        self.stop_node_input = create_node_id_widget(id_to_names, set_last_index=True)
        stop_node_layout = QHBoxLayout()
        stop_node_layout.addWidget(QLabel("Output node:"))
        stop_node_layout.addWidget(self.stop_node_input)

        # OK button
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.validate_inputs)

        # Set layout
        layout = QVBoxLayout()
        layout.addWidget(name_label)
        layout.addWidget(self.name_input)
        layout.addWidget(description_label)
        layout.addWidget(self.description_input)
        layout.addLayout(start_node_layout)
        layout.addLayout(stop_node_layout)
        layout.addWidget(ok_button)
        self.setLayout(layout)

    def create_warning(self, title, msg):
        box = QMessageBox(self)
        box.setText(title)
        box.setInformativeText(msg)
        box.setIcon(QMessageBox.Warning)
        box.exec_()

    def validate_inputs(self):
        name = self.name_input.text().strip()
        # Check name exists
        if not name:
            self.create_warning("Missing Name", "Please enter a name for your custom node.")
            return
        # Check name does not already exist
        if name in self.existing_names:
            self.create_warning("Name In Use", "This name is assigned to an existing custom node. Please choose another.")
            return
        # Check start node is before stop node in the pipeline
        start_id = self.start_node_input.currentData()
        stop_id = self.stop_node_input.currentData()
        if self.node_ids.index(start_id) >= self.node_ids.index(stop_id):
            self.create_warning("Invalid Selection", "The selected input node must come before the selected output node in the pipeline. Please try again.")
            return
        self.accept()

    def get_inputs(self):
        return (
            self.name_input.text().strip(),
            self.description_input.toPlainText(),
            self.start_node_input.currentData(),
            self.stop_node_input.currentData()
        )