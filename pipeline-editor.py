import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QGraphicsScene, QGraphicsView, 
                            QGraphicsItem, QGraphicsRectItem, QGraphicsEllipseItem, 
                            QGraphicsLineItem, QMenu, QAction, QInputDialog, QColorDialog)
from PyQt5.QtCore import Qt, QLineF, pyqtSignal, QObject
from PyQt5.QtGui import QPen, QBrush, QColor, QPainter, QFont


class ConnectionSignals(QObject):
    """Signals for the connection process"""
    connectionStarted = pyqtSignal(object)  # Emits the source port
    connectionMade = pyqtSignal(object, object)  # Emits source and destination ports


class NodeItem(QGraphicsRectItem):
    """Represents a node/box in the pipeline"""
    
    def __init__(self, x, y, width, height, title="Node", color=QColor(200, 230, 250)):
        super().__init__(0, 0, width, height)
        self.setPos(x, y)
        self.setZValue(1)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        
        self.setBrush(QBrush(color))
        self.setPen(QPen(Qt.black, 2))
        
        self.title = title
        self.input_ports = []
        self.output_ports = []
        self.create_ports()
        
    def create_ports(self):
        # Create input port (left side)
        input_port = PortItem(self, -10, self.rect().height() / 2, is_input=True)
        self.input_ports.append(input_port)
        
        # Create output port (right side)
        output_port = PortItem(self, self.rect().width() + 10, self.rect().height() / 2, is_input=False)
        self.output_ports.append(output_port)
        
    def paint(self, painter, option, widget):
        super().paint(painter, option, widget)
        
        # Draw node title
        painter.setFont(QFont("Arial", 10))
        painter.drawText(self.rect(), Qt.AlignCenter, self.title)
        
    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            # Update connected edges when node moves
            for port in self.input_ports + self.output_ports:
                for edge in port.edges:
                    edge.update_position()
                    
        return super().itemChange(change, value)


class PortItem(QGraphicsEllipseItem):
    """Represents connection points on nodes"""
    
    def __init__(self, parent, x, y, is_input=True):
        size = 12  # Slightly larger port for easier clicking
        super().__init__(-size/2, -size/2, size, size, parent)
        self.setPos(x, y)
        self.setZValue(1)
        self.is_input = is_input
        self.edges = []
        
        # Make port interactive
        self.setAcceptHoverEvents(True)
        
        if is_input:
            self.setBrush(QBrush(QColor(100, 100, 100)))
            self.setCursor(Qt.ArrowCursor)
        else:
            self.setBrush(QBrush(QColor(50, 150, 50)))
            self.setCursor(Qt.CrossCursor)  # Shows + cursor when hovering output ports
        
        self.setPen(QPen(Qt.black, 1))
        
    def add_edge(self, edge):
        self.edges.append(edge)
    
    def remove_edge(self, edge):
        if edge in self.edges:
            self.edges.remove(edge)
    
    def get_center_scene_pos(self):
        return self.mapToScene(self.rect().center())
    
    def hoverEnterEvent(self, event):
        # Highlight port on hover
        self.setPen(QPen(Qt.red, 2))
        if not self.is_input:
            # Change cursor for output ports to indicate dragging availability
            self.setCursor(Qt.CrossCursor)
        super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event):
        self.setPen(QPen(Qt.black, 1))
        super().hoverLeaveEvent(event)
    

class EdgeItem(QGraphicsLineItem):
    """Represents connections between nodes"""
    
    def __init__(self, source_port, dest_port):
        super().__init__()
        self.setZValue(0)

        self.source_port = source_port
        self.dest_port = dest_port
        
        self.source_port.add_edge(self)
        self.dest_port.add_edge(self)
        
        # Thicker line with rounded caps for better appearance
        self.setPen(QPen(Qt.black, 2.5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        
        self.update_position()
    
    def update_position(self):
        if self.source_port and self.dest_port:
            source_pos = self.source_port.get_center_scene_pos()
            dest_pos = self.dest_port.get_center_scene_pos()
            self.setLine(QLineF(source_pos, dest_pos))


class PipelineScene(QGraphicsScene):
    """Scene that contains all pipeline elements"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSceneRect(0, 0, 2000, 2000)
        
        # Connection related variables
        self.connection_signals = ConnectionSignals()
        self.active_connection = None
        self.temp_line = None
        self.source_port = None
        self.dest_port = None
        
        # Connect signals
        self.connection_signals.connectionStarted.connect(self.start_connection)
        self.connection_signals.connectionMade.connect(self.finish_connection)
        
    def start_connection(self, source_port):
        """Start creating a connection from the given source port"""
        if source_port and not source_port.is_input:
            self.source_port = source_port
            start_pos = source_port.get_center_scene_pos()
            
            # Create a temporary line for visual feedback
            self.temp_line = QGraphicsLineItem()
            self.temp_line.setLine(QLineF(start_pos, start_pos))
            self.temp_line.setPen(QPen(Qt.darkGray, 2, Qt.DashLine))
            self.addItem(self.temp_line)
    
    def update_temp_connection(self, end_pos):
        """Update the temporary connection line to the current mouse position"""
        if self.source_port and self.temp_line:
            start_pos = self.source_port.get_center_scene_pos()
            self.temp_line.setLine(QLineF(start_pos, end_pos))
    
    def finish_connection(self, source_port, dest_port):
        """Create a permanent connection between source and destination ports"""
        if source_port and dest_port and source_port != dest_port:
            # Don't connect if they're on the same node
            if source_port.parentItem() != dest_port.parentItem():
                # Check if connection already exists
                connection_exists = False
                for edge in source_port.edges:
                    if hasattr(edge, 'dest_port') and edge.dest_port == dest_port:
                        connection_exists = True
                        break
                
                if not connection_exists:
                    edge = EdgeItem(source_port, dest_port)
                    self.addItem(edge)
        
        # Clean up temporary line
        if self.temp_line:
            self.removeItem(self.temp_line)
            self.temp_line = None
        
        # Reset ports
        self.source_port = None
        self.dest_port = None
    
    def mousePressEvent(self, event):
        """Handle mouse press events for the scene"""
        if event.button() == Qt.LeftButton:
            item = self.itemAt(event.scenePos(), QGraphicsView.transform(self.views()[0]))
            
            if isinstance(item, PortItem) and not item.is_input:
                # Start creating a connection if an output port is clicked
                self.connection_signals.connectionStarted.emit(item)
                event.accept()
                return
        
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move events for the scene"""
        if self.source_port and self.temp_line:
            self.update_temp_connection(event.scenePos())
            
            # Highlight input port if we're hovering over one
            item = self.itemAt(event.scenePos(), QGraphicsView.transform(self.views()[0]))
            if isinstance(item, PortItem) and item.is_input:
                if self.dest_port != item:
                    # Reset previous dest port highlighting
                    if self.dest_port:
                        self.dest_port.setPen(QPen(Qt.black, 1))
                    
                    # Set new dest port
                    self.dest_port = item
                    self.dest_port.setPen(QPen(Qt.red, 2))
            elif self.dest_port:
                # Reset dest port highlighting if not hovering over an input port
                self.dest_port.setPen(QPen(Qt.black, 1))
                self.dest_port = None
            
            event.accept()
            return
            
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release events for the scene"""
        if event.button() == Qt.LeftButton and self.source_port:
            item = self.itemAt(event.scenePos(), QGraphicsView.transform(self.views()[0]))
            if isinstance(item, PortItem) and item.is_input:
                # Create permanent connection
                self.connection_signals.connectionMade.emit(self.source_port, item)
                event.accept()
                return
            else:
                # Clean up if not released over an input port
                if self.temp_line:
                    self.removeItem(self.temp_line)
                    self.temp_line = None
                self.source_port = None
                
                # Reset dest port highlighting if needed
                if self.dest_port:
                    self.dest_port.setPen(QPen(Qt.black, 1))
                    self.dest_port = None
        
        super().mouseReleaseEvent(event)
    
    def contextMenuEvent(self, event):
        """Handle context menu events for the scene"""
        clicked_item = self.itemAt(event.scenePos(), QGraphicsView.transform(self.views()[0]))
        
        if isinstance(clicked_item, EdgeItem):
            # Context menu for connections
            menu = QMenu()
            delete_action = QAction("Delete Connection", menu)
            delete_action.triggered.connect(lambda: self.delete_edge(clicked_item))
            menu.addAction(delete_action)
            menu.exec_(event.screenPos())
        elif isinstance(clicked_item, NodeItem) or isinstance(clicked_item, PortItem):
            # Context menu for nodes (or ports on nodes)
            if isinstance(clicked_item, PortItem):
                clicked_item = clicked_item.parentItem()
                
            menu = QMenu()
            rename_action = QAction("Rename Node", menu)
            rename_action.triggered.connect(lambda: self.rename_node(clicked_item))
            
            change_color_action = QAction("Change Color", menu)
            change_color_action.triggered.connect(lambda: self.change_node_color(clicked_item))
            
            delete_action = QAction("Delete Node", menu)
            delete_action.triggered.connect(lambda: self.delete_node(clicked_item))
            
            menu.addAction(rename_action)
            menu.addAction(change_color_action)
            menu.addAction(delete_action)
            menu.exec_(event.screenPos())
        elif event.scenePos().x() >= 0 and event.scenePos().y() >= 0:
            # Context menu for empty space
            menu = QMenu()
            add_action = QAction("Add Node", menu)
            add_action.triggered.connect(lambda: self.add_node(event.scenePos()))
            menu.addAction(add_action)
            menu.exec_(event.screenPos())
    
    def nodes(self):
        """Return all nodes in the scene"""
        return [item for item in self.items() if isinstance(item, NodeItem)]
    
    def add_node(self, pos):
        """Add a new node at the given position"""
        node_name, ok = QInputDialog.getText(None, "New Node", "Enter node name:")
        if ok and node_name:
            new_node = NodeItem(pos.x(), pos.y(), 150, 80, node_name)
            self.addItem(new_node)
    
    def rename_node(self, node):
        """Rename the given node"""
        new_name, ok = QInputDialog.getText(None, "Rename Node", "Enter new name:", text=node.title)
        if ok and new_name:
            node.title = new_name
            node.update()
    
    def change_node_color(self, node):
        """Change the color of the given node"""
        color = QColorDialog.getColor(node.brush().color(), None, "Select Node Color")
        if color.isValid():
            node.setBrush(QBrush(color))
    
    def delete_edge(self, edge):
        """Delete the given edge"""
        edge.source_port.remove_edge(edge)
        edge.dest_port.remove_edge(edge)
        self.removeItem(edge)
    
    def delete_node(self, node):
        """Delete the given node and all its connections"""
        # Remove all connected edges first
        for port in node.input_ports + node.output_ports:
            for edge in list(port.edges):  # Use a copy to avoid issues while removing
                self.delete_edge(edge)
        
        self.removeItem(node)


class PipelineView(QGraphicsView):
    """View to interact with the pipeline scene"""
    
    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.setRenderHint(QPainter.Antialiasing)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setBackgroundBrush(QBrush(QColor(240, 240, 240)))
        
        # Add grid lines
        self.draw_grid()
    
    def draw_grid(self):
        """Draw a grid background for the scene"""
        grid_size = 20
        scene_rect = self.scene().sceneRect()
        
        # Draw vertical lines
        for x in range(0, int(scene_rect.width()), grid_size):
            line = QGraphicsLineItem(x, 0, x, scene_rect.height())
            line.setPen(QPen(QColor(200, 200, 200), 1))
            line.setZValue(-1000)  # Place behind all other items
            self.scene().addItem(line)
        
        # Draw horizontal lines
        for y in range(0, int(scene_rect.height()), grid_size):
            line = QGraphicsLineItem(0, y, scene_rect.width(), y)
            line.setPen(QPen(QColor(200, 200, 200), 1))
            line.setZValue(-1000)  # Place behind all other items
            self.scene().addItem(line)
    
    def mousePressEvent(self, event):
        """Handle mouse press events for the view"""
        if event.button() == Qt.MiddleButton:
            self.setDragMode(QGraphicsView.ScrollHandDrag)
            # Create a fake mouse press event to initiate the drag
            fake_event = event
            fake_event.button = lambda: Qt.LeftButton
            super().mousePressEvent(fake_event)
        else:
            super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release events for the view"""
        if event.button() == Qt.MiddleButton:
            self.setDragMode(QGraphicsView.RubberBandDrag)
        
        super().mouseReleaseEvent(event)


class PipelineEditor(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pipeline Editor")
        self.setGeometry(100, 100, 1000, 800)
        
        # Create the scene and view
        self.scene = PipelineScene()
        self.view = PipelineView(self.scene)
        self.setCentralWidget(self.view)
        
        # Add some example nodes
        self.add_example_nodes()
        
        # Create a status bar with instructions
        self.statusBar().showMessage("Drag from output port (green) to input port (gray) to create connections")
        
        self.show()
    
    def add_example_nodes(self):
        """Add some example nodes to the scene"""
        node1 = NodeItem(100, 100, 150, 80, "Data Source")
        node2 = NodeItem(400, 100, 150, 80, "Transform")
        node3 = NodeItem(400, 250, 150, 80, "Filter")
        node4 = NodeItem(700, 175, 150, 80, "Output")
        
        for node in [node1, node2, node3, node4]:
            self.scene.addItem(node)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    editor = PipelineEditor()
    sys.exit(app.exec_())