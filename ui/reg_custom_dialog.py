from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QTextEdit, QPushButton, QMessageBox,
    QDialog, QTreeWidget, QTreeWidgetItem, QHeaderView, QComboBox
)

from ui.id_generator import shorten_uid
from ui.nodes.port_defs import PortIO


class PortSelectionTree(QWidget):
    def __init__(self, id_to_info, port_io):
        """
        id_to_ports: dict of node_id -> list of port
        display_names: optional dict of (node_id, port) -> str for custom labels
        """
        super().__init__()

        layout = QVBoxLayout()
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setColumnCount(1)
        self.check_items = {}  # {(node_id, port): QTreeWidgetItem}

        for node_id, (node_name, port_map) in id_to_info.items():
            # Filter by IO
            filtered_ports = {
                port_id: port_name
                for port_id, port_name in port_map.items()
                if port_id[0] == port_io
            }

            # Skip if no ports of this IO
            if not filtered_ports:
                continue

            node_item = QTreeWidgetItem([f"{node_name} (#{shorten_uid(node_id)})"])
            node_item.setFlags(Qt.ItemIsEnabled)
            self.tree.addTopLevelItem(node_item)

            for port_id, port_name in filtered_ports.items():
                port_item = QTreeWidgetItem([port_name])
                port_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
                port_item.setCheckState(0, Qt.Unchecked)

                # Store actual data
                port_item.setData(0, Qt.UserRole, (node_id, port_id))

                node_item.addChild(port_item)
                self.check_items[(node_id, port_id)] = port_item

            node_item.setExpanded(False)

        layout.addWidget(self.tree)
        self.setLayout(layout)

    def get_selected_ports(self):
        selected = []
        for item in self.check_items.values():
            if item.checkState(0) == Qt.Checked:
                node_id, port = item.data(0, Qt.UserRole)
                selected.append((node_id, port))
        return selected


class RegCustomDialog(QDialog):
    def __init__(self, id_to_info, existing_names):
        super().__init__()
        self.setWindowTitle("Create custom node")
        self.id_to_info = id_to_info
        self.node_ids = list(id_to_info.keys())
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
        self.in_port_selector = PortSelectionTree(self.id_to_info, port_io=PortIO.INPUT)
        in_port_selector_label = QLabel("Select input ports:")
        in_port_selector_layout = QVBoxLayout()
        in_port_selector_layout.addWidget(in_port_selector_label)
        in_port_selector_layout.addWidget(self.in_port_selector)

        # Output port selection
        self.out_port_selector = PortSelectionTree(self.id_to_info, port_io=PortIO.OUTPUT)
        out_port_selector_label = QLabel("Select output ports:")
        out_port_selector_layout = QVBoxLayout()
        out_port_selector_layout.addWidget(out_port_selector_label)
        out_port_selector_layout.addWidget(self.out_port_selector)

        # Visualisation selection
        self.vis_selector = QComboBox()
        vis_selector_label = QLabel("Select visualisation node (your custom node's visualisation will mirror this node):")
        for node_id, (node_name, _) in self.id_to_info.items():
            self.vis_selector.addItem(f"{node_name} (#{shorten_uid(node_id)})", userData=node_id)
        self.vis_selector.setCurrentIndex(self.vis_selector.count() - 1) # Default to last list item
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
            self.create_warning("Name In Use", "This name is assigned to an existing custom node. Please choose another.")
            return
        # Check start node is before stop node in the pipeline
        # start_id = self.start_node_input.currentData()
        # stop_id = self.stop_node_input.currentData()
        # if self.node_ids.index(start_id) > self.node_ids.index(stop_id):
        #     self.create_warning("Invalid Selection", "The selected input node must come before (or be) the selected output node in the pipeline. Please try again.")
        #     return
        self.accept()

    def get_inputs(self):
        return (
            self.name_input.text().strip(),
            self.description_input.toPlainText(),
            self.in_port_selector.get_selected_ports(),
            self.out_port_selector.get_selected_ports(),
            self.vis_selector.currentData()
        )