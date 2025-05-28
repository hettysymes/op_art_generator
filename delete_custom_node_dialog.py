from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QComboBox, QPushButton, QApplication
)
import sys

class DeleteCustomNodeDialog(QDialog):
    def __init__(self, node_list, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Delete Custom Node")

        # Layout
        layout = QVBoxLayout()

        # Label
        label = QLabel("Select custom node to delete:")
        layout.addWidget(label)

        # ComboBox
        self.combo = QComboBox()
        self.combo.addItems(node_list)
        layout.addWidget(self.combo)

        # Delete Button
        self.delete_button = QPushButton("Delete")
        self.delete_button.clicked.connect(self.accept)
        layout.addWidget(self.delete_button)

        self.setLayout(layout)

    def get_selected_node(self):
        return self.combo.currentText()
