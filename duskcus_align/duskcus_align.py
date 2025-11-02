from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from krita import *
import enum


class DuskcusAlign(Extension):
 
    def __init__(self, parent):
        super().__init__(parent)
 
    def setup(self):
        pass
 
    def createActions(self, window):
        pass

 
Krita.instance().addExtension(DuskcusAlign(Krita.instance()))


class EdgeAlignType(enum.Enum):
    centre = 0
    horiz = 1
    vert = 2
    grid = 3


def get_bounds_centre(curr_doc):
    """Get centre of the document/canvas."""
    coords = [0, 0]
    coords[0] = round(curr_doc.width() / 2)
    coords[1] = round(curr_doc.height() / 2)
    return coords


def get_bounds_centre(node):
    coords = [0, 0]
    lb = node.bounds()
    coords[0] = lb.x() + round(lb.width() / 2)
    coords[1] = lb.y() + round(lb.height() / 2)
    return coords


def get_move_coordinates(node, sc, pivot=[0.5, 0.5]):
    """Calculate move coordinates with adjustable pivot point. pivot: [0.5, 0.5] = centre, [0, 0] = top-left, [1, 1] = bottom-right, etc."""
    lb = node.bounds()
    # Calculate current position of the pivot point on the layer
    pivot_x = lb.x() + round(lb.width() * pivot[0])
    pivot_y = lb.y() + round(lb.height() * pivot[1])
    
    mc = [0, 0]
    mc[0] = sc[0] - pivot_x
    mc[1] = sc[1] - pivot_y
    return mc


def move_children(node, pos_offset):
    """Recursively move all child nodes by the position offset."""
    n_children = node.childNodes()
    for ch in n_children:
        pos = ch.position()
        ch.move(pos.x() + pos_offset.x(), pos.y() + pos_offset.y())
        move_children(ch, pos_offset)


def apply_align_type(align_type, node, curr_doc, grid_position=None):
    """Calculate target position and pivot point based on alignment type. grid_position: tuple (row, col) where row and col are 0-2 Returns: (targetX, targetY, pivotX, pivotY) """
    doc_width = curr_doc.width()
    doc_height = curr_doc.height()
    doc_centre_x = round(doc_width / 2)
    doc_centre_y = round(doc_height / 2)
    
    if align_type == EdgeAlignType.centre:
        # Use the same approach as horiz/vert for consistency
        lb = node.bounds()
        return [doc_centre_x, doc_centre_y], [0.5, 0.5]
    
    if align_type == EdgeAlignType.horiz:
        # For horizontal, keep the current Y position (not the center of the layer)
        lb = node.bounds()
        return [doc_centre_x, lb.y()], [0.5, 0]
    
    if align_type == EdgeAlignType.vert:
        # For vertical, keep the current X position (not the center of the layer)
        lb = node.bounds()
        return [lb.x(), doc_centre_y], [0, 0.5]
    
    if align_type == EdgeAlignType.grid and grid_position is not None:
        row, col = grid_position
        
        # Map grid position to target coordinates and pivot
        # Columns: 0=left, 1=center, 2=right
        # Rows: 0=top, 1=center, 2=bottom
        
        # For center position (1,1), use the same logic as horiz+vert buttons
        if row == 1 and col == 1:
            return [doc_centre_x, doc_centre_y], [0.5, 0.5]
        
        target_x_map = {0: 0, 1: doc_centre_x, 2: doc_width}
        target_y_map = {0: 0, 1: doc_centre_y, 2: doc_height}
        pivot_x_map = {0: 0, 1: 0.5, 2: 1}
        pivot_y_map = {0: 0, 1: 0.5, 2: 1}
        
        target_pos = [target_x_map[col], target_y_map[row]]
        pivot = [pivot_x_map[col], pivot_y_map[row]]
        
        return target_pos, pivot
    
    # Default to centre
    return [doc_centre_x, doc_centre_y], [0.5, 0.5]


class AlignToSelectionDocker(DockWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("DuskcuS Align")
        self.offset_x_spinbox = None
        self.offset_y_spinbox = None
        self.create_align_docker()

    def create_align_docker(self):
        # Create the main horizontal layout - everything in one row
        main_layout = QHBoxLayout()
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setAlignment(Qt.AlignLeft)
        
        # Quick align buttons (existing functionality)
        align_horiz_button = QPushButton()
        align_horiz_button.setIcon(Krita.instance().icon('distribute-horizontal'))
        align_horiz_button.setToolTip("Horizontal")
        align_horiz_button.clicked.connect(self.b_align_horiz)
        align_horiz_button.setFixedSize(32, 32)

        align_vert_button = QPushButton()
        align_vert_button.setIcon(Krita.instance().icon('distribute-vertical'))
        align_vert_button.setToolTip("Vertical")
        align_vert_button.clicked.connect(self.b_align_vert)
        align_vert_button.setFixedSize(32, 32)

        main_layout.addWidget(align_horiz_button)
        main_layout.addWidget(align_vert_button)
        
        # Separator
        separator = QLabel(" | ")
        main_layout.addWidget(separator)
        
        # Create 3x3 grid for alignment positions
        grid_layout = QGridLayout()
        grid_layout.setSpacing(2)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        
        # Icon names for each position
        # Using arrow icons to indicate direction
        icon_map = {
            (0, 0): 'arrow-topleft',      # Top-Left
            (0, 1): 'arrow-up',           # Top
            (0, 2): 'arrow-topright',     # Top-Right
            (1, 0): 'arrow-left',         # Left
            (1, 1): 'select-all',         # Centre
            (1, 2): 'arrow-right',        # Right
            (2, 0): 'arrow-downleft',     # Bottom-Left
            (2, 1): 'arrow-down',         # Bottom
            (2, 2): 'arrow-downright',    # Bottom-Right
        }
        
        tooltip_map = {
            (0, 0): 'Top-Left',
            (0, 1): 'Top',
            (0, 2): 'Top-Right',
            (1, 0): 'Left',
            (1, 1): 'Centre',
            (1, 2): 'Right',
            (2, 0): 'Bottom-Left',
            (2, 1): 'Bottom',
            (2, 2): 'Bottom-Right',
        }
        
        # Create buttons for 3x3 grid
        for row in range(3):
            for col in range(3):
                btn = QPushButton()
                btn.setFixedSize(24, 24)
                
                # Try to set icon, fallback to text if icon not available
                icon_name = icon_map.get((row, col), 'select-all')
                icon = Krita.instance().icon(icon_name)
                if not icon.isNull():
                    btn.setIcon(icon)
                else:
                    # Fallback: use simple text indicators
                    fallback_text = {
                        (0, 0): '↖', (0, 1): '↑', (0, 2): '↗',
                        (1, 0): '←', (1, 1): '●', (1, 2): '→',
                        (2, 0): '↙', (2, 1): '↓', (2, 2): '↘',
                    }
                    btn.setText(fallback_text.get((row, col), ''))
                
                btn.setToolTip(tooltip_map.get((row, col), ''))
                btn.clicked.connect(lambda checked, r=row, c=col: self.b_align_grid(r, c))
                grid_layout.addWidget(btn, row, col)
        
        # Add grid to main layout
        grid_widget = QWidget()
        grid_widget.setLayout(grid_layout)
        main_layout.addWidget(grid_widget)
        
        # Another separator
        separator2 = QLabel(" | ")
        main_layout.addWidget(separator2)
        
        # Offset controls - create a vertical layout with label, X/Y inputs, and Apply button
        offset_outer_container = QVBoxLayout()
        offset_outer_container.setSpacing(2)
        offset_outer_container.setContentsMargins(0, 0, 0, 0)
        
        # Offset label
        offset_label = QLabel("Offset:")
        offset_label.setStyleSheet("font-weight: bold;")
        offset_label.setAlignment(Qt.AlignCenter)
        offset_outer_container.addWidget(offset_label)
        
        # Container for X and Y controls
        offset_container = QHBoxLayout()
        offset_container.setSpacing(4)
        
        # X offset
        offset_x_label = QLabel("X:")
        self.offset_x_spinbox = QSpinBox()
        self.offset_x_spinbox.setRange(-10000, 10000)
        self.offset_x_spinbox.setValue(0)
        self.offset_x_spinbox.setToolTip("Horizontal offset in pixels")
        self.offset_x_spinbox.setFixedWidth(60)
        offset_container.addWidget(offset_x_label)
        offset_container.addWidget(self.offset_x_spinbox)
        
        # Y offset
        offset_y_label = QLabel("Y:")
        self.offset_y_spinbox = QSpinBox()
        self.offset_y_spinbox.setRange(-10000, 10000)
        self.offset_y_spinbox.setValue(0)
        self.offset_y_spinbox.setToolTip("Vertical offset in pixels")
        self.offset_y_spinbox.setFixedWidth(60)
        offset_container.addWidget(offset_y_label)
        offset_container.addWidget(self.offset_y_spinbox)
        
        offset_outer_container.addLayout(offset_container)
        
        # Apply offset button
        apply_offset_button = QPushButton("Offset Without Align")
        apply_offset_button.setToolTip("Apply offset directly to layer position")
        apply_offset_button.clicked.connect(self.apply_offset_directly)
        
        offset_outer_container.addWidget(apply_offset_button)
        
        main_layout.addLayout(offset_outer_container)
        
        # Set up the docker widget
        widget = QWidget()
        widget.setLayout(main_layout)
        
        # Set size policy to prevent vertical stretching
        widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.setWidget(widget)

    def get_offset(self):
        """Get current offset values from spinboxes."""
        return [self.offset_x_spinbox.value(), self.offset_y_spinbox.value()]

    def apply_offset_directly(self):
        """Apply the offset values directly to the layer position without any alignment."""
        active_doc = Krita.instance().activeDocument()
        if active_doc is None:
            QMessageBox.information(QWidget(), "Apply Offset", "There is no active Krita document!")
            return

        active_layer = active_doc.activeNode()
        if active_layer is None:
            QMessageBox.information(QWidget(), "Apply Offset", "There is no active layer in Krita document!")
            return
        
        # Get the offset values
        offset = self.get_offset()
        
        # Check if it's a group layer - if so, apply to all direct children
        if active_layer.type() == "grouplayer":
            children = active_layer.childNodes()
            if not children:
                QMessageBox.information(QWidget(), "Apply Offset", "The selected group layer is empty!")
                return
            
            # Apply offset to each child layer
            for child in children:
                self.apply_offset_to_layer(child, offset)
        else:
            # Apply offset to single layer
            self.apply_offset_to_layer(active_layer, offset)
        
        # Refresh the display
        active_doc.refreshProjection()
    
    def apply_offset_to_layer(self, layer, offset):
        """Apply offset to a single layer."""
        # Store original position
        pos_before_move = layer.position()
        
        # Move the layer by the offset amount
        layer.move(pos_before_move.x() + offset[0], pos_before_move.y() + offset[1])
        
        # Calculate the position offset for children
        pos_offset = layer.position() - pos_before_move
        
        # Move all children by the same offset
        move_children(layer, pos_offset)

    def process_align(self, align_type, grid_position=None):
        active_doc = Krita.instance().activeDocument()
        if active_doc is None:
            QMessageBox.information(QWidget(), "Align to Canvas", "There is no active Krita document!")
            return

        active_layer = active_doc.activeNode()
        if active_layer is None:
            QMessageBox.information(QWidget(), "Align to Canvas", "There is no active layer in Krita document!")
            return
        
        # Check if it's a group layer - if so, apply to all direct children
        if active_layer.type() == "grouplayer":
            children = active_layer.childNodes()
            if not children:
                QMessageBox.information(QWidget(), "Align to Canvas", "The selected group layer is empty!")
                return
            
            # Process each child layer
            for child in children:
                self.align_single_layer(child, align_type, active_doc, grid_position)
        else:
            # Process single layer
            self.align_single_layer(active_layer, align_type, active_doc, grid_position)
        
        # Refresh the display
        active_doc.refreshProjection()

    def align_single_layer(self, layer, align_type, active_doc, grid_position=None):
        """Align a single layer."""
        # Get target position and pivot point based on alignment type
        target_pos, pivot = apply_align_type(align_type, layer, active_doc, grid_position)
        
        # Apply offset to target position
        # For horiz/vert, only apply offset in the direction being aligned
        offset = self.get_offset()
        if align_type == EdgeAlignType.horiz:
            # Only apply X offset for horizontal alignment
            target_pos[0] += offset[0]
        elif align_type == EdgeAlignType.vert:
            # Only apply Y offset for vertical alignment
            target_pos[1] += offset[1]
        else:
            # Apply both offsets for centre and grid alignments
            target_pos[0] += offset[0]
            target_pos[1] += offset[1]
        
        # Calculate move coordinates using the appropriate pivot point
        move_coords = get_move_coordinates(layer, target_pos, pivot)
        
        # Store original position
        pos_before_move = layer.position()
        
        # Move the layer
        layer.move(move_coords[0] + pos_before_move.x(), move_coords[1] + pos_before_move.y())
        
        # Calculate the position offset for children
        pos_offset = layer.position() - pos_before_move
        
        # Move all children by the same offset
        move_children(layer, pos_offset)

    def b_align_centre(self):
        self.process_align(EdgeAlignType.centre)

    def b_align_horiz(self):
        self.process_align(EdgeAlignType.horiz)

    def b_align_vert(self):
        self.process_align(EdgeAlignType.vert)

    def b_align_grid(self, row, col):
        self.process_align(EdgeAlignType.grid, (row, col))

    def canvasChanged(self, canvas):
        pass


Krita.instance().addDockWidgetFactory(DockWidgetFactory("DuskcuS Align", DockWidgetFactoryBase.DockRight, AlignToSelectionDocker))