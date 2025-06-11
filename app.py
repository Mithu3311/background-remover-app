import sys
import os
import requests
import io
from PIL import Image
from PyQt5.QtGui import QImage
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QPushButton, 
                             QVBoxLayout, QHBoxLayout, QWidget, QFileDialog, 
                             QMessageBox, QProgressBar, QFrame, QSizePolicy)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize, QMimeData, QUrl
from PyQt5.QtGui import QPixmap, QDrag, QFont, QPalette, QColor, QIcon, QCursor

# API key for remove.bg
API_KEY = "hAkcLnBa8jfuKZEmCzKPAVf5"

class ImageProcessor(QThread):
    finished = pyqtSignal(bytes)
    error = pyqtSignal(str)
    progress = pyqtSignal(int)
    
    def __init__(self, image_path):
        super().__init__()
        self.image_path = image_path
        
    def run(self):
        try:
            self.progress.emit(10)
            
            # Prepare the API request
            url = "https://api.remove.bg/v1.0/removebg"
            headers = {"X-Api-Key": API_KEY}
            
            self.progress.emit(30)
            
            with open(self.image_path, "rb") as image_file:
                files = {"image_file": image_file}
                self.progress.emit(50)
                
                # Make the API request
                response = requests.post(url, headers=headers, files=files)
                self.progress.emit(80)
                
                if response.status_code == 200:
                    self.progress.emit(100)
                    self.finished.emit(response.content)
                else:
                    error_message = f"Error: {response.status_code} - {response.text}"
                    self.error.emit(error_message)
        except Exception as e:
            self.error.emit(str(e))

class DropLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setText("Drag & Drop Image Here\nor Click to Browse")
        self.setAcceptDrops(True)
        self.setStyleSheet("""
            QLabel {
                border: 2px dashed #aaa;
                border-radius: 10px;
                padding: 20px;
                background-color: #f8f8f8;
                color: #555;
                font-size: 16px;
            }
        """)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumHeight(300)
        
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()
            
    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.CopyAction)
            event.accept()
        else:
            event.ignore()
            
    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.CopyAction)
            event.accept()
            
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
                    self.parent().parent().load_image(file_path)
                    break
        else:
            event.ignore()
            
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.parent().parent().browse_image()

class ImageFrame(QFrame):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 10px;
                border: 1px solid #ddd;
            }
        """)
        
        layout = QVBoxLayout(self)
        
        # Title label
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #333;
                padding: 5px;
                background-color: #f0f0f0;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
                border-bottom: 1px solid #ddd;
            }
        """)
        
        # Image label
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("padding: 10px;")
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        layout.addWidget(title_label)
        layout.addWidget(self.image_label)
        
    def set_image(self, pixmap):
        if pixmap:
            # Scale the pixmap to fit the label while maintaining aspect ratio
            scaled_pixmap = pixmap.scaled(self.image_label.size(), 
                                          Qt.KeepAspectRatio, 
                                          Qt.SmoothTransformation)
            self.image_label.setPixmap(scaled_pixmap)
        else:
            self.image_label.clear()
            
    def clear(self):
        self.image_label.clear()

class BackgroundRemoverApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.current_image_path = None
        self.processed_image_data = None
        
    def init_ui(self):
        self.setWindowTitle("Background Remover")
        self.setMinimumSize(900, 600)
        
        # Set application style
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QPushButton {
                background-color: #4a86e8;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3a76d8;
            }
            QPushButton:pressed {
                background-color: #2a66c8;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #888888;
            }
            QProgressBar {
                border: 1px solid #ddd;
                border-radius: 5px;
                text-align: center;
                background-color: #f0f0f0;
            }
            QProgressBar::chunk {
                background-color: #4a86e8;
                border-radius: 5px;
            }
        """)
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # App title
        title_label = QLabel("Background Remover")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #333;
                margin-bottom: 10px;
            }
        """)
        
        # Drop area for image upload
        self.drop_label = DropLabel()
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        self.progress_bar.setFixedHeight(15)
        
        # Image display area
        images_layout = QHBoxLayout()
        
        # Original image frame
        self.original_frame = ImageFrame("Original Image")
        
        # Processed image frame
        self.processed_frame = ImageFrame("Processed Image")
        
        images_layout.addWidget(self.original_frame)
        images_layout.addWidget(self.processed_frame)
        
        # Buttons layout
        buttons_layout = QHBoxLayout()
        
        # Browse button
        self.browse_button = QPushButton("Browse Image")
        self.browse_button.clicked.connect(self.browse_image)
        
        # Process button
        self.process_button = QPushButton("Remove Background")
        self.process_button.clicked.connect(self.process_image)
        self.process_button.setEnabled(False)
        
        # Save button
        self.save_button = QPushButton("Save Result")
        self.save_button.clicked.connect(self.save_image)
        self.save_button.setEnabled(False)
        
        buttons_layout.addWidget(self.browse_button)
        buttons_layout.addWidget(self.process_button)
        buttons_layout.addWidget(self.save_button)
        
        # Add all layouts to main layout
        main_layout.addWidget(title_label)
        main_layout.addWidget(self.drop_label)
        main_layout.addWidget(self.progress_bar)
        main_layout.addLayout(images_layout)
        main_layout.addLayout(buttons_layout)
        
    def browse_image(self):
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(
            self, "Select Image", "", "Image Files (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        
        if file_path:
            self.load_image(file_path)
            
    def load_image(self, file_path):
        try:
            self.current_image_path = file_path
            pixmap = QPixmap(file_path)
            
            if pixmap.isNull():
                QMessageBox.critical(self, "Error", "Failed to load image!")
                return
                
            self.original_frame.set_image(pixmap)
            self.processed_frame.clear()
            self.process_button.setEnabled(True)
            self.save_button.setEnabled(False)
            self.processed_image_data = None
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error loading image: {str(e)}")
            
    def process_image(self):
        if not self.current_image_path:
            return
            
        # Show progress bar
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        
        # Disable buttons during processing
        self.browse_button.setEnabled(False)
        self.process_button.setEnabled(False)
        
        # Create and start the image processor thread
        self.processor = ImageProcessor(self.current_image_path)
        self.processor.finished.connect(self.on_processing_finished)
        self.processor.error.connect(self.on_processing_error)
        self.processor.progress.connect(self.progress_bar.setValue)
        self.processor.start()
        
    def on_processing_finished(self, image_data):
        try:
            # Store the processed image data
            self.processed_image_data = image_data
            
            # Convert bytes to QPixmap
            image = Image.open(io.BytesIO(image_data))
            # Save to a temporary buffer and load with QPixmap
            temp_buffer = io.BytesIO()
            image.save(temp_buffer, format="PNG")
            pixmap = QPixmap()
            pixmap.loadFromData(temp_buffer.getvalue())
            
            # Display the processed image
            self.processed_frame.set_image(pixmap)
            
            # Enable buttons
            self.browse_button.setEnabled(True)
            self.process_button.setEnabled(True)
            self.save_button.setEnabled(True)
            
            # Hide progress bar
            self.progress_bar.setVisible(False)
            
        except Exception as e:
            self.on_processing_error(f"Error displaying processed image: {str(e)}")
            
    def on_processing_error(self, error_message):
        # Hide progress bar
        self.progress_bar.setVisible(False)
        
        # Enable buttons
        self.browse_button.setEnabled(True)
        self.process_button.setEnabled(True)
        
        # Show error message
        QMessageBox.critical(self, "Error", error_message)
        
    def save_image(self):
        if not self.processed_image_data:
            return
            
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getSaveFileName(
            self, "Save Image", "", "PNG Image (*.png)"
        )
        
        if file_path:
            try:
                # Ensure the file has .png extension
                if not file_path.lower().endswith('.png'):
                    file_path += '.png'
                    
                # Save the image
                with open(file_path, 'wb') as f:
                    f.write(self.processed_image_data)
                    
                QMessageBox.information(self, "Success", "Image saved successfully!")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error saving image: {str(e)}")
                
    def resizeEvent(self, event):
        # Update image display when window is resized
        if hasattr(self, 'original_frame') and hasattr(self, 'processed_frame'):
            if self.original_frame.image_label.pixmap():
                original_pixmap = QPixmap(self.current_image_path)
                self.original_frame.set_image(original_pixmap)
                
            if self.processed_image_data and self.processed_frame.image_label:
                try:
                    image = Image.open(io.BytesIO(self.processed_image_data))
                    # Save to a temporary buffer and load with QPixmap
                    temp_buffer = io.BytesIO()
                    image.save(temp_buffer, format="PNG")
                    pixmap = QPixmap()
                    pixmap.loadFromData(temp_buffer.getvalue())
                    self.processed_frame.set_image(pixmap)
                except:
                    pass
        
        super().resizeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BackgroundRemoverApp()
    window.show()
    sys.exit(app.exec_())