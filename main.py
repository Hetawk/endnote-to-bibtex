import sys
import os
import traceback
import datetime
import re  # Added for regex pattern matching
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QLineEdit, QTextEdit, QTabWidget, 
                             QProgressBar, QFileDialog, QMessageBox, QComboBox, QGroupBox,
                             QRadioButton, QButtonGroup, QCheckBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import xml.etree.ElementTree as ET
from xml_converter import XML


class Logger:
    """Centralized logging system for the application."""
    
    def __init__(self, log_file="conversion_log.txt"):
        self.log_file = log_file
        
    def log(self, message, level="INFO"):
        """Log a message with timestamp and level."""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}\n"
        
        try:
            with open(self.log_file, "a", encoding='utf-8') as log_file:
                log_file.write(log_entry)
            return True
        except Exception as e:
            print(f"Error writing to log file: {str(e)}")
            return False
    
    def info(self, message):
        """Log an informational message."""
        return self.log(message, "INFO")
    
    def warning(self, message):
        """Log a warning message."""
        return self.log(message, "WARNING")
    
    def error(self, message):
        """Log an error message."""
        return self.log(message, "ERROR")
    
    def success(self, message):
        """Log a success message."""
        return self.log(message, "SUCCESS")


class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Reference Converter")
        self.setGeometry(100, 100, 800, 600)  # Increased size for more UI elements
        self.setStyleSheet("background-color: #2a1a1f;")

        self.xml_converter = XML()
        self.converted_text = None
        self.logger = Logger()  # Initialize the logger
        
        self.logger.info("Application started")

        self.init_ui()

    def init_ui(self):
        # Main container widget
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #333;
                background-color: #2a1a1f;
            }
            QTabBar::tab {
                background-color: #764134;
                color: white;
                padding: 6px 12px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #8B5A4C;
            }
        """)
        main_layout.addWidget(self.tab_widget)
        
        # Create conversion tab
        self.create_conversion_tab()
        
        # Create log tab
        self.create_log_tab()
        
        # Create settings tab
        self.create_settings_tab()

    def create_conversion_tab(self):
        # Conversion tab widget
        conversion_tab = QWidget()
        conversion_tab.setStyleSheet("background-color: #2a1a1f;")
        conversion_layout = QVBoxLayout(conversion_tab)
        
        # Header label
        header_label = QLabel("Convert References to BibTeX")
        header_label.setFont(QFont("Arial", 16, QFont.Bold))
        header_label.setStyleSheet("color: white;")
        header_label.setAlignment(Qt.AlignCenter)
        conversion_layout.addWidget(header_label)
        
        # File selection frame
        file_frame = QWidget()
        file_layout = QHBoxLayout(file_frame)
        
        file_label = QLabel("Select File:")
        file_label.setFont(QFont("Arial", 12))
        file_label.setStyleSheet("color: white;")
        file_layout.addWidget(file_label)
        
        self.file_entry = QLineEdit()
        self.file_entry.setStyleSheet("background-color: #afa060; color: black; padding: 5px;")
        file_layout.addWidget(self.file_entry)
        
        browse_button = QPushButton("Browse")
        browse_button.setStyleSheet("background-color: #764134; color: black;")
        browse_button.clicked.connect(self.browse_file)
        file_layout.addWidget(browse_button)
        
        conversion_layout.addWidget(file_frame)
        
        # Conversion Type Selection
        type_group = QGroupBox("Conversion Type")
        type_group.setStyleSheet("""
            QGroupBox {
                color: white; 
                border: 1px solid #764134;
                margin-top: 20px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        type_layout = QVBoxLayout(type_group)
        type_layout.setContentsMargins(15, 25, 15, 10)  # Add more top margin for the title
        type_layout.setSpacing(10)  # Add spacing between radio buttons
        
        # Remove button group and auto-detect option since we only have one format
        self.xml_radio = QRadioButton("EndNote XML to BibTeX")
        self.xml_radio.setStyleSheet("color: white;")
        self.xml_radio.setChecked(True)  # Always checked since it's the only option
        type_layout.addWidget(self.xml_radio)
        
        conversion_layout.addWidget(type_group)
        
        # Warning suppression
        warning_frame = QWidget()
        warning_layout = QHBoxLayout(warning_frame)
        warning_layout.setContentsMargins(5, 10, 5, 10)  # Add some margin
        
        self.suppress_warnings = QCheckBox("Suppress missing field warnings")
        self.suppress_warnings.setStyleSheet("color: white;")
        self.suppress_warnings.setChecked(True)  # Default to suppress warnings
        warning_layout.addWidget(self.suppress_warnings)
        
        conversion_layout.addWidget(warning_frame)
        
        # Convert button
        convert_button = QPushButton("Convert Now")
        convert_button.setStyleSheet("background-color: #764134; color: black; padding: 8px; font-weight: bold;")
        convert_button.clicked.connect(self.convert_file)
        conversion_layout.addWidget(convert_button)
        
        # Progress section
        progress_frame = QWidget()
        progress_layout = QVBoxLayout(progress_frame)
        
        self.progress_label = QLabel("")
        self.progress_label.setStyleSheet("color: white;")
        self.progress_label.setAlignment(Qt.AlignCenter)
        progress_layout.addWidget(self.progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid grey;
                border-radius: 5px;
                text-align: center;
                background-color: #333;
                color: white;
            }
            QProgressBar::chunk {
                background-color: #764134;
                width: 10px;
                margin: 0.5px;
            }
        """)
        progress_layout.addWidget(self.progress_bar)
        
        conversion_layout.addWidget(progress_frame)
        
        # Save section
        save_frame = QWidget()
        save_layout = QVBoxLayout(save_frame)
        
        save_buttons_layout = QHBoxLayout()
        
        self.save_button = QPushButton("Save As...")
        self.save_button.setStyleSheet("background-color: #764134; color: black; padding: 8px; font-weight: bold;")
        self.save_button.clicked.connect(self.save_file)
        self.save_button.hide()  # Initially hidden
        save_buttons_layout.addWidget(self.save_button)
        
        self.quick_save_button = QPushButton("Save to Directory")
        self.quick_save_button.setStyleSheet("background-color: #764134; color: black; padding: 8px;")
        self.quick_save_button.setToolTip("Save as 'converted.bib' in a selected directory")
        self.quick_save_button.clicked.connect(self.quick_save_file)
        self.quick_save_button.hide()  # Initially hidden
        save_buttons_layout.addWidget(self.quick_save_button)
        
        save_layout.addLayout(save_buttons_layout)
        
        # Completion message
        self.complete_label = QLabel("")
        self.complete_label.setFont(QFont("Arial", 12, QFont.StyleItalic))
        self.complete_label.setStyleSheet("color: white;")
        self.complete_label.setAlignment(Qt.AlignCenter)
        save_layout.addWidget(self.complete_label)
        
        conversion_layout.addWidget(save_frame)
        
        # Add tab to tab widget
        self.tab_widget.addTab(conversion_tab, "Conversion")

    def create_log_tab(self):
        # Log tab widget
        log_tab = QWidget()
        log_tab.setStyleSheet("background-color: #2a1a1f;")
        log_layout = QVBoxLayout(log_tab)
        
        # Log text edit
        self.log_text = QTextEdit()
        self.log_text.setStyleSheet("background-color: #333; color: white;")
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        
        # Log view button
        log_button = QPushButton("View Log")
        log_button.setStyleSheet("background-color: #764134; color: black; padding: 8px;")
        log_button.clicked.connect(self.view_log)
        log_layout.addWidget(log_button)
        
        # Add tab to tab widget
        self.tab_widget.addTab(log_tab, "Log")

    def create_settings_tab(self):
        # Settings tab widget
        settings_tab = QWidget()
        settings_tab.setStyleSheet("background-color: #2a1a1f;")
        settings_layout = QVBoxLayout(settings_tab)
        
        # Header
        settings_header = QLabel("Settings")
        settings_header.setFont(QFont("Arial", 16, QFont.Bold))
        settings_header.setStyleSheet("color: white;")
        settings_header.setAlignment(Qt.AlignCenter)
        settings_layout.addWidget(settings_header)
        
        # Default save directory
        save_dir_frame = QWidget()
        save_dir_layout = QHBoxLayout(save_dir_frame)
        
        save_dir_label = QLabel("Default Save Directory:")
        save_dir_label.setStyleSheet("color: white;")
        save_dir_layout.addWidget(save_dir_label)
        
        self.save_dir_entry = QLineEdit()
        self.save_dir_entry.setStyleSheet("background-color: #afa060; color: black;")
        save_dir_layout.addWidget(self.save_dir_entry)
        
        save_dir_browse = QPushButton("Browse")
        save_dir_browse.setStyleSheet("background-color: #764134; color: black;")
        save_dir_browse.clicked.connect(self.browse_save_dir)
        save_dir_layout.addWidget(save_dir_browse)
        
        settings_layout.addWidget(save_dir_frame)
        
        # EndNote specific settings
        endnote_group = QGroupBox("EndNote XML Settings")
        endnote_group.setStyleSheet("""
            QGroupBox {
                color: white; 
                border: 1px solid #764134;
                margin-top: 20px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        endnote_layout = QVBoxLayout(endnote_group)
        endnote_layout.setContentsMargins(15, 25, 15, 10)  # Add more top margin for the title
        endnote_layout.setSpacing(10)  # Add spacing between checkboxes
        
        self.styled_text = QCheckBox("Extract styled text (for EndNote XML)")
        self.styled_text.setStyleSheet("color: white;")
        self.styled_text.setChecked(True)
        endnote_layout.addWidget(self.styled_text)
        
        settings_layout.addWidget(endnote_group)
        
        # General UI spacing
        settings_layout.setSpacing(15)  # Add general spacing between elements
        settings_layout.setContentsMargins(20, 20, 20, 20)  # Add margins around all elements
        
        # Save settings button
        save_settings = QPushButton("Save Settings")
        save_settings.setStyleSheet("background-color: #764134; color: black; padding: 8px;")
        save_settings.clicked.connect(self.save_settings)
        settings_layout.addWidget(save_settings)
        
        settings_layout.addStretch()
        
        # Add tab to tab widget
        self.tab_widget.addTab(settings_tab, "Settings")

    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Select EndNote XML File", 
            "", 
            "XML Files (*.xml);;All Files (*.*)"
        )
        if file_path:
            self.file_entry.setText(file_path)
            self.logger.info(f"Selected file: {file_path}")
            # No need to auto-select radio button since there's only one option

    def browse_save_dir(self):
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Select Default Save Directory",
            os.path.expanduser("~")  # Start in user's home directory
        )
        if dir_path:
            self.save_dir_entry.setText(dir_path)

    def save_settings(self):
        QMessageBox.information(self, "Settings Saved", "Your settings have been saved.")

    def convert_file(self):
        file_path = self.file_entry.text()
        if not file_path:
            QMessageBox.warning(self, "Warning", "Please select a file first")
            self.logger.warning("Conversion attempted without selecting a file")
            return
            
        if not os.path.exists(file_path):
            error_msg = f"File not found: {file_path}"
            self.log_error(error_msg)
            return
            
        # Check if the file is a log file by name (to prevent users from loading the log file)
        if os.path.basename(file_path).lower() == "conversion_log.txt":
            error_msg = "The selected file appears to be a log file, not a reference file."
            QMessageBox.warning(self, "Invalid File", error_msg)
            self.logger.warning(error_msg)
            return
            
        # Reset UI elements
        self.progress_label.setText("")
        self.complete_label.setText("")
        self.log_text.clear()
        self.progress_bar.setValue(0)
        self.save_button.hide()
        self.quick_save_button.hide()
        self.converted_text = None
        
        # Log the conversion attempt
        self.logger.info(f"Starting conversion of file: {file_path}")
        
        # Update UI to show processing
        self.progress_label.setText("Converting...")
        QApplication.processEvents()  # Force UI update
        
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as file:
                file_data = file.read()
            
            # Improved log file detection - timestamp pattern and multiple log keywords
            log_file_pattern = r'\[\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}\]'
            if re.search(log_file_pattern, file_data) and ("INFO:" in file_data or "ERROR:" in file_data or "WARNING:" in file_data):
                error_msg = "The selected file appears to be a log file, not a reference file."
                QMessageBox.warning(self, "Invalid File", error_msg)
                self.logger.warning(error_msg)
                return
            
            # Set suppress warnings flag
            self.xml_converter.suppress_warnings = self.suppress_warnings.isChecked()
            
            # Set styled text extraction for EndNote XML
            self.xml_converter.extract_styled_text = self.styled_text.isChecked()
            
            # Simplified conversion logic - always use XML converter
            self.log_text.append("Processing EndNote XML file...")
            self.logger.info("Converting EndNote XML to BibTeX")
            conversion_method = "EndNote XML to BibTeX"
            bib_entry = self.xml_converter.convert_to_bibtex(file_data)
            
            # Check if conversion was successful
            if not bib_entry:
                error_msg = "Conversion failed: No BibTeX entries generated"
                self.log_error(error_msg)
                return
                
            # Update UI with success
            self.progress_bar.setValue(100)
            self.progress_label.setText("Conversion Complete")
            self.complete_label.setText("Conversion completed successfully!")
            self.complete_label.setStyleSheet("color: white;")
            self.converted_text = bib_entry  # Store BibTeX entry for saving
            self.save_button.show()  # Show save button
            self.quick_save_button.show()  # Show quick save button
            
            # Create preview of the converted text
            preview = bib_entry[:500] + "..." if len(bib_entry) > 500 else bib_entry
            self.log_text.append("\nPreview of converted BibTeX:\n")
            self.log_text.append(preview)
            
            # Log success
            entry_count = bib_entry.count('@')
            self.log_text.append(f"\nGenerated {entry_count} BibTeX entries")
            self.log_text.append("Conversion completed successfully!")
            
            # Log detailed success information
            success_msg = (
                f"Conversion completed successfully. "
                f"File: {os.path.basename(file_path)}, "
                f"Method: {conversion_method}, "
                f"Entries: {entry_count}"
            )
            self.logger.success(success_msg)
                
        except Exception as e:
            # Handle any exception
            error_message = f"Error during conversion: {str(e)}"
            self.log_error(error_message)
            self.log_text.append(traceback.format_exc())
            self.progress_label.setText("Conversion Failed")
            self.complete_label.setText("An error occurred during conversion.")
            self.complete_label.setStyleSheet("color: red;")
            
            # Log detailed error information
            self.logger.error(f"Exception during conversion of {file_path}: {str(e)}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")

    def save_file(self):
        if not self.converted_text:
            QMessageBox.warning(self, "Warning", "No converted data to save")
            self.logger.warning("Save attempted with no converted data")
            return
                    
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save BibTeX File",
            os.path.join(os.path.expanduser("~"), "converted.bib"),
            "BibTeX Files (*.bib);;Text Files (*.txt);;All Files (*.*)"
        )
        
        if file_path:
            self.logger.info(f"Saving file as: {file_path}")
            self._save_to_path(file_path)

    def quick_save_file(self):
        if not self.converted_text:
            QMessageBox.warning(self, "Warning", "No converted data to save")
            self.logger.warning("Quick save attempted with no converted data")
            return
            
        # Ask user to select a directory
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Select Directory to Save",
            os.path.expanduser("~")  # Start in user's home directory
        )
        
        if not dir_path:
            self.logger.info("Directory selection canceled by user")
            return  # User canceled directory selection
                
        # Create the file path
        file_path = os.path.join(dir_path, "converted.bib")
        self.logger.info(f"Quick saving to: {file_path}")
        
        # Check if file already exists
        if os.path.exists(file_path):
            self.logger.warning(f"File already exists: {file_path}")
            reply = QMessageBox.question(
                self, 
                "File Exists", 
                f"A file named 'converted.bib' already exists in this directory.\nDo you want to replace it?",
                QMessageBox.Yes | QMessageBox.No, 
                QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                self.logger.info("User chose not to overwrite existing file")
                return
            else:
                self.logger.info("User chose to overwrite existing file")
        
        # Save the file
        self._save_to_path(file_path)

    def _save_to_path(self, file_path):
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(self.converted_text)
            
            self.complete_label.setText(f"File saved as {os.path.basename(file_path)}")
            self.complete_label.setStyleSheet("color: white;")
            self.log_text.append(f"File saved as: {file_path}")
            
            # Log success
            self.logger.success(f"File successfully saved to: {file_path}")
            
            # Ask if user wants to open the file
            reply = QMessageBox.question(
                self, 
                "File Saved", 
                f"File saved as {file_path}\n\nWould you like to open the directory?",
                QMessageBox.Yes | QMessageBox.No, 
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # Open the directory containing the file
                directory = os.path.dirname(file_path)
                if sys.platform == 'win32':
                    os.startfile(directory)
                elif sys.platform == 'darwin':  # macOS
                    os.system(f"open {directory}")
                else:  # Linux
                    os.system(f"xdg-open {directory}")
                
                self.logger.info(f"Opened directory: {directory}")
                
        except Exception as e:
            error_message = f"Error saving file: {str(e)}"
            self.log_error(error_message)
            QMessageBox.critical(self, "Save Error", error_message)

    def log_error(self, error_message):
        self.log_text.append(f"Error: {error_message}")
        self.logger.error(error_message)
        self.tab_widget.setCurrentIndex(1)  # Switch to log tab to show the error

    def view_log(self):
        self.log_text.clear()
        try:
            with open("conversion_log.txt", "r", encoding='utf-8') as log_file:
                log_content = log_file.read()
            self.log_text.setText(log_content)
            self.logger.info("User viewed log file")
        except FileNotFoundError:
            self.log_text.setText("Log file not found.")
            self.logger.warning("Log file not found when attempting to view")
        except Exception as e:
            self.log_text.setText(f"Error reading log file: {str(e)}")
            self.logger.error(f"Error reading log file: {str(e)}")


def main():
    app = QApplication(sys.argv)
    window = MainApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()