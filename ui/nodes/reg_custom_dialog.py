from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QLabel, QTextEdit, QHBoxLayout, QPushButton


class RegCustomDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Create custom node")

        self.layout = QVBoxLayout()

        self.name_label = QLabel("Name of custom node:")
        self.name_input = QLineEdit()
        self.layout.addWidget(self.name_label)
        self.layout.addWidget(self.name_input)

        # Description (optional)
        self.description_label = QLabel("Description (optional):")
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("This will appear over the help icon (?) for your node.")
        self.description_input.setFixedHeight(60)  # Controls the height of the box

        self.layout.addWidget(self.description_label)
        self.layout.addWidget(self.description_input)

        self.label1 = QLabel("Input node ID:")
        self.input1 = QLineEdit()
        self.hash_label1 = QLabel("#")

        self.input_layout1 = QHBoxLayout()
        self.input_layout1.addWidget(self.hash_label1)
        self.input_layout1.addWidget(self.input1)

        self.layout.addWidget(self.label1)
        self.layout.addLayout(self.input_layout1)

        self.label2 = QLabel("Output node ID:")
        self.input2 = QLineEdit()
        self.hash_label2 = QLabel("#")

        self.input_layout2 = QHBoxLayout()
        self.input_layout2.addWidget(self.hash_label2)
        self.input_layout2.addWidget(self.input2)

        self.layout.addWidget(self.label2)
        self.layout.addLayout(self.input_layout2)

        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        self.layout.addWidget(self.ok_button)

        self.setLayout(self.layout)

    def get_inputs(self):
        return (
            self.name_input.text(),
            self.description_input.toPlainText(),
            self.input1.text(),
            self.input2.text()
        )