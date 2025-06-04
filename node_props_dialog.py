import copy
from typing import Optional, cast

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPen
from PyQt5.QtWidgets import QDialog, QPushButton, QComboBox, QHBoxLayout, QWidget, QVBoxLayout, \
    QFormLayout, QDoubleSpinBox, QDialogButtonBox, QStyledItemDelegate, QColorDialog, QSpinBox, QCheckBox, \
    QGroupBox, QLabel, QLineEdit

from app_state import NodeState
from blaze_circle_def_table import BlazeCircleDefWidget
from colour_prop_widget import ColorPropertyWidget
from gradient_colour_table import GradOffsetColourWidget
from id_datatypes import PortId, PropKey, input_port, output_port, NodeId
from node_graph import NodeGraph
from node_manager import NodeInfo, NodeManager
from nodes.node_defs import PropDef, PortStatus, DisplayStatus
from nodes.prop_types import PT_Int, PT_Float, PT_Bool, PT_Point, PT_Fill, PT_Number, PT_String, \
    PT_List, PT_PointsHolder, PT_Enum, PT_ElementHolder, \
    PT_FillHolder, PT_GradOffset, PT_ValProbPairHolder, PT_BlazeCircleDef
from nodes.prop_values import PropValue, Enum, Point, PortRefTableEntry, Colour, LineRef, Bool
from point_dialog import PointDialog
from port_ref_table_widget import PortRefTableWidget
from random_probability_table import RandomProbabilityWidget


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
    def __init__(self, on_click_callback, port: PortId, adding, max_width=300, parent=None):
        super().__init__(parent)
        self.port = port
        self.adding = adding
        txt_display1 = "IN" if self.port.is_input else "OUT"
        txt_display2 = "input" if self.port.is_input else "output"
        self.text_pair = (f"{txt_display1} -", f"{txt_display1} +")
        self.description_pair = (f"Remove the {txt_display2} port for this property.",
                                 f"Add an {txt_display2} port to control this property.")
        self.setText(self.text_pair[int(self.adding)])
        self.setFixedSize(16, 16)
        self.max_width = max_width

        # Style the button to look like a help icon
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {"#4a90e2" if port.is_input else "#7ed321"};  /* Blue for input, Green for output */
                color: white;
                font-weight: bold;
                border-radius: 10px;
                border: none;
                padding: 1px 4px;
                font-size: 6px;
                min-width: 18px;
                min-height: 18px;
                max-width: 22px;
                max-height: 22px;
            }}
            QPushButton:hover {{
                background-color: {"#357ABD" if port.is_input else "#5DAA1E"};
            }}
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
            self.user_callback(self.port, not self.adding)


class NodePropertiesDialog(QDialog):
    """Dialog for editing node properties"""

    def __init__(self, node_item, parent=None):
        super().__init__(parent)
        self.node_item = node_item
        self.node_info: NodeInfo = node_item.node_info
        self.scene = node_item.scene()
        self.setWindowTitle(f"Properties: {self.node_info.name}")
        self.setMinimumWidth(400)
        self.ports_toggled: dict[PortId, bool] = {}  # bool is True if port opened

        # Main layout
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Create form layout for properties
        form_layout = QFormLayout()
        form_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

        self.property_widgets = {}

        # Add custom properties based on node type
        props_group = QGroupBox("Node Properties")
        props_layout = QFormLayout()
        props_group.setLayout(props_layout)

        port_only_displayal: list[PropKey] = []
        for key, prop_def in self.node_info.prop_defs.items():
            if prop_def.display_status == DisplayStatus.ANY_DISPLAY:
                widget: Optional[QWidget] = self.create_property_widget(prop_def,
                                                                        node_item.node_manager.get_internal_property(
                                                                            node_item.uid, key))
                if widget:
                    # Create the row with label and help icon
                    label_container, widget_container = self.create_property_row(key, prop_def, node_item, widget)
                    props_layout.addRow(label_container, widget_container)
                    self.property_widgets[key] = widget
                else:
                    port_only_displayal.append(key)
            elif prop_def.display_status == DisplayStatus.PORT_ONLY_DISPLAY:
                port_only_displayal.append(key)
        main_layout.addWidget(props_group)

        if port_only_displayal:
            no_widget_group = QGroupBox("Port modifiable properties")
            no_widget_group_layout = QFormLayout()
            no_widget_group.setLayout(no_widget_group_layout)

            for key in port_only_displayal:
                prop_def: PropDef = self.node_info.prop_defs[key]

                # Reuse the existing method, passing None as the widget
                label_container, widget_container = self.create_property_row(
                    key=key,
                    prop_def=prop_def,
                    node_item=node_item,
                    widget=None
                )
                no_widget_group_layout.addRow(label_container, widget_container)

            main_layout.addWidget(no_widget_group)

        # Create buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        main_layout.addLayout(form_layout)
        main_layout.addWidget(button_box)

    def change_property_port(self, port: PortId, adding):
        if adding:
            self.node_item.add_port(port)
        else:
            self.node_item.remove_port(port)
        self.ports_toggled[port] = adding

    def create_property_row(self, key: PropKey, prop_def: PropDef, node_item, widget=None):
        """Create a row with property label and a help icon to the right of the widget"""

        # Create a container widget for the label
        label_container = QWidget()
        label_layout = QHBoxLayout(label_container)
        label_layout.setContentsMargins(0, 0, 0, 0)
        label_layout.setSpacing(4)  # Small spacing between elements

        # Create the label
        add_text = ":" if prop_def.auto_format and widget else ""
        label = QLabel(prop_def.display_name + add_text)
        label_layout.addWidget(label)
        label_layout.addStretch()

        # Create a container for the widget and help icon
        widget_container = QWidget()
        widget_layout = QHBoxLayout(widget_container)
        widget_layout.setContentsMargins(0, 0, 0, 0)

        if widget:
            # Add the widget first
            widget_layout.addWidget(widget)

        # Add the help icon after the widget (on the right)
        if prop_def.description:
            help_icon = HelpIconLabel(prop_def.description, max_width=300)  # Set maximum width for tooltip
            widget_layout.addSpacing(1)
            widget_layout.addWidget(help_icon)
        # Add input and output toggle buttons
        if input_port(node=node_item.uid, key=key) in self.node_info.filter_ports_by_status(PortStatus.OPTIONAL,
                                                                                            get_output=False):
            widget_layout.addWidget(
                self.create_toggle_plus_minus_btn(cast(NodeState, node_item.node_state).ports_open, key, node_item.uid,
                                                  is_input=True))
        if output_port(node=node_item.uid, key=key) in self.node_info.filter_ports_by_status(PortStatus.OPTIONAL,
                                                                                             get_output=True):
            widget_layout.addWidget(
                self.create_toggle_plus_minus_btn(cast(NodeState, node_item.node_state).ports_open, key, node_item.uid,
                                                  is_input=False))

        return label_container, widget_container

    def create_toggle_plus_minus_btn(self, ports_open: list[PortId], key: PropKey, node: NodeId, is_input=True):
        keys_w_input = [port.key for port in ports_open if port.is_input == is_input]
        return ModifyPropertyPortButton(self.change_property_port,
                                        PortId(node=node, key=key, is_input=is_input),
                                        adding=key not in keys_w_input)

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
            widget.setChecked(bool(current_value) or False)

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
            x_spinbox.setDecimals(3)
            x_spinbox.setMinimum(-999999)
            x_spinbox.setMaximum(999999)

            y_spinbox = QDoubleSpinBox()
            y_spinbox.setDecimals(3)
            y_spinbox.setMinimum(-999999)
            y_spinbox.setMaximum(999999)

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
            enum: Enum = current_value
            widget = QComboBox()
            for display, data in enum.display_data_options:
                widget.addItem(display, userData=data)
            if current_value is not None:
                index = enum.options.index(enum.selected_option)
                widget.setCurrentIndex(index)


        elif isinstance(prop_type, PT_List):
            if isinstance(prop_type.base_item_type, PT_ElementHolder):
                port_ref_table = PortRefTableWidget(
                    list_item_type=PT_ElementHolder(),
                    ref_querier=lambda ref: cast(NodeGraph, self.scene.node_graph).query_ref(node=self.node_item.uid,
                                                                                             ref=ref),
                    node_manager=self.node_item.node_manager,
                    table_heading="Drawings",
                    entries=current_value
                )
                widget = port_ref_table

            elif isinstance(prop_type.base_item_type, PT_PointsHolder):
                def text_callback(ref_port: Optional[PortId], node_manager: Optional[NodeManager], entry_group):
                    first_entry = entry_group[0]
                    if isinstance(first_entry, LineRef):
                        node_info: NodeInfo = node_manager.node_info(ref_port.node)
                        start_x, start_y = first_entry.points[0]
                        stop_x, stop_y = entry_group[-1].points[-1]
                        arrow = '←' if first_entry.is_reversed else '→'
                        return f"{node_info.base_name} (id: {ref_port.node})\n({start_x:.3f}, {start_y:.3f}) {arrow} ({stop_x:.3f}, {stop_y:.3f})"
                    assert isinstance(first_entry, Point)
                    x, y = first_entry
                    return f"({x:.3f}, {y:.3f})"

                def custom_context_menu(menu, entry_group):
                    if isinstance(entry_group[0], LineRef):
                        menu.actions_map = {'reverse': menu.addAction("Reverse")}
                    else:
                        # Ordinary point
                        menu.actions_map = {'edit': menu.addAction("Edit")}

                def edit_action(table, entry_group, row):
                    point_dialog = PointDialog(*entry_group[0])
                    if point_dialog.exec_() == QDialog.Accepted:
                        x, y = point_dialog.get_value()
                        table.set_item([Point(x, y)], row)

                def reverse_action(table, line_ref_entry_group, row):
                    new_entry_group = copy.deepcopy(line_ref_entry_group)
                    for entry in new_entry_group:
                        entry.toggle_reverse()
                    new_entry_group.reverse()
                    table.set_item(new_entry_group, row)

                def add_action(table):
                    point_dialog = PointDialog()
                    if point_dialog.exec_() == QDialog.Accepted:
                        x, y = point_dialog.get_value()
                        row = table.row_count()
                        table.set_row_count(row + 1)
                        table.set_item([Point(x, y)], row)

                port_ref_table = PortRefTableWidget(
                    list_item_type=PT_PointsHolder(),
                    ref_querier=lambda ref: cast(NodeGraph, self.scene.node_graph).query_ref(node=self.node_item.uid,
                                                                                             ref=ref),
                    node_manager=self.node_item.node_manager,
                    table_heading="Points (X, Y)",
                    entries=current_value,
                    text_callback=text_callback,
                    context_menu_callback=custom_context_menu,
                    additional_actions={'edit': edit_action, 'reverse': reverse_action, 'add': add_action}
                )
                widget = port_ref_table

            elif isinstance(prop_type.base_item_type, PT_FillHolder):
                # Custom delegate to display colour swatches
                class ColourDelegate(QStyledItemDelegate):
                    def paint(self, painter, option, index):
                        first_entry = index.data(Qt.UserRole)[0]

                        if not isinstance(first_entry, PortRefTableEntry):
                            assert isinstance(first_entry, Colour)
                            q_colour = QColor(*first_entry)
                            painter.fillRect(option.rect, q_colour)

                            # Draw a border
                            painter.setPen(QPen(Qt.black, 1))
                            painter.drawRect(option.rect.adjusted(0, 0, -1, -1))
                        else:
                            # Otherwise, fall back to the default behavior (centered text)
                            super().paint(painter, option, index)

                    def initStyleOption(self, option, index):
                        super().initStyleOption(option, index)
                        option.displayAlignment = Qt.AlignCenter

                def custom_context_menu(menu, entry_group):
                    if isinstance(entry_group[0], Colour):
                        menu.actions_map = {'edit': menu.addAction("Edit")}

                def edit_action(port_ref_table, entry_group, row):
                    first_entry = entry_group[0]
                    assert isinstance(first_entry, Colour)
                    colour_dialog = QColorDialog(QColor(*first_entry))
                    colour_dialog.setOption(QColorDialog.ShowAlphaChannel, True)
                    if colour_dialog.exec_() == QDialog.Accepted:
                        sel_col = colour_dialog.selectedColor().getRgb()
                        port_ref_table.set_item([Colour(*sel_col)], row)

                def add_action(port_ref_table):
                    colour_dialog = QColorDialog()
                    colour_dialog.setOption(QColorDialog.ShowAlphaChannel, True)
                    if colour_dialog.exec_() == QDialog.Accepted:
                        sel_col = colour_dialog.selectedColor().getRgb()
                        row = port_ref_table.row_count()
                        port_ref_table.set_row_count(row + 1)
                        port_ref_table.set_item([Colour(*sel_col)], row)

                port_ref_table = PortRefTableWidget(
                    list_item_type=PT_FillHolder(),
                    ref_querier=lambda ref: cast(NodeGraph, self.scene.node_graph).query_ref(node=self.node_item.uid,
                                                                                             ref=ref),
                    node_manager=self.node_item.node_manager,
                    table_heading="Colour",
                    entries=current_value,
                    context_menu_callback=custom_context_menu,
                    additional_actions={'edit': edit_action, 'add': add_action},
                    item_delegate=ColourDelegate()
                )
                widget = port_ref_table
            elif isinstance(prop_type.base_item_type, PT_GradOffset):
                widget = GradOffsetColourWidget(entries=current_value)
            elif isinstance(prop_type.base_item_type, PT_ValProbPairHolder):
                widget = RandomProbabilityWidget(
                    ref_querier=lambda ref: cast(NodeGraph, self.scene.node_graph).query_ref(node=self.node_item.uid,
                                                                                             ref=ref),
                    node_manager=self.node_item.node_manager,
                    entries=current_value
                )
            elif isinstance(prop_type.base_item_type, PT_BlazeCircleDef):
                widget = BlazeCircleDefWidget(entries=current_value)
        elif isinstance(prop_type, PT_Fill):
            assert isinstance(current_value, Colour)
            widget = ColorPropertyWidget(current_value)
        elif isinstance(prop_type, PT_String):  # Default to string type
            widget = QLineEdit(str(current_value) if current_value is not None else "")
            widget.setMinimumWidth(250)

        return widget

    def accept(self):
        """Apply properties and close dialog"""
        props_changed = {}

        # Update custom properties
        for prop_key, widget in self.property_widgets.items():
            if isinstance(widget, QSpinBox) or isinstance(widget, QDoubleSpinBox):
                value = widget.value()
            elif isinstance(widget, QCheckBox):
                value = Bool(widget.isChecked())
            elif isinstance(widget, QComboBox):
                display_options = [widget.itemText(i) for i in range(widget.count())]
                options = [widget.itemData(i) for i in range(widget.count())]
                selected_option = widget.itemData(widget.currentIndex())
                value = Enum(options=options, display_options=display_options, selected_option=selected_option)
            elif isinstance(widget, QWidget) and hasattr(widget.layout(), 'itemAt') and widget.layout().count() > 0:
                value = widget.get_value()
            else:  # QLineEdit
                value = widget.text()

            old_val = cast(NodeManager, self.node_item.node_manager).get_internal_property(self.node_item.uid, prop_key)
            if old_val != value:
                props_changed[prop_key] = (copy.deepcopy(old_val), value)

        if props_changed:
            self.node_item.change_properties(props_changed, self.ports_toggled)
        super().accept()
