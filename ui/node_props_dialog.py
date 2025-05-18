import copy
from typing import Optional, cast

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPen
from PyQt5.QtWidgets import QDialog, QPushButton, QComboBox, QHBoxLayout, QWidget, QVBoxLayout, \
    QFormLayout, QDoubleSpinBox, QDialogButtonBox, QStyledItemDelegate, QColorDialog, QSpinBox, QCheckBox, \
    QGroupBox, QLabel, QLineEdit

from ui.colour_prop_widget import ColorPropertyWidget
from ui.id_datatypes import PortId, PropKey, input_port
from ui.node_graph import NodeGraph
from ui.node_manager import NodeInfo, NodeManager
from ui.nodes.prop_defs import PT_Int, PT_Float, PT_Bool, PT_Point, PT_Enum, \
    LineRef, PT_Fill, PT_Number, PortRefTableEntry, PortStatus, PropDef, PropValue, \
    PT_String, PT_Colour, List, Point, PT_List, PT_PointsHolder, PT_Element, PT_TableEntry
from ui.point_dialog import PointDialog
from ui.port_ref_table_widget import PortRefTableWidget


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
        self.node_info: NodeInfo = node_item.node_info
        self.scene = node_item.scene()
        self.setWindowTitle(f"Properties: {self.node_info.name}")
        self.setMinimumWidth(400)

        # Main layout
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Create form layout for properties
        form_layout = QFormLayout()
        form_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

        self.property_widgets = {}

        # Add custom properties based on node type
        if self.node_info.prop_defs:
            props_group = QGroupBox("Node Properties")
            props_layout = QFormLayout()
            props_group.setLayout(props_layout)

            for key, prop_def in self.node_info.prop_defs.items():
                if prop_def.display_in_props:
                    widget: Optional[QWidget] = self.create_property_widget(prop_def, node_item.node_manager.get_internal_property(node_item.uid, key))
                    if widget:
                        # Create the row with label and help icon
                        label_container, widget_container = self.create_property_row(key, prop_def, widget,
                                                                                     node_item)
                        props_layout.addRow(label_container, widget_container)
                        self.property_widgets[key] = widget
            main_layout.addWidget(props_group)

        # input_ports_open: list[PortId] = [port for port in node_item.node_state.ports_open if port.is_input]
        # for port in self.node_info.filter_ports_by_status(PortStatus.OPTIONAL, get_output=False):
        #     if port_def.optional and port_def.description and (port_key not in node_item.node().get_prop_entries()):
        #         # Add label with property button
        #         if not port_only_group:
        #             port_only_group = QGroupBox("Port modifiable properties")
        #             port_only_group_layout = QVBoxLayout(port_only_group)  # Create a vertical layout for the group
        #             port_only_group.setLayout(port_only_group_layout)  # Set the layout for the group
        #
        #         widget_container = QWidget()  # This will be a widget inside the group
        #         widget_layout = QHBoxLayout(widget_container)
        #         widget_layout.setContentsMargins(0, 0, 0, 0)
        #         widget_layout.setSpacing(4)
        #
        #         text = f"{port_def.display_name}: {port_def.description}"
        #
        #         # Create and add label
        #         label = QLabel(text)
        #         widget_layout.addWidget(label)
        #
        #         # Add plus/minus buttons based on port state
        #         if port in input_ports_open:
        #             # If port is open, add minus button to remove the port
        #             minus_btn = ModifyPropertyPortButton(self.change_property_port, port_key, adding=False)
        #             widget_layout.addWidget(minus_btn)
        #         else:
        #             # If port is not open, add plus button to add the port
        #             plus_btn = ModifyPropertyPortButton(self.change_property_port, port_key, adding=True)
        #             widget_layout.addWidget(plus_btn)
        #
        #         # Add the widget container (with layout) to the group
        #         port_only_group_layout.addWidget(widget_container)
        #
        # # If port_only_group was created, add it to the main layout
        # if port_only_group:
        #     main_layout.addWidget(port_only_group)

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

    def create_property_row(self, key: PropKey, prop_def: PropDef, widget, node_item):
        """Create a row with property label and a help icon to the right of the widget"""

        # Create a container widget for the label
        label_container = QWidget()
        label_layout = QHBoxLayout(label_container)
        label_layout.setContentsMargins(0, 0, 0, 0)
        label_layout.setSpacing(4)  # Small spacing between elements

        # Create the label
        add_text = ":" if prop_def.auto_format else ""
        label = QLabel(prop_def.display_name + add_text)
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
        if prop_def.description:
            help_icon = HelpIconLabel(prop_def.description, max_width=300)  # Set maximum width for tooltip
            widget_layout.addWidget(help_icon)
        if input_port(node=node_item.uid, key=key) in self.node_info.filter_ports_by_status(PortStatus.OPTIONAL, get_output=False):
            input_ports_open = [port for port in node_item.node_state.ports_open if port.is_input]
            if key in input_ports_open:
                # Exists port to modify this property, add minus button
                minus_btn = ModifyPropertyPortButton(self.change_property_port,
                                                     key,
                                                     adding=False)  # Set maximum width for tooltip
                widget_layout.addWidget(minus_btn)
            else:
                # Does not exist port to modify this property, add plus button
                plus_btn = ModifyPropertyPortButton(self.change_property_port, key,
                                                    adding=True)  # Set maximum width for tooltip
                widget_layout.addWidget(plus_btn)

        return label_container, widget_container

    def create_property_widget(self, prop_def: PropDef, current_value: Optional[PropValue]) -> Optional[QWidget]:
        prop_type = prop_def.prop_type
        widget: Optional[QWidget] = None
        """Create an appropriate widget for the property type"""
        if isinstance(prop_type, PT_Number):
            if isinstance(prop_type, PT_Int):
                widget = QSpinBox()
            else:
                assert isinstance(prop_type, PT_Float)
                widget = QDoubleSpinBox()
                widget.setDecimals(prop_type.decimals)
            # Set minimum and maximum values
            widget.setMinimum(prop_type.min_value)
            widget.setMaximum(prop_type.max_value)
            # Set value
            widget.setValue(current_value or 0)

        elif isinstance(prop_type, PT_Bool):
            widget = QCheckBox()
            widget.setChecked(current_value or False)

        elif isinstance(prop_type, PT_Point):
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

        elif isinstance(prop_type, PT_Enum):
            widget = QComboBox()
            for display, data in prop_type.display_data_options():
                widget.addItem(display, userData=data)
            if current_value is not None:
                index = prop_type.get_options().index(current_value) if current_value in prop_type.get_options() else 0
                widget.setCurrentIndex(index)


        elif isinstance(prop_type, PT_List):
            if isinstance(prop_type.base_item_type, PT_TableEntry) and isinstance(prop_type.base_item_type.data_type, PT_Element):
                port_ref_table = PortRefTableWidget(
                    list_item_type=PT_Element(),
                    ref_querier=lambda ref: cast(NodeGraph, self.scene.node_graph).query_ref(node=self.node_item.uid,
                                                                                             ref=ref),
                    node_manager=self.node_item.node_manager,
                    table_heading="Drawings",
                    entries=current_value
                )
                widget = port_ref_table

            if isinstance(prop_type.base_item_type, PT_PointsHolder):
                def text_callback(ref_port: Optional[PortId], node_manager: Optional[NodeManager], table_entry):
                    if isinstance(table_entry, LineRef):
                        node_info: NodeInfo = node_manager.node_info(ref_port.node)
                        start_x, start_y = table_entry.points[0]
                        stop_x, stop_y = table_entry.points[-1]
                        arrow = '←' if table_entry.is_reversed else '→'
                        return f"{node_info.base_name} (id: {ref_port.node})\n({start_x:.2f}, {start_y:.2f}) {arrow} ({stop_x:.2f}, {stop_y:.2f})"
                    assert isinstance(table_entry, Point)
                    x, y = table_entry
                    return f"({x:.2f}, {y:.2f})"

                def custom_context_menu(menu, table_entry):
                    if isinstance(table_entry, LineRef):
                        menu.actions_map = {'reverse': menu.addAction("Reverse")}
                    else:
                        # Ordinary point
                        menu.actions_map = {'edit': menu.addAction("Edit")}

                def edit_action(table, point, row):
                    point_dialog = PointDialog(*point)
                    if point_dialog.exec_() == QDialog.Accepted:
                        x, y = point_dialog.get_value()
                        table.set_item(Point(x, y), row)

                def reverse_action(table, line_ref_entry, row):
                    new_line_ref_entry = copy.deepcopy(line_ref_entry)
                    new_line_ref_entry.toggle_reverse()
                    table.set_item(new_line_ref_entry, row)

                def add_action(table):
                    point_dialog = PointDialog()
                    if point_dialog.exec_() == QDialog.Accepted:
                        x, y = point_dialog.get_value()
                        row = table.row_count()
                        table.set_row_count(row + 1)
                        table.set_item(Point(x, y), row)

                port_ref_table = PortRefTableWidget(
                    list_item_type=PT_PointsHolder(),
                    ref_querier=lambda ref: cast(NodeGraph, self.scene.node_graph).query_ref(node=self.node_item.uid, ref=ref),
                    node_manager=self.node_item.node_manager,
                    table_heading="Points (X, Y)",
                    entries=current_value,
                    text_callback=text_callback,
                    context_menu_callback=custom_context_menu,
                    additional_actions={'edit': edit_action, 'reverse': reverse_action, 'add': add_action}
                )
                widget = port_ref_table

        # elif isinstance(prop_type, PT_ColourRefTable):
        #     # Custom delegate to display colour swatches
        #     class ColourDelegate(QStyledItemDelegate):
        #         def paint(self, painter, option, index):
        #             value = index.data(Qt.UserRole)
        #
        #             if not isinstance(value, PortRefTableEntry):
        #                 q_colour = QColor(*value)
        #                 painter.fillRect(option.rect, q_colour)
        #
        #                 # Draw a border
        #                 painter.setPen(QPen(Qt.black, 1))
        #                 painter.drawRect(option.rect.adjusted(0, 0, -1, -1))
        #             else:
        #                 # Otherwise, fall back to the default behavior (centered text)
        #                 super().paint(painter, option, index)
        #
        #         def initStyleOption(self, option, index):
        #             super().initStyleOption(option, index)
        #             option.displayAlignment = Qt.AlignCenter
        #
        #     def custom_context_menu(menu, _):
        #         menu.actions_map = {'edit': menu.addAction("Edit")}
        #
        #     def edit_action(port_ref_table, _, row):
        #         colour_dialog = QColorDialog()
        #         colour_dialog.setOption(QColorDialog.ShowAlphaChannel, True)
        #         if colour_dialog.exec_() == QDialog.Accepted:
        #             sel_col = colour_dialog.selectedColor().getRgb()
        #             port_ref_table.set_item(sel_col, row)
        #
        #     def add_action(port_ref_table):
        #         colour_dialog = QColorDialog()
        #         colour_dialog.setOption(QColorDialog.ShowAlphaChannel, True)
        #         if colour_dialog.exec_() == QDialog.Accepted:
        #             sel_col = colour_dialog.selectedColor().getRgb()
        #             row = port_ref_table.row_count()
        #             port_ref_table.set_row_count(row + 1)
        #             port_ref_table.set_item(sel_col, row)
        #
        #     port_ref_table = PortRefTableWidget(
        #         port_ref_getter=lambda ref_id: self.scene.graph_querier.get_port_ref(self.node_item.node_state.node,
        #                                                                              prop_def.prop_type.linked_port_key,
        #                                                                              ref_id),
        #         table_heading="Colour",
        #         entries=current_value,
        #         context_menu_callback=custom_context_menu,
        #         additional_actions={'edit': edit_action, 'add': add_action},
        #         item_delegate=ColourDelegate()
        #     )
        #     widget = port_ref_table
        elif isinstance(prop_type, PT_Fill):
            r, g, b, a = current_value
            widget = ColorPropertyWidget(QColor(r, g, b, a) or QColor(0, 0, 0, 255))
        elif isinstance(prop_type, PT_String):  # Default to string type
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

            old_val = cast(NodeManager, self.node_item.node_manager).get_internal_property(self.node_item.uid, prop_key)
            if old_val != value:
                props_changed[prop_key] = (copy.deepcopy(old_val), value)

        if props_changed:
            self.node_item.change_properties(props_changed)
        super().accept()
