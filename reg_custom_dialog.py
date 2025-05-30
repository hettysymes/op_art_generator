from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit, QPushButton, QMessageBox,
    QDialog, QTreeWidget, QTreeWidgetItem, QComboBox, QTableWidget, QTableWidgetItem,
    QSplitter, QHeaderView
)

from id_datatypes import NodeId, PortId, PropKey


class PortSelectionTree(QWidget):
    def __init__(self, node_info: dict[NodeId, tuple[str, dict[PortId, str]]], is_input: bool):
        """
        node_info: dict of node_id -> (node_name, {port_id: port_name})
        is_input: whether to show input ports (True) or output ports (False)
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
        selected = []
        for port, item in self.check_items.items():
            if item.checkState(0) == Qt.Checked:
                selected.append(port)
        return selected


class PortRenameTable(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        # Label
        label = QLabel("Port Names (same keys across input/output will share the same name):")
        layout.addWidget(label)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Node", "Original Name", "Custom Name"])

        # Make columns resize appropriately
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)

        layout.addWidget(self.table)
        self.setLayout(layout)

        # Keep track of port keys and their custom names
        self.port_key_names = {}  # {(node_id, port_key): custom_name}
        self.key_to_rows = {}  # {(node_id, port_key): row_index}

    def update_ports(self, selected_input_ports: list[PortId], selected_output_ports: list[PortId],
                     node_info: dict[NodeId, tuple[str, dict[PortId, str]]]):
        """Update the table based on selected ports"""

        # Clear existing table
        self.table.setRowCount(0)
        self.key_to_rows.clear()

        # Collect unique (node_id, port_key) combinations, preserving node order
        unique_keys = {}  # {(node_id, port_key): original_name}

        for port in selected_input_ports + selected_output_ports:
            node_id = port.node
            port_key = port.key  # Assuming PortId has a 'key' attribute

            # Find the original name for this port
            if node_id in node_info:
                node_name, port_map = node_info[node_id]
                if port in port_map:
                    original_name = port_map[port]
                    unique_keys[(node_id, port_key)] = original_name

        # Sort keys maintaining node order from node_info, but alphabetical port names within each node
        node_order = list(node_info.keys())  # Preserve original topological order
        sorted_keys = []

        for node_id in node_order:
            # Get all port keys for this node and sort them alphabetically by original name
            node_ports = [(nid, pk, orig_name) for (nid, pk), orig_name in unique_keys.items() if nid == node_id]
            node_ports.sort(key=lambda x: x[2])  # Sort by original name
            sorted_keys.extend([(nid, pk) for nid, pk, _ in node_ports])

        # Populate table
        self.table.setRowCount(len(sorted_keys))

        for row, (node_id, port_key) in enumerate(sorted_keys):
            # Node name
            node_name = node_info[node_id][0] if node_id in node_info else str(node_id)
            node_item = QTableWidgetItem(f"{node_name} ({node_id})")
            node_item.setFlags(Qt.ItemIsEnabled)  # Read-only
            self.table.setItem(row, 0, node_item)

            # Original port name (not key)
            original_name = unique_keys[(node_id, port_key)]
            original_item = QTableWidgetItem(original_name)
            original_item.setFlags(Qt.ItemIsEnabled)  # Read-only
            self.table.setItem(row, 1, original_item)

            # Display name (editable)
            current_custom_name = self.port_key_names.get((node_id, port_key), "")
            if not current_custom_name:
                # Use original name as default
                current_custom_name = original_name

            name_item = QTableWidgetItem(current_custom_name)
            self.table.setItem(row, 2, name_item)

            # Store row mapping
            self.key_to_rows[(node_id, port_key)] = row

        # Connect cell changed signal
        self.table.cellChanged.connect(self._on_cell_changed)

    def _on_cell_changed(self, row, column):
        """Handle changes to display names"""
        if column == 2:  # Display name column
            # Find which (node_id, port_key) this row represents
            for (node_id, port_key), mapped_row in self.key_to_rows.items():
                if mapped_row == row:
                    new_name = self.table.item(row, column).text().strip()
                    self.port_key_names[(node_id, port_key)] = new_name
                    break

    def get_port_key_names(self) -> dict[tuple[NodeId, str], str]:
        """Get the mapping of (node_id, port_key) -> custom_name"""
        # Update from current table state
        result = {}
        for (node_id, port_key), row in self.key_to_rows.items():
            name_item = self.table.item(row, 2)
            if name_item:
                custom_name = name_item.text().strip()
                if custom_name:
                    result[(node_id, port_key)] = custom_name
        return result

def process_name(name: str) -> str:
    return name.strip().title()

class RegCustomDialog(QDialog):
    def __init__(self, node_to_info, existing_names):
        super().__init__()
        self.setWindowTitle("Create custom node")
        self.setMinimumSize(800, 800)
        self.existing_names = existing_names
        self.node_to_info = node_to_info

        # Main layout
        layout = QVBoxLayout()

        # Name
        name_label = QLabel("Name of custom node:")
        self.name_input = QLineEdit()
        layout.addWidget(name_label)
        layout.addWidget(self.name_input)

        # Description
        description_label = QLabel("Description (optional):")
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("This will appear over the help icon (?) for your node.")
        self.description_input.setFixedHeight(60)
        layout.addWidget(description_label)
        layout.addWidget(self.description_input)

        # Create splitter for port selection and renaming
        splitter = QSplitter(Qt.Vertical)

        # Port selection area
        port_selection_widget = QWidget()
        port_selection_layout = QHBoxLayout()

        # Input port selection
        input_widget = QWidget()
        input_layout = QVBoxLayout()
        input_layout.addWidget(QLabel("Select input ports:"))
        self.in_port_selector = PortSelectionTree(node_to_info, is_input=True)
        input_layout.addWidget(self.in_port_selector)
        input_widget.setLayout(input_layout)

        # Output port selection
        output_widget = QWidget()
        output_layout = QVBoxLayout()
        output_layout.addWidget(QLabel("Select output ports:"))
        self.out_port_selector = PortSelectionTree(node_to_info, is_input=False)
        output_layout.addWidget(self.out_port_selector)
        output_widget.setLayout(output_layout)

        port_selection_layout.addWidget(input_widget)
        port_selection_layout.addWidget(output_widget)
        port_selection_widget.setLayout(port_selection_layout)

        # Port rename table
        self.port_rename_table = PortRenameTable()

        # Add to splitter
        splitter.addWidget(port_selection_widget)
        splitter.addWidget(self.port_rename_table)
        splitter.setSizes([400, 300])  # Initial sizes

        layout.addWidget(splitter)

        # Visualisation selection
        vis_selector_label = QLabel(
            "Select visualisation node (your custom node's visualisation will mirror this node):")
        self.vis_selector = QComboBox()
        for node, (node_name, _) in node_to_info.items():
            self.vis_selector.addItem(f"{node_name} ({node})", userData=node)
        self.vis_selector.setCurrentIndex(self.vis_selector.count() - 1)
        layout.addWidget(vis_selector_label)
        layout.addWidget(self.vis_selector)

        # Buttons
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Cancel")
        ok_button.clicked.connect(self.validate_inputs)
        cancel_button.clicked.connect(self.reject)
        button_layout.addStretch()
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(ok_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

        # Connect tree changes to auto-update table
        self.in_port_selector.tree.itemChanged.connect(self.update_port_names_table)
        self.out_port_selector.tree.itemChanged.connect(self.update_port_names_table)

        # Initial population
        self.update_port_names_table()

    def update_port_names_table(self):
        """Update the port names table based on current selections"""
        selected_inputs = self.in_port_selector.get_selected_ports()
        selected_outputs = self.out_port_selector.get_selected_ports()
        self.port_rename_table.update_ports(selected_inputs, selected_outputs, self.node_to_info)

    def create_warning(self, title, msg):
        box = QMessageBox(self)
        box.setText(title)
        box.setInformativeText(msg)
        box.setIcon(QMessageBox.Warning)
        box.exec_()

    def validate_inputs(self):
        name = process_name(self.name_input.text())
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

    def get_inputs(self) -> tuple[str, str, list[PortId], list[PortId], NodeId, dict[tuple[NodeId, PropKey], str]]:
        """
        Returns: (name, description, input_ports, output_ports, vis_node, port_key_names)
        where port_key_names maps (node_id, port_key) -> custom_display_name
        """
        return (
            process_name(self.name_input.text()),  # Name
            self.description_input.toPlainText(),  # Description
            self.in_port_selector.get_selected_ports(),  # Input ports
            self.out_port_selector.get_selected_ports(),  # Output ports
            self.vis_selector.currentData(),  # Visualisation node
            self.port_rename_table.get_port_key_names()  # Port key custom names
        )
