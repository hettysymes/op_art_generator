from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QTextEdit, QPushButton, QMessageBox,
    QDialog, QTreeWidget, QTreeWidgetItem, QComboBox
)

from ui.id_datatypes import NodeId, PortId


class PortSelectionTree(QWidget):
    def __init__(self, node_info: dict[NodeId, tuple[str, dict[PortId, str]]], is_input: bool):
        """
        id_to_ports: dict of node_id -> list of port
        display_names: optional dict of (node_id, port) -> str for custom labels
        """
        super().__init__()

        layout = QVBoxLayout()
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setColumnCount(1)
        self.check_items = {}  # {port: QTreeWidgetItem}

        for node, (node_name, port_map) in node_info.items():
            # Filter by IO
            filtered_port_map = {
                port: port_name
                for port, port_name in port_map.items()
                if port.is_input == is_input
            }

            # Skip if no ports of this IO
            if not filtered_port_map:
                continue

            node_item = QTreeWidgetItem([f"{node_name} ({node})"])
            node_item.setFlags(Qt.ItemIsEnabled)
            self.tree.addTopLevelItem(node_item)

            for port, port_name in filtered_port_map.items():
                port_item = QTreeWidgetItem([port_name])
                port_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
                port_item.setCheckState(0, Qt.Checked)

                # Store actual data
                port_item.setData(0, Qt.UserRole, port)

                node_item.addChild(port_item)
                self.check_items[port] = port_item

            node_item.setExpanded(True)

        layout.addWidget(self.tree)
        self.setLayout(layout)

    def get_selected_ports(self) -> list[PortId]:
        selected: list[PortId] = []
        for item in self.check_items.values():
            if item.checkState(0) == Qt.Checked:
                selected.append(item.data(0, Qt.UserRole))
        return selected


class RegCustomDialog(QDialog):
    def __init__(self, node_to_info, existing_names):
        super().__init__()
        self.setWindowTitle("Create custom node")
        self.existing_names = existing_names

        # Name
        name_label = QLabel("Name of custom node:")
        self.name_input = QLineEdit()

        # Description
        description_label = QLabel("Description (optional):")
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("This will appear over the help icon (?) for your node.")
        self.description_input.setFixedHeight(60)

        # Input port selection
        self.in_port_selector = PortSelectionTree(node_to_info, is_input=True)
        in_port_selector_label = QLabel("Select input ports:")
        in_port_selector_layout = QVBoxLayout()
        in_port_selector_layout.addWidget(in_port_selector_label)
        in_port_selector_layout.addWidget(self.in_port_selector)

        # Output port selection
        self.out_port_selector = PortSelectionTree(node_to_info, is_input=False)
        out_port_selector_label = QLabel("Select output ports:")
        out_port_selector_layout = QVBoxLayout()
        out_port_selector_layout.addWidget(out_port_selector_label)
        out_port_selector_layout.addWidget(self.out_port_selector)

        # Visualisation selection
        self.vis_selector = QComboBox()
        vis_selector_label = QLabel(
            "Select visualisation node (your custom node's visualisation will mirror this node):")
        for node, (node_name, _) in node_to_info.items():
            self.vis_selector.addItem(f"{node_name} ({node})", userData=node)
        self.vis_selector.setCurrentIndex(self.vis_selector.count() - 1)  # Default to last list item
        vis_selector_layout = QVBoxLayout()
        vis_selector_layout.addWidget(vis_selector_label)
        vis_selector_layout.addWidget(self.vis_selector)

        # OK button
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.validate_inputs)

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(name_label)
        layout.addWidget(self.name_input)
        layout.addWidget(description_label)
        layout.addWidget(self.description_input)
        layout.addLayout(in_port_selector_layout)
        layout.addLayout(out_port_selector_layout)
        layout.addLayout(vis_selector_layout)
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
            self.create_warning("Name In Use",
                                "This name is assigned to an existing custom node. Please choose another.")
            return
        self.accept()

    def get_inputs(self) -> tuple[str, str, list[PortId], list[PortId], NodeId]:
        return (
            self.name_input.text().strip(),                  # Name
            self.description_input.toPlainText(),            # Description
            self.in_port_selector.get_selected_ports(),      # Input ports
            self.out_port_selector.get_selected_ports(),     # Output ports
            self.vis_selector.currentData()                  # Visualisation node
        )
