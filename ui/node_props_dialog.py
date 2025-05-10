import copy

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QDialog, QPushButton, QComboBox, QTableWidgetItem, QHBoxLayout, QWidget, QVBoxLayout, \
    QFormLayout, QDoubleSpinBox, QDialogButtonBox, QMenu, QStyledItemDelegate, QColorDialog, QSpinBox, QCheckBox, \
    QGroupBox, QLabel, QLineEdit

from ui.colour_prop_widget import ColorPropertyWidget
from ui.id_generator import shorten_uid
from ui.nodes.elem_ref import ElemRef
from ui.nodes.node_defs import PropType
from ui.nodes.port_defs import PortIO
from ui.reorderable_table_widget import ReorderableTableWidget


class HelpIconLabel(QPushButton):
    def __init__(self, description, max_width=300, parent=None):
        super().__init__(parent)

        # Set up the help icon with "?" text
        self.setText("?")
        self.setFixedSize(16, 16)

        # Style the button to look like a help icon
        self.setStyleSheet("""
            QPushButton {
                background-color: #b0b0b0;
                color: white;
                font-weight: bold;
                border-radius: 8px;
                border: none;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: #8a8a8a;
            }
        """)

        # Apply word-wrapped tooltip using HTML
        width_px = str(max_width) + "px"
        wrapped_text = f"<div style='max-width: {width_px}; white-space: normal;'>{description}</div>"
        self.setToolTip(wrapped_text)

class ModifyPropertyPortButton(QPushButton):
    def __init__(self, on_click_callback, port_key, adding, max_width=300, parent=None):
        super().__init__(parent)
        self.port_key = port_key
        self.adding = adding
        self.text_pair = ('-', '+')
        self.description_pair = ("Remove the input port for this property.",
                                 "Add an input port to control this property.")
        self.setText(self.text_pair[int(self.adding)])
        self.setFixedSize(16, 16)
        self.max_width = max_width

        # Style the button to look like a help icon
        self.setStyleSheet("""
            QPushButton {
                background-color: #b0b0b0;
                color: white;
                font-weight: bold;
                border-radius: 8px;
                border: none;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: #8a8a8a;
            }
        """)

        # Apply word-wrapped tooltip using HTML
        width_px = str(max_width) + "px"
        wrapped_text = f"<div style='max-width: {width_px}; white-space: normal;'>{self.description_pair[int(self.adding)]}</div>"
        self.setToolTip(wrapped_text)

        # Connect the click signal to the callback
        self.user_callback = on_click_callback
        self.clicked.connect(self.handle_click)

    def handle_click(self):
        # Toggle the state
        self.adding = not self.adding
        self.setText(self.text_pair[int(self.adding)])

        # Apply word-wrapped tooltip using HTML
        width_px = str(self.max_width) + "px"
        wrapped_text = f"<div style='max-width: {width_px}; white-space: normal;'>{self.description_pair[int(self.adding)]}</div>"
        self.setToolTip(wrapped_text)

        # Execute user callback
        if self.user_callback:
            self.user_callback(self.port_key, not self.adding)

class NodePropertiesDialog(QDialog):
    """Dialog for editing node properties"""

    def __init__(self, node_item, parent=None):
        super().__init__(parent)
        self.node_item = node_item
        self.scene = node_item.scene()
        self.setWindowTitle(f"Properties: {node_item.node().name()}")
        self.setMinimumWidth(400)

        # Main layout
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Create form layout for properties
        form_layout = QFormLayout()
        form_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

        self.property_widgets = {}

        # Add custom properties based on node type
        if node_item.node().get_prop_entries():
            props_group = QGroupBox("Node Properties")
            props_layout = QFormLayout()
            props_group.setLayout(props_layout)

            # Now modify your existing code to use this function
            for prop_key, prop_entry in node_item.node().get_prop_entries().items():
                if prop_entry.prop_type != PropType.HIDDEN:
                    widget = self.create_property_widget(prop_key, prop_entry, node_item.node().get_property(prop_key), node_item)

                    # Create the row with label and help icon
                    label_container, widget_container = self.create_property_row(prop_key, prop_entry, widget, node_item)
                    props_layout.addRow(label_container, widget_container)
                    self.property_widgets[prop_key] = widget

            main_layout.addWidget(props_group)

        port_only_group = None
        input_ports_open = [port_key for (io, port_key) in node_item.node_state.ports_open if io == PortIO.INPUT]

        for port_key, port_def in node_item.node().port_defs_filter_by_io(PortIO.INPUT).items():
            if port_def.optional and port_def.description and (port_key not in node_item.node().get_prop_entries()):
                # Add label with property button
                if not port_only_group:
                    port_only_group = QGroupBox("Port modifiable properties")
                    port_only_group_layout = QVBoxLayout(port_only_group)  # Create a vertical layout for the group
                    port_only_group.setLayout(port_only_group_layout)  # Set the layout for the group

                widget_container = QWidget()  # This will be a widget inside the group
                widget_layout = QHBoxLayout(widget_container)
                widget_layout.setContentsMargins(0, 0, 0, 0)
                widget_layout.setSpacing(4)

                text = f"{port_def.display_name}: {port_def.description}"

                # Create and add label
                label = QLabel(text)
                widget_layout.addWidget(label)

                # Add plus/minus buttons based on port state
                if port_key in input_ports_open:
                    # If port is open, add minus button to remove the port
                    minus_btn = ModifyPropertyPortButton(self.change_property_port, port_key, adding=False)
                    widget_layout.addWidget(minus_btn)
                else:
                    # If port is not open, add plus button to add the port
                    plus_btn = ModifyPropertyPortButton(self.change_property_port, port_key, adding=True)
                    widget_layout.addWidget(plus_btn)

                # Add the widget container (with layout) to the group
                port_only_group_layout.addWidget(widget_container)

        # If port_only_group was created, add it to the main layout
        if port_only_group:
            main_layout.addWidget(port_only_group)

        # Create buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        main_layout.addLayout(form_layout)
        main_layout.addWidget(button_box)

    def change_property_port(self, port_key, adding):
        if adding:
            self.node_item.add_property_port(port_key)
        else:
            self.node_item.remove_property_port(port_key)

    def create_property_row(self, prop_key, prop_entry, widget, node_item):
        """Create a row with property label and a help icon to the right of the widget"""

        # Create a container widget for the label
        label_container = QWidget()
        label_layout = QHBoxLayout(label_container)
        label_layout.setContentsMargins(0, 0, 0, 0)
        label_layout.setSpacing(4)  # Small spacing between elements

        # Create the label
        add_text = ":" if prop_entry.auto_format else ""
        label = QLabel(prop_entry.display_name + add_text)
        label_layout.addWidget(label)
        label_layout.addStretch()

        # Create a container for the widget and help icon
        widget_container = QWidget()
        widget_layout = QHBoxLayout(widget_container)
        widget_layout.setContentsMargins(0, 0, 0, 0)
        widget_layout.setSpacing(4)  # Small spacing between widget and icon

        # Add the widget first
        widget_layout.addWidget(widget)

        # Add the help icon after the widget (on the right)
        if prop_entry.description:
            help_icon = HelpIconLabel(prop_entry.description, max_width=300)  # Set maximum width for tooltip
            widget_layout.addWidget(help_icon)
        if prop_key in node_item.node().port_defs_filter_by_io(PortIO.INPUT):
            input_ports_open = [port_key for (io, port_key) in node_item.node_state.ports_open if io == PortIO.INPUT]
            if prop_key in input_ports_open:
                # Exists port to modify this property, add minus button
                minus_btn = ModifyPropertyPortButton(self.change_property_port,
                                                     prop_key,
                                                     adding=False)  # Set maximum width for tooltip
                widget_layout.addWidget(minus_btn)
            else:
                # Does not exist port to modify this property, add plus button
                plus_btn = ModifyPropertyPortButton(self.change_property_port, prop_key, adding=True)  # Set maximum width for tooltip
                widget_layout.addWidget(plus_btn)

        return label_container, widget_container

    def create_property_widget(self, prop_key, prop_entry, current_value, node_item):
        """Create an appropriate widget for the property type"""
        if prop_entry.prop_type == PropType.INT:
            widget = QSpinBox()
            if prop_entry.min_value is not None:
                widget.setMinimum(prop_entry.min_value)
            if prop_entry.max_value is not None:
                widget.setMaximum(prop_entry.max_value)
            widget.setValue(current_value or 0)

        elif prop_entry.prop_type == PropType.FLOAT:
            widget = QDoubleSpinBox()
            widget.setMinimum(prop_entry.min_value if prop_entry.min_value is not None else -999999.0)
            if prop_entry.max_value is not None:
                widget.setMaximum(prop_entry.max_value)
            widget.setValue(current_value or 0.0)

        elif prop_entry.prop_type == PropType.BOOL:
            widget = QCheckBox()
            widget.setChecked(current_value or False)

        elif prop_entry.prop_type == PropType.COORDINATE:
            # Create the widget
            widget = QWidget()

            # Create a form layout for the overall container
            form_layout = QFormLayout(widget)

            # Create a horizontal layout for the spinboxes
            spinbox_container = QWidget()
            spinbox_layout = QHBoxLayout(spinbox_container)
            spinbox_layout.setContentsMargins(0, 0, 0, 0)  # Remove internal margins

            # Create the spinboxes
            x_spinbox = QDoubleSpinBox()
            y_spinbox = QDoubleSpinBox()

            # Set initial values
            x, y = (current_value or (0.5, 0.5))
            x_spinbox.setValue(x)
            y_spinbox.setValue(y)

            # Add spinboxes to the horizontal layout with labels
            spinbox_layout.addWidget(QLabel("("))
            spinbox_layout.addWidget(x_spinbox)
            spinbox_layout.addWidget(QLabel(","))
            spinbox_layout.addWidget(y_spinbox)
            spinbox_layout.addWidget(QLabel(")"))

            # Add the container to the form layout as a single row
            form_layout.addRow(spinbox_container)

            def get_coord_value():
                return x_spinbox.value(), y_spinbox.value()

            widget.get_value = get_coord_value

        # elif prop_entry.prop_type == PropType.PROP_ENUM:
        #     widget = QComboBox()
        #     input_node_props = node_item.node()._input_node('element').prop_type_list()
        #     # Populate the widget
        #     widget.addItem("[none]", userData=None)
        #     for inp_prop in input_node_props:
        #         widget.addItem(inp_prop.name, userData=inp_prop.key_name)
        #     # Set the current value if available
        #     if current_value is not None:
        #         # Find the index where the key_name matches current_value
        #         index = next((i for i in range(widget.count())
        #                       if widget.itemData(i) == current_value), 0)
        #         widget.setCurrentIndex(index)

        # elif prop_entry.prop_type == PropType.SELECTOR_ENUM:
        #     widget = QComboBox()
        #     input_prop_compute = node_item.node._input_node('iterator').compute()
        #     # Populate the widget
        #     widget.addItem("[none]", userData=None)
        #     if input_prop_compute:
        #         for i in range(len(input_prop_compute)):
        #             widget.addItem(str(i + 1), userData=i)
        #     # Set the current value if available
        #     if current_value is not None:
        #         # Find the index where the key_name matches current_value
        #         index = next((i for i in range(widget.count())
        #                       if widget.itemData(i) == current_value), 0)
        #         widget.setCurrentIndex(index)

        # elif prop_entry.prop_type == PropType.ENUM and prop_entry.options:
        #     widget = QComboBox()
        #     for option in prop_entry.options:
        #         widget.addItem(option, userData=option)
        #     if current_value is not None:
        #         index = prop_entry.options.index(current_value) if current_value in prop_entry.options else 0
        #         widget.setCurrentIndex(index)

        elif prop_entry.prop_type == PropType.POINT_TABLE:
            def add_point_item(point, row=None, table=None):
                item = QTableWidgetItem()
                item.setTextAlignment(Qt.AlignCenter)
                item.setData(Qt.UserRole, point)
                if isinstance(point, ElemRef):
                    points = point.get_base_points()
                    start_x, start_y = points[0]
                    stop_x, stop_y = points[-1]
                    arrow = '←' if point.reversed else '→'
                    item.setText(
                        f"{point.node_type} (id: #{shorten_uid(point.node_id)})\n({start_x:.2f}, {start_y:.2f}) {arrow} ({stop_x:.2f}, {stop_y:.2f})")
                    item.setBackground(QColor(237, 130, 157))
                else:
                    x, y = point
                    item.setText(f"({x:.2f}, {y:.2f})")
                if (row is not None) and (table is not None):
                    table.setItem(row, 0, item)
                return item

            # Create our custom table widget
            table = ReorderableTableWidget(add_point_item)

            # Set up the basic table structure with single column
            table.setColumnCount(1)
            table.setHorizontalHeaderLabels(["Coordinate Points (X, Y)"])

            # Custom delegate to ensure text alignment is centered
            class CenteredItemDelegate(QStyledItemDelegate):
                def initStyleOption(self, option, index):
                    super().initStyleOption(option, index)
                    option.displayAlignment = Qt.AlignCenter

            # Apply the delegate to the table
            centered_delegate = CenteredItemDelegate()
            table.setItemDelegate(centered_delegate)
            table.verticalHeader().setDefaultSectionSize(40)
            table.setWordWrap(True)

            # Populate with current data
            points_data = current_value or prop_entry.default_value or []
            table.setRowCount(len(points_data))
            for row, point in enumerate(points_data):
                add_point_item(point, row, table)

            # Add button to add points
            button_widget = QWidget()
            button_layout = QHBoxLayout(button_widget)
            button_layout.setContentsMargins(0, 0, 0, 0)

            add_button = QPushButton("+")

            def show_point_dialog(initial_x=0.0, initial_y=0.0):
                dialog = QDialog()
                dialog.setWindowTitle("Coordinate Point")
                dialog_layout = QVBoxLayout(dialog)

                form_layout = QFormLayout()

                x_input = QDoubleSpinBox()
                x_input.setDecimals(2)
                x_input.setValue(initial_x)

                y_input = QDoubleSpinBox()
                y_input.setDecimals(2)
                y_input.setValue(initial_y)

                form_layout.addRow("X:", x_input)
                form_layout.addRow("Y:", y_input)
                dialog_layout.addLayout(form_layout)

                button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
                button_box.accepted.connect(dialog.accept)
                button_box.rejected.connect(dialog.reject)
                dialog_layout.addWidget(button_box)

                if dialog.exec_():
                    try:
                        return x_input.value(), y_input.value()
                    except ValueError:
                        return None
                return None

            # Add point dialog function
            def add_point():
                result = show_point_dialog()
                if result:
                    row = table.rowCount()
                    table.setRowCount(row + 1)
                    add_point_item(result, row, table)

            add_button.clicked.connect(add_point)
            button_layout.addWidget(add_button)

            # Set up context menu for deletion and editing
            def show_context_menu(position):
                row = table.rowAt(position.y())

                if row >= 0:
                    item = table.item(row, 0)
                    item_data = item.data(Qt.UserRole)
                    menu = QMenu()
                    if not isinstance(item_data, ElemRef):
                        edit_action = menu.addAction("Edit")
                        delete_action = menu.addAction("Delete")

                        action = menu.exec_(table.viewport().mapToGlobal(position))

                        if action == delete_action:
                            table.removeRow(row)

                        elif action == edit_action:
                            x_val, y_val = item_data
                            result = show_point_dialog(x_val, y_val)

                            if result:
                                add_point_item(result, row, table)
                    else:
                        reverse_action = menu.addAction("Reverse points")
                        action = menu.exec_(table.viewport().mapToGlobal(position))
                        if action == reverse_action:
                            item_data.reverse()
                            add_point_item(item_data, row, table)

            table.setContextMenuPolicy(Qt.CustomContextMenu)
            table.customContextMenuRequested.connect(show_context_menu)

            # Create a container for the table and button
            container = QWidget()
            layout = QVBoxLayout(container)
            layout.addWidget(table)
            layout.addWidget(button_widget)

            # Function to get the current value from the table
            def get_table_value():
                points = []
                for row in range(table.rowCount()):
                    item = table.item(row, 0)
                    if item:
                        # Retrieve the actual tuple data stored in UserRole
                        point_data = item.data(Qt.UserRole)
                        if point_data:
                            points.append(point_data)
                return points

            # Store both the getter function and the reference to the table with the container
            container.get_value = get_table_value
            container.table_widget = table  # Store a reference to the actual table

            widget = container
        elif prop_entry.prop_type == PropType.PORT_REF_TABLE:

            def add_item(table_entry, row=None, table=None):
                ref_id = table_entry[0]
                port_ref = self.scene.node_graph.get_port_ref(self.node_item.node_state.node_id, prop_entry.linked_port_key, ref_id)
                item = QTableWidgetItem()
                item.setTextAlignment(Qt.AlignCenter)
                item.setData(Qt.UserRole, table_entry)
                item.setText(f"{port_ref.base_node_name} (id: #{shorten_uid(port_ref.node_id)})")
                if not table_entry[2]:
                    # Set red background for non-deletable items
                    item.setBackground(QColor(237, 130, 157))
                if (row is not None) and (table is not None):
                    table.setItem(row, 0, item)
                return item

            # Create our custom table widget
            table = ReorderableTableWidget(add_item)

            # Set up the basic table structure with single column
            table.setColumnCount(1)
            table.setHorizontalHeaderLabels(["Drawing"])

            # Custom delegate to ensure text alignment is centered
            class CenteredItemDelegate(QStyledItemDelegate):
                def initStyleOption(self, option, index):
                    super().initStyleOption(option, index)
                    option.displayAlignment = Qt.AlignCenter

            # Apply the delegate to the table
            centered_delegate = CenteredItemDelegate()
            table.setItemDelegate(centered_delegate)
            table.verticalHeader().setDefaultSectionSize(40)
            table.setWordWrap(True)

            # Populate with current data
            current_entries = current_value or prop_entry.default_value or []
            table.setRowCount(len(current_entries))
            for row, table_entry in enumerate(current_entries):
                add_item(table_entry, row, table)

            # Set up context menu for deletion and duplicating
            def show_context_menu(position):
                row = table.rowAt(position.y())

                if row >= 0:
                    item = table.item(row, 0)
                    ref_id, element, deletable = item.data(Qt.UserRole)
                    menu = QMenu()
                    duplicate_action = menu.addAction("Duplicate")
                    if deletable:
                        delete_action = menu.addAction("Delete")

                    action = menu.exec_(table.viewport().mapToGlobal(position))

                    if deletable and action == delete_action:
                        table.removeRow(row)

                    if action == duplicate_action:
                        # Add a new row below the current one
                        table.insertRow(row + 1)
                        # Create a new item
                        new_item = QTableWidgetItem(item.text())
                        # Set the same user data (elem_ref)
                        new_item.setData(Qt.UserRole, (ref_id, copy.deepcopy(element), True))
                        # Add the item to the table
                        table.setItem(row + 1, 0, new_item)

            table.setContextMenuPolicy(Qt.CustomContextMenu)
            table.customContextMenuRequested.connect(show_context_menu)

            # Create a container for the table and button
            container = QWidget()
            layout = QVBoxLayout(container)
            layout.addWidget(table)

            # Function to get the current value from the table
            def get_table_value():
                data = []
                for row in range(table.rowCount()):
                    item = table.item(row, 0)
                    data.append(item.data(Qt.UserRole))
                return data

            # Store both the getter function and the reference to the table with the container
            container.get_value = get_table_value
            container.table_widget = table  # Store a reference to the actual table

            widget = container
        # elif prop_entry.prop_type == PropType.COLOUR_TABLE:
        #     def add_colour_item(colour, row=None, table=None):
        #         string_col = str((colour.red(), colour.green(), colour.blue(), colour.alpha()))
        #         item = QTableWidgetItem(string_col)
        #         item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        #         item.setData(Qt.UserRole, colour)
        #         if (row is not None) and (table is not None):
        #             table.setItem(row, 0, item)
        #         return item
        #
        #     # Create a table widget
        #     table = ReorderableTableWidget(add_colour_item)
        #
        #     # Set up the basic table structure
        #     table.setColumnCount(1)
        #     table.setHorizontalHeaderLabels(["Colour"])
        #
        #     # Custom delegate to display color swatches
        #     class ColorDelegate(QStyledItemDelegate):
        #         def paint(self, painter, option, index):
        #             if index.column() == 0:
        #                 color_str = index.data()
        #                 if color_str:
        #                     color = QColor(*ast.literal_eval(color_str))
        #                     # Fill the entire cell with the color
        #                     painter.fillRect(option.rect, color)
        #
        #                     # Add a border around the color swatch
        #                     painter.setPen(QPen(Qt.black, 1))
        #                     painter.drawRect(option.rect.adjusted(0, 0, -1, -1))
        #
        #                     # The key part: prevent default text drawing
        #                     return
        #             # Only call the base implementation if we didn't handle it above
        #             super().paint(painter, option, index)
        #
        #         def displayText(self, value, locale):
        #             # Return empty string to prevent text display
        #             return ""
        #
        #     # Apply the delegate to the table
        #     table.setItemDelegate(ColorDelegate())
        #
        #     # Make rows a bit taller to better display the color swatches
        #     table.verticalHeader().setDefaultSectionSize(30)
        #
        #     # Populate with current data
        #     colours = current_value or prop_entry.default_value or []
        #     table.setRowCount(len(colours))
        #     for row, colour in enumerate(colours):
        #         add_colour_item(QColor(*colour), row, table)
        #
        #     # Add buttons to add/remove rows
        #     button_widget = QWidget()
        #     button_layout = QHBoxLayout(button_widget)
        #     button_layout.setContentsMargins(0, 0, 0, 0)
        #
        #     add_button = QPushButton("+")
        #
        #     # Add row function
        #     def add_row():
        #         # Open color dialog directly when adding a new row
        #         color_dialog = QColorDialog()
        #         color_dialog.setOption(QColorDialog.ShowAlphaChannel, True)
        #         if color_dialog.exec_():
        #             sel_col = color_dialog.selectedColor()
        #             row = table.rowCount()
        #             table.setRowCount(row + 1)
        #             add_colour_item(sel_col, row, table)
        #
        #     # Double-click to edit/select color for existing rows
        #     def on_cell_clicked(row, column):
        #         if column == 0:
        #             color_dialog = QColorDialog()
        #             color_dialog.setOption(QColorDialog.ShowAlphaChannel, True)
        #             current_item = table.item(row, column)
        #             current_color = current_item.data(Qt.UserRole)
        #             color_dialog.setCurrentColor(current_color)
        #             if color_dialog.exec_():
        #                 sel_col = color_dialog.selectedColor()
        #                 add_colour_item(sel_col, row, table)
        #
        #     # Connect to cellDoubleClicked signal
        #     table.cellDoubleClicked.connect(on_cell_clicked)
        #     add_button.clicked.connect(add_row)
        #     button_layout.addWidget(add_button)
        #
        #     # Set up context menu for deletion
        #     def show_context_menu(position):
        #         row = table.rowAt(position.y())
        #         if row >= 0:
        #             menu = QMenu()
        #             delete_action = menu.addAction("Delete")
        #             action = menu.exec_(table.viewport().mapToGlobal(position))
        #             if action == delete_action:
        #                 table.removeRow(row)
        #
        #     table.setContextMenuPolicy(Qt.CustomContextMenu)
        #     table.customContextMenuRequested.connect(show_context_menu)
        #
        #     # Create a container for the table and buttons
        #     container = QWidget()
        #     layout = QVBoxLayout(container)
        #     layout.addWidget(table)
        #     layout.addWidget(button_widget)
        #
        #     # Function to get the current value from the table
        #     def get_table_value():
        #         colours = []
        #         for row in range(table.rowCount()):
        #             try:
        #                 colour = table.item(row, 0).text()
        #                 colours.append(ast.literal_eval(colour))
        #             except (ValueError, AttributeError):
        #                 # Handle empty or invalid cells
        #                 pass
        #         return colours
        #
        #     # Store both the getter function and the reference to the table with the container
        #     container.get_value = get_table_value
        #     container.table_widget = table  # Store a reference to the actual table
        #
        #     widget = container

        elif prop_entry.prop_type == PropType.FILL:
            r, g, b, a = current_value
            widget = ColorPropertyWidget(QColor(r, g, b, a) or QColor(0, 0, 0, 255))
        else:  # Default to string type
            widget = QLineEdit(str(current_value) if current_value is not None else "")

        return widget

    def accept(self):
        """Apply properties and close dialog"""
        props_changed = {}

        # Update custom properties
        for prop_key, widget in self.property_widgets.items():
            if isinstance(widget, QSpinBox) or isinstance(widget, QDoubleSpinBox):
                value = widget.value()
            elif isinstance(widget, QCheckBox):
                value = widget.isChecked()
            elif isinstance(widget, QComboBox):
                value = widget.itemData(widget.currentIndex())
            elif isinstance(widget, QWidget) and hasattr(widget.layout(), 'itemAt') and widget.layout().count() > 0:
                value = widget.get_value()
            else:  # QLineEdit
                value = widget.text()

            old_val = self.node_item.node().get_property(prop_key)
            if old_val != value:
                props_changed[prop_key] = (copy.deepcopy(old_val), value)

        if props_changed:
            self.node_item.change_properties(props_changed)
        super().accept()
