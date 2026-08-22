"""
Constellation Grid UI Component for Photo Organizer
Modern, animated interface inspired by shadcn/ui constellation-grid component
"""

import sys
import math
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QCheckBox, QSpinBox, QLineEdit,
    QFileDialog, QScrollArea, QFrame, QGridLayout
)
from PySide6.QtCore import Qt, QTimer, QPoint, QSize, QRect, pyqtSignal
from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont, QPixmap, QIcon,
    QLinearGradient, QPainterPath
)
from PySide6.QtOpenGLWidgets import QOpenGLWidget
import numpy as np


class Node:
    """Represents a point in the constellation grid"""
    def __init__(self, x, y, label=""):
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0
        self.baseX = x
        self.baseY = y
        self.radius = np.random.uniform(1.2, 2.4)
        self.label = label
        self.pulse = np.random.uniform(0, 2 * math.pi)


class ConstellationCanvas(QOpenGLWidget):
    """High-performance canvas for rendering constellation grid"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.nodes = []
        self.mouse_x = -1000
        self.mouse_y = -1000
        self.mouse_prev_x = -1000
        self.mouse_prev_y = -1000
        self.mouse_vx = 0
        self.mouse_vy = 0
        self.mouse_radius = 220
        self.is_dark_mode = True
        
        self.width = 0
        self.height = 0
        self.last_time = 0
        
        # Physics parameters
        self.SPRING_K = 18
        self.DAMPING = 0.82
        self.MAX_CONN_DIST = 75
        
        # Animation timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(16)  # ~60 FPS
        
        self.setMouseTracking(True)
        self.setCursor(Qt.CrossCursor)
        self.setFocusPolicy(Qt.StrongFocus)
        
    def paintEvent(self, event):
        """Render the constellation grid"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        
        # Background
        bg_color = QColor("#030407") if self.is_dark_mode else QColor("#f8fafc")
        painter.fillRect(self.rect(), bg_color)
        
        # Colors
        node_color = (255, 255, 255) if self.is_dark_mode else (15, 23, 42)
        accent_color = (56, 189, 248)  # Sky cyan
        
        # Update nodes physics
        dt = 0.016  # ~60 FPS
        self.update_physics(dt)
        
        # Draw connections
        self.draw_connections(painter, node_color)
        
        # Draw nodes
        self.draw_nodes(painter, node_color, accent_color)
        
    def update_physics(self, dt):
        """Update node positions based on physics simulation"""
        if not self.nodes:
            return
            
        # Mouse velocity
        speed = math.sqrt(self.mouse_vx**2 + self.mouse_vy**2)
        
        for node in self.nodes:
            node.pulse += dt * 3
            
            # Mouse distance
            dx = self.mouse_x - node.x
            dy = self.mouse_y - node.y
            dist = math.sqrt(dx*dx + dy*dy)
            
            # Repulsion from cursor
            if dist < self.mouse_radius and dist > 0:
                power = 1 - (dist / self.mouse_radius)
                force = power * (1500 + speed * 150)
                angle = math.atan2(dy, dx)
                
                node.vx -= math.cos(angle) * force * dt
                node.vy -= math.sin(angle) * force * dt
            
            # Spring force to home position
            home_dx = node.baseX - node.x
            home_dy = node.baseY - node.y
            
            node.vx += home_dx * self.SPRING_K * dt
            node.vy += home_dy * self.SPRING_K * dt
            
            # Damping
            node.vx *= self.DAMPING
            node.vy *= self.DAMPING
            
            # Integration
            node.x += node.vx * dt * 60
            node.y += node.vy * dt * 60
    
    def draw_connections(self, painter, node_color):
        """Draw lines between nearby nodes"""
        max_dist_sq = self.MAX_CONN_DIST ** 2
        
        for i in range(len(self.nodes)):
            for j in range(i + 1, len(self.nodes)):
                n1 = self.nodes[i]
                n2 = self.nodes[j]
                
                dx = n1.x - n2.x
                dy = n1.y - n2.y
                dist_sq = dx*dx + dy*dy
                
                if dist_sq < max_dist_sq:
                    dist = math.sqrt(dist_sq)
                    alpha = int((1 - dist / self.MAX_CONN_DIST) * (46 if self.is_dark_mode else 20))
                    
                    pen = QPen(QColor(*node_color, alpha))
                    pen.setWidth(1)
                    painter.setPen(pen)
                    painter.drawLine(int(n1.x), int(n1.y), int(n2.x), int(n2.y))
    
    def draw_nodes(self, painter, node_color, accent_color):
        """Draw node points with effects"""
        for node in self.nodes:
            dx = self.mouse_x - node.x
            dy = self.mouse_y - node.y
            dist = math.sqrt(dx*dx + dy*dy)
            is_near = dist < self.mouse_radius
            
            # Node color and size
            if is_near:
                base_alpha = 242
                color = QColor(*accent_color, base_alpha)
                radius = node.radius * 2.2
            else:
                base_alpha = int(64 + math.sin(node.pulse) * 25)
                color = QColor(*node_color, base_alpha)
                radius = node.radius + math.sin(node.pulse) * 0.3
            
            # Draw node
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(
                int(node.x - radius),
                int(node.y - radius),
                int(radius * 2),
                int(radius * 2)
            )
            
            # Radar rings
            if dist < 90:
                pulse_ring = ((node.pulse * 20) % 30) + 4
                ring_alpha = int((1 - pulse_ring / 34) * 102)
                
                ring_pen = QPen(QColor(*accent_color, ring_alpha))
                ring_pen.setWidth(1)
                painter.setPen(ring_pen)
                painter.setBrush(Qt.NoBrush)
                painter.drawEllipse(
                    int(node.x - pulse_ring),
                    int(node.y - pulse_ring),
                    int(pulse_ring * 2),
                    int(pulse_ring * 2)
                )
    
    def resizeEvent(self, event):
        """Handle window resize"""
        super().resizeEvent(event)
        self.width = event.size().width()
        self.height = event.size().height()
        self.init_nodes()
    
    def init_nodes(self):
        """Initialize constellation grid"""
        self.nodes = []
        spacing = 55
        cols = (self.width // spacing) + 1
        rows = (self.height // spacing) + 1
        
        for i in range(cols):
            for j in range(rows):
                x = i * spacing
                y = j * spacing
                label = f"{(i*7):X}:{(j*11):X}"
                self.nodes.append(Node(x, y, label))
    
    def mouseMoveEvent(self, event):
        """Track mouse position"""
        self.mouse_prev_x = self.mouse_x
        self.mouse_prev_y = self.mouse_y
        self.mouse_x = event.position().x()
        self.mouse_y = event.position().y()
        self.mouse_vx = (self.mouse_x - self.mouse_prev_x) / 16
        self.mouse_vy = (self.mouse_y - self.mouse_prev_y) / 16
    
    def leaveEvent(self, event):
        """Hide cursor effects when leaving window"""
        self.mouse_x = -1000
        self.mouse_y = -1000


class PhotoOrganizerWindow(QMainWindow):
    """Main application window with modern UI"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Organizer Zdjęć - PySide6")
        self.setGeometry(100, 100, 1400, 900)
        self.apply_stylesheet()
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Left sidebar
        left_panel = self.create_left_panel()
        main_layout.addWidget(left_panel, 1)
        
        # Center - constellation canvas
        self.canvas = ConstellationCanvas()
        main_layout.addWidget(self.canvas, 2)
        
        # Right sidebar
        right_panel = self.create_right_panel()
        main_layout.addWidget(right_panel, 1)
    
    def create_left_panel(self):
        """Create left sidebar with catalogs"""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: #0f172a;
                border-right: 1px solid #1e293b;
            }
        """)
        
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("Katalogi Wejściowe")
        title.setStyleSheet("""
            color: #38bdf8;
            font-size: 14px;
            font-weight: bold;
            font-family: 'Courier New';
        """)
        layout.addWidget(title)
        
        # Catalog buttons
        for i, catalog in enumerate(["Folder A", "Folder B", "Folder C"]):
            btn = QPushButton(f"📁 {catalog}")
            btn.setStyleSheet(self.get_button_style())
            layout.addWidget(btn)
        
        layout.addSpacing(20)
        
        # Add catalog button
        add_btn = QPushButton("➕ Dodaj Katalog")
        add_btn.setStyleSheet(self.get_button_style(accent=True))
        add_btn.clicked.connect(self.add_catalog)
        layout.addWidget(add_btn)
        
        layout.addStretch()
        return frame
    
    def create_right_panel(self):
        """Create right sidebar with options"""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: #0f172a;
                border-left: 1px solid #1e293b;
            }
        """)
        
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("Opcje Przetwarzania")
        title.setStyleSheet("""
            color: #38bdf8;
            font-size: 14px;
            font-weight: bold;
            font-family: 'Courier New';
        """)
        layout.addWidget(title)
        
        # Typ
        layout.addWidget(QLabel("Typ:"))
        type_combo = QComboBox()
        type_combo.addItems(["copy", "move", "link"])
        type_combo.setStyleSheet(self.get_combo_style())
        layout.addWidget(type_combo)
        
        # Kolizje
        layout.addWidget(QLabel("Kolizje:"))
        collision_combo = QComboBox()
        collision_combo.addItems(["unique", "overwrite", "skip"])
        collision_combo.setStyleSheet(self.get_combo_style())
        layout.addWidget(collision_combo)
        
        # Checkboxes
        dup_check = QCheckBox("Sprawdzaj Duplikaty")
        dup_check.setStyleSheet(self.get_checkbox_style())
        layout.addWidget(dup_check)
        
        dry_run_check = QCheckBox("Dry-Run")
        dry_run_check.setStyleSheet(self.get_checkbox_style())
        layout.addWidget(dry_run_check)
        
        # Threads
        layout.addWidget(QLabel("Wątki:"))
        threads_spin = QSpinBox()
        threads_spin.setValue(4)
        threads_spin.setMaximum(16)
        threads_spin.setStyleSheet(self.get_spinbox_style())
        layout.addWidget(threads_spin)
        
        layout.addSpacing(20)
        
        # Process button
        process_btn = QPushButton("▶ Rozpocnij Organizację")
        process_btn.setStyleSheet(self.get_button_style(accent=True, large=True))
        process_btn.clicked.connect(self.start_processing)
        layout.addWidget(process_btn)
        
        layout.addStretch()
        return frame
    
    def get_button_style(self, accent=False, large=False):
        """Get button stylesheet"""
        if accent:
            return """
                QPushButton {
                    background-color: #3b82f6;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 12px 16px;
                    font-weight: bold;
                    font-size: 13px;
                    font-family: 'Courier New';
                }
                QPushButton:hover {
                    background-color: #2563eb;
                }
                QPushButton:pressed {
                    background-color: #1d4ed8;
                }
            """
        else:
            return """
                QPushButton {
                    background-color: #1e293b;
                    color: #38bdf8;
                    border: 1px solid #334155;
                    border-radius: 6px;
                    padding: 10px 14px;
                    font-weight: bold;
                    font-size: 12px;
                    font-family: 'Courier New';
                }
                QPushButton:hover {
                    background-color: #334155;
                    border: 1px solid #38bdf8;
                }
                QPushButton:pressed {
                    background-color: #475569;
                }
            """
    
    def get_combo_style(self):
        """Get combobox stylesheet"""
        return """
            QComboBox {
                background-color: #1e293b;
                color: #e2e8f0;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 8px 12px;
                font-family: 'Courier New';
            }
            QComboBox::drop-down {
                border: none;
                background-color: transparent;
            }
            QComboBox QAbstractItemView {
                background-color: #1e293b;
                color: #e2e8f0;
                selection-background-color: #3b82f6;
            }
        """
    
    def get_checkbox_style(self):
        """Get checkbox stylesheet"""
        return """
            QCheckBox {
                color: #e2e8f0;
                font-family: 'Courier New';
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
            QCheckBox::indicator:unchecked {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 4px;
            }
            QCheckBox::indicator:checked {
                background-color: #3b82f6;
                border: 1px solid #3b82f6;
                border-radius: 4px;
            }
        """
    
    def get_spinbox_style(self):
        """Get spinbox stylesheet"""
        return """
            QSpinBox {
                background-color: #1e293b;
                color: #e2e8f0;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 6px 10px;
                font-family: 'Courier New';
            }
            QSpinBox::up-button, QSpinBox::down-button {
                background-color: #334155;
                border: none;
            }
        """
    
    def apply_stylesheet(self):
        """Apply global stylesheet"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #030407;
            }
            QLabel {
                color: #e2e8f0;
                font-family: 'Courier New';
                font-size: 12px;
            }
            QFrame {
                background-color: #030407;
            }
        """)
    
    def add_catalog(self):
        """Handle adding a new catalog"""
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.Directory)
        if dialog.exec():
            print(f"Selected: {dialog.selectedFiles()[0]}")
    
    def start_processing(self):
        """Handle starting photo organization"""
        print("Starting photo organization...")


def main():
    app = QApplication(sys.argv)
    window = PhotoOrganizerWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
