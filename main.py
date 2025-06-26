import sys
import os
import traceback
import datetime
import re  # Added for regex pattern matching
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QLineEdit, QTextEdit, QTabWidget,
                             QProgressBar, QFileDialog, QMessageBox, QComboBox, QGroupBox,
                             QRadioButton, QButtonGroup, QCheckBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
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
        print("DEBUG: Starting MainApp initialization...")
        try:
            super().__init__()
            print("DEBUG: QMainWindow.__init__() completed")

            self.logger = Logger()  # Initialize logger first
            self.logger.info("Starting MainApp initialization")

            self.setWindowTitle("Reference Converter")
            print("DEBUG: Window title set")
            self.logger.info("Window title set")

            # Increased size for more UI elements
            self.setGeometry(100, 100, 800, 600)
            print("DEBUG: Window geometry set")
            self.logger.info("Window geometry set")

            self.setStyleSheet("background-color: #2a1a1f;")
            print("DEBUG: Window style set")
            self.logger.info("Window style set")

            print("DEBUG: Creating XML converter...")
            self.logger.info("Creating XML converter...")
            self.xml_converter = XML()
            print("DEBUG: XML converter created successfully")
            self.logger.info("XML converter created successfully")

            self.converted_text = None
            print("DEBUG: Variables initialized")
            self.logger.info("Variables initialized")

            # Initialize worker threads
            self.conversion_worker = None
            self.progress_monitor = ProgressMonitor()
            self.progress_monitor.log_updated.connect(self.update_log_display)
            print("DEBUG: Worker threads initialized")
            self.logger.info("Worker threads initialized")

            self.logger.info("Application started")
            print("DEBUG: About to call init_ui()")
            self.logger.info("About to call init_ui()")

            self.init_ui()
            print("DEBUG: init_ui() completed successfully")
            self.logger.info("MainApp initialization completed successfully")

        except Exception as e:
            error_msg = f"Error in MainApp.__init__(): {str(e)}"
            print(f"DEBUG ERROR: {error_msg}")
            print(f"DEBUG TRACEBACK: {traceback.format_exc()}")
            if hasattr(self, 'logger'):
                self.logger.error(error_msg)
                self.logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    def init_ui(self):
        try:
            print("DEBUG: Starting init_ui()")
            self.logger.info("Starting UI initialization")

            # Main container widget
            print("DEBUG: Creating central widget")
            self.logger.info("Creating central widget")
            central_widget = QWidget(self)
            self.setCentralWidget(central_widget)

            # Main layout
            print("DEBUG: Creating main layout")
            self.logger.info("Creating main layout")
            main_layout = QVBoxLayout(central_widget)

            # Tab widget
            print("DEBUG: Creating tab widget")
            self.logger.info("Creating tab widget")
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
            print("DEBUG: Tab widget styled")
            self.logger.info("Tab widget styled")

            main_layout.addWidget(self.tab_widget)
            print("DEBUG: Tab widget added to layout")
            self.logger.info("Tab widget added to layout")

            # Create conversion tab
            print("DEBUG: Creating conversion tab")
            self.logger.info("Creating conversion tab")
            self.create_conversion_tab()
            print("DEBUG: Conversion tab created")
            self.logger.info("Conversion tab created")

            # Create log tab
            print("DEBUG: Creating log tab")
            self.logger.info("Creating log tab")
            self.create_log_tab()
            print("DEBUG: Log tab created")
            self.logger.info("Log tab created")

            # Create settings tab
            print("DEBUG: Creating settings tab")
            self.logger.info("Creating settings tab")
            self.create_settings_tab()
            print("DEBUG: Settings tab created")
            self.logger.info("Settings tab created")

        except Exception as e:
            error_msg = f"Error in init_ui(): {str(e)}"
            print(f"DEBUG ERROR: {error_msg}")
            print(f"DEBUG TRACEBACK: {traceback.format_exc()}")
            self.logger.error(error_msg)
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    def create_conversion_tab(self):
        try:
            print("DEBUG: Starting create_conversion_tab()")
            self.logger.info("Starting conversion tab creation")

            # Conversion tab widget
            conversion_tab = QWidget()
            conversion_tab.setStyleSheet("background-color: #2a1a1f;")
            conversion_layout = QVBoxLayout(conversion_tab)
            print("DEBUG: Conversion tab widget created")
            self.logger.info("Conversion tab widget created")

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
            self.file_entry.setStyleSheet(
                "background-color: #afa060; color: black; padding: 5px;")
            file_layout.addWidget(self.file_entry)

            browse_button = QPushButton("Browse")
            browse_button.setStyleSheet(
                "background-color: #764134; color: black;")
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
            # Add more top margin for the title
            type_layout.setContentsMargins(15, 25, 15, 10)
            type_layout.setSpacing(10)  # Add spacing between radio buttons

            # Remove button group and auto-detect option since we only have one format
            self.xml_radio = QRadioButton("EndNote XML to BibTeX")
            self.xml_radio.setStyleSheet("color: white;")
            # Always checked since it's the only option
            self.xml_radio.setChecked(True)
            type_layout.addWidget(self.xml_radio)

            conversion_layout.addWidget(type_group)

            # Warning suppression
            warning_frame = QWidget()
            warning_layout = QHBoxLayout(warning_frame)
            warning_layout.setContentsMargins(5, 10, 5, 10)  # Add some margin

            self.suppress_warnings = QCheckBox(
                "Suppress missing field warnings")
            self.suppress_warnings.setStyleSheet("color: white;")
            self.suppress_warnings.setChecked(
                True)  # Default to suppress warnings
            warning_layout.addWidget(self.suppress_warnings)

            conversion_layout.addWidget(warning_frame)

            # Conversion Mode Selection
            mode_group = QGroupBox("Conversion Mode")
            mode_group.setStyleSheet("""
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
            mode_layout = QVBoxLayout(mode_group)
            mode_layout.setContentsMargins(15, 25, 15, 10)
            mode_layout.setSpacing(15)

            # Create button group for conversion modes
            self.conversion_mode_group = QButtonGroup(self)

            # Standard conversion mode
            self.standard_conversion_radio = QRadioButton(
                "Standard Conversion")
            self.standard_conversion_radio.setStyleSheet(
                "color: white; font-weight: bold;")
            self.standard_conversion_radio.setChecked(True)  # Default option
            standard_info = QLabel(
                "→ Fast conversion using only data from your XML file")
            standard_info.setStyleSheet(
                "color: #ccc; font-size: 11px; margin-left: 20px;")

            self.conversion_mode_group.addButton(
                self.standard_conversion_radio, 0)
            mode_layout.addWidget(self.standard_conversion_radio)
            mode_layout.addWidget(standard_info)

            # Enhanced conversion mode
            self.enhanced_conversion_radio = QRadioButton(
                "Enhanced Conversion with External APIs")
            self.enhanced_conversion_radio.setStyleSheet(
                "color: white; font-weight: bold;")
            enhanced_info = QLabel(
                "→ Enriches references by fetching missing data from Semantic Scholar & CrossRef")
            enhanced_info.setStyleSheet(
                "color: #ccc; font-size: 11px; margin-left: 20px;")
            enhanced_warning = QLabel(
                "   ⚠ Requires internet connection and may take longer")
            enhanced_warning.setStyleSheet(
                "color: #FFC107; font-size: 10px; margin-left: 20px;")

            self.conversion_mode_group.addButton(
                self.enhanced_conversion_radio, 1)
            mode_layout.addWidget(self.enhanced_conversion_radio)
            mode_layout.addWidget(enhanced_info)
            mode_layout.addWidget(enhanced_warning)

            # Connect mode change signal to update UI feedback
            self.standard_conversion_radio.toggled.connect(
                self._on_conversion_mode_changed)
            self.enhanced_conversion_radio.toggled.connect(
                self._on_conversion_mode_changed)

            print("DEBUG: Conversion mode radio buttons created")
            self.logger.info("Conversion mode radio buttons created")

            # Check API availability and configure the enhanced option
            print("DEBUG: About to call get_api_status()")
            self.logger.info("About to call get_api_status()")
            try:
                # Safely check API status
                if hasattr(self.xml_converter, 'get_api_status'):
                    api_status = self.xml_converter.get_api_status()
                    print(f"DEBUG: get_api_status() returned: {api_status}")
                    self.logger.info(
                        f"get_api_status() returned: {api_status}")

                    if isinstance(api_status, dict) and 'available' in api_status:
                        if not api_status.get('available', False):
                            # Disable enhanced conversion if API is not available
                            self.enhanced_conversion_radio.setEnabled(False)
                            self.enhanced_conversion_radio.setText(
                                "Enhanced Conversion with External APIs (Unavailable)")
                            enhanced_warning.setText(
                                "   ⚠ Install requirements: pip install requests fuzzywuzzy python-Levenshtein")
                            enhanced_warning.setStyleSheet(
                                "color: #F44336; font-size: 10px; margin-left: 20px;")
                    else:
                        # Fallback if api_status is not as expected
                        self.enhanced_conversion_radio.setEnabled(False)
                        self.enhanced_conversion_radio.setText(
                            "Enhanced Conversion with External APIs (Status check failed)")
                else:
                    # XML converter doesn't have get_api_status method
                    self.enhanced_conversion_radio.setEnabled(False)
                    self.enhanced_conversion_radio.setText(
                        "Enhanced Conversion with External APIs (Not supported)")

                print("DEBUG: API status configuration completed")
                self.logger.info("API status configuration completed")

            except Exception as e:
                error_msg = f"Error calling get_api_status(): {str(e)}"
                print(f"DEBUG ERROR: {error_msg}")
                self.logger.error(error_msg)
                self.logger.error(f"Traceback: {traceback.format_exc()}")

                # Set default values if API status check fails
                self.enhanced_conversion_radio.setEnabled(False)
                self.enhanced_conversion_radio.setText(
                    "Enhanced Conversion with External APIs (Error checking status)")

            # API status label
            self.api_status_label = QLabel()
            self.api_status_label.setStyleSheet(
                "color: #888; font-size: 10px;")
            print("DEBUG: About to update API status label")
            self.logger.info("About to update API status label")
            try:
                self._update_api_status_label()
                print("DEBUG: API status label updated")
                self.logger.info("API status label updated")
            except Exception as e:
                error_msg = f"Error updating API status label: {str(e)}"
                print(f"DEBUG ERROR: {error_msg}")
                self.logger.error(error_msg)
                # Set a default message if update fails
                self.api_status_label.setText("API status update failed")
                self.api_status_label.setStyleSheet(
                    "color: #F44336; font-size: 10px;")

            mode_layout.addWidget(self.api_status_label)
            conversion_layout.addWidget(mode_group)

            # Convert button
            convert_button = QPushButton("Convert Now")
            convert_button.setStyleSheet(
                "background-color: #764134; color: black; padding: 8px; font-weight: bold;")
            convert_button.clicked.connect(self.convert_file)
            conversion_layout.addWidget(convert_button)

            # Cancel button (initially hidden)
            self.cancel_button = QPushButton("Cancel Conversion")
            self.cancel_button.setStyleSheet(
                "background-color: #d32f2f; color: white; padding: 8px; font-weight: bold;")
            self.cancel_button.clicked.connect(self.cancel_conversion)
            self.cancel_button.hide()
            conversion_layout.addWidget(self.cancel_button)

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
            self.save_button.setStyleSheet(
                "background-color: #764134; color: black; padding: 8px; font-weight: bold;")
            self.save_button.clicked.connect(self.save_file)
            self.save_button.hide()  # Initially hidden
            save_buttons_layout.addWidget(self.save_button)

            self.quick_save_button = QPushButton("Save to Directory")
            self.quick_save_button.setStyleSheet(
                "background-color: #764134; color: black; padding: 8px;")
            self.quick_save_button.setToolTip(
                "Save as 'converted.bib' in a selected directory")
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

        except Exception as e:
            error_msg = f"Error in create_conversion_tab(): {str(e)}"
            print(f"DEBUG ERROR: {error_msg}")
            print(f"DEBUG TRACEBACK: {traceback.format_exc()}")
            self.logger.error(error_msg)
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            raise

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
        log_button.setStyleSheet(
            "background-color: #764134; color: black; padding: 8px;")
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
        self.save_dir_entry.setStyleSheet(
            "background-color: #afa060; color: black;")
        save_dir_layout.addWidget(self.save_dir_entry)

        save_dir_browse = QPushButton("Browse")
        save_dir_browse.setStyleSheet(
            "background-color: #764134; color: black;")
        save_dir_browse.clicked.connect(self.browse_save_dir)
        save_dir_layout.addWidget(save_dir_browse)

        settings_layout.addWidget(save_dir_frame)

        # BibTeX Style Selection
        style_group = QGroupBox("BibTeX Output Style")
        style_group.setStyleSheet("""
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
        style_layout = QVBoxLayout(style_group)
        style_layout.setContentsMargins(15, 25, 15, 10)
        style_layout.setSpacing(10)

        self.bibtex_style = QButtonGroup(self)

        self.standard_bibtex_radio = QRadioButton("Standard BibTeX")
        self.standard_bibtex_radio.setChecked(True)
        self.standard_bibtex_radio.setStyleSheet("color: white;")
        self.bibtex_style.addButton(self.standard_bibtex_radio, 0)
        style_layout.addWidget(self.standard_bibtex_radio)

        self.acm_bibtex_radio = QRadioButton("ACM BibTeX Format")
        self.acm_bibtex_radio.setStyleSheet("color: white;")
        self.bibtex_style.addButton(self.acm_bibtex_radio, 1)
        style_layout.addWidget(self.acm_bibtex_radio)

        settings_layout.addWidget(style_group)

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
        # Add more top margin for the title
        endnote_layout.setContentsMargins(15, 25, 15, 10)
        endnote_layout.setSpacing(10)  # Add spacing between checkboxes

        self.styled_text = QCheckBox("Extract styled text (for EndNote XML)")
        self.styled_text.setStyleSheet("color: white;")
        self.styled_text.setChecked(True)
        endnote_layout.addWidget(self.styled_text)

        settings_layout.addWidget(endnote_group)

        # BibTeX Format Options
        format_group = QGroupBox("BibTeX Format Options")
        format_group.setStyleSheet("""
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
        format_layout = QVBoxLayout(format_group)
        format_layout.setContentsMargins(15, 25, 15, 10)
        format_layout.setSpacing(10)

        self.use_string_defs = QCheckBox("Use String Definitions")
        self.use_string_defs.setStyleSheet("color: white;")
        self.use_string_defs.setChecked(True)
        self.use_string_defs.setToolTip(
            "Generate @String definitions for journals and publishers")
        format_layout.addWidget(self.use_string_defs)

        self.use_biblatex = QCheckBox("Use BibLaTeX Field Names")
        self.use_biblatex.setStyleSheet("color: white;")
        self.use_biblatex.setChecked(False)
        self.use_biblatex.setToolTip(
            "Use BibLaTeX field names instead of standard BibTeX")
        format_layout.addWidget(self.use_biblatex)

        self.escape_latex = QCheckBox("Escape LaTeX Special Characters")
        self.escape_latex.setStyleSheet("color: white;")
        self.escape_latex.setChecked(True)
        self.escape_latex.setToolTip(
            "Automatically escape special LaTeX characters")
        format_layout.addWidget(self.escape_latex)

        settings_layout.addWidget(format_group)

        # General UI spacing
        settings_layout.setSpacing(15)  # Add general spacing between elements
        # Add margins around all elements
        settings_layout.setContentsMargins(20, 20, 20, 20)

        # Save settings button
        save_settings = QPushButton("Save Settings")
        save_settings.setStyleSheet(
            "background-color: #764134; color: black; padding: 8px;")
        save_settings.clicked.connect(self.save_settings)
        settings_layout.addWidget(save_settings)

        settings_layout.addStretch()

        # Add tab to tab widget
        self.tab_widget.addTab(settings_tab, "Settings")

    def _on_conversion_mode_changed(self):
        """Handle conversion mode changes to provide user feedback."""
        try:
            if hasattr(self, 'enhanced_conversion_radio') and self.enhanced_conversion_radio.isChecked():
                self.logger.info("User selected Enhanced Conversion mode")
            elif hasattr(self, 'standard_conversion_radio') and self.standard_conversion_radio.isChecked():
                self.logger.info("User selected Standard Conversion mode")
        except Exception as e:
            print(f"Error in _on_conversion_mode_changed: {str(e)}")

    def _update_api_status_label(self):
        """Update the API status label with current status"""
        try:
            if hasattr(self.xml_converter, 'get_api_status'):
                api_status = self.xml_converter.get_api_status()

                if isinstance(api_status, dict):
                    if api_status.get('available', False):
                        self.api_status_label.setText(
                            "✓ Enhanced conversion mode available - fetches missing metadata from external APIs")
                        self.api_status_label.setStyleSheet(
                            "color: #4CAF50; font-size: 10px;")
                    else:
                        self.api_status_label.setText(
                            "⚠ Enhanced conversion unavailable - install: pip install requests fuzzywuzzy python-Levenshtein")
                        self.api_status_label.setStyleSheet(
                            "color: #F44336; font-size: 10px;")
                else:
                    self.api_status_label.setText("API status unavailable")
                    self.api_status_label.setStyleSheet(
                        "color: #888; font-size: 10px;")
            else:
                self.api_status_label.setText(
                    "Enhanced conversion not supported")
                self.api_status_label.setStyleSheet(
                    "color: #888; font-size: 10px;")
        except Exception as e:
            self.api_status_label.setText(f"API status error: {str(e)}")
            self.api_status_label.setStyleSheet(
                "color: #F44336; font-size: 10px;")

    def browse_file(self):
        try:
            print("DEBUG: Starting browse_file()")
            self.logger.info("Starting file browser")

            # Use native=False to avoid macOS native dialog issues
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Select EndNote XML File",
                os.path.expanduser("~"),  # Start in home directory
                "XML Files (*.xml);;All Files (*.*)",
                options=QFileDialog.DontUseNativeDialog  # Avoid native dialog on macOS
            )

            print(f"DEBUG: File dialog returned: {file_path}")

            if file_path:
                self.file_entry.setText(file_path)
                self.logger.info(f"Selected file: {file_path}")
                print(f"DEBUG: File path set in entry: {file_path}")
            else:
                print("DEBUG: No file selected")
                self.logger.info("File selection cancelled by user")

        except Exception as e:
            error_msg = f"Error in browse_file(): {str(e)}"
            print(f"DEBUG ERROR: {error_msg}")
            print(f"DEBUG TRACEBACK: {traceback.format_exc()}")
            self.logger.error(error_msg)
            self.logger.error(f"Traceback: {traceback.format_exc()}")

            # Show error to user
            QMessageBox.critical(self, "File Browser Error",
                                 f"An error occurred while opening the file browser:\n{str(e)}")
            # No need to auto-select radio button since there's only one option

    def browse_save_dir(self):
        try:
            print("DEBUG: Starting browse_save_dir()")
            self.logger.info("Starting directory browser")

            # Use native=False to avoid macOS native dialog issues
            dir_path = QFileDialog.getExistingDirectory(
                self,
                "Select Default Save Directory",
                os.path.expanduser("~"),  # Start in user's home directory
                options=QFileDialog.DontUseNativeDialog  # Avoid native dialog on macOS
            )

            print(f"DEBUG: Directory dialog returned: {dir_path}")

            if dir_path:
                self.save_dir_entry.setText(dir_path)
                self.logger.info(f"Selected directory: {dir_path}")
                print(f"DEBUG: Directory path set in entry: {dir_path}")
            else:
                print("DEBUG: No directory selected")
                self.logger.info("Directory selection cancelled by user")

        except Exception as e:
            error_msg = f"Error in browse_save_dir(): {str(e)}"
            print(f"DEBUG ERROR: {error_msg}")
            print(f"DEBUG TRACEBACK: {traceback.format_exc()}")
            self.logger.error(error_msg)
            self.logger.error(f"Traceback: {traceback.format_exc()}")

            # Show error to user
            QMessageBox.critical(self, "Directory Browser Error",
                                 f"An error occurred while opening the directory browser:\n{str(e)}")

    def save_settings(self):
        QMessageBox.information(self, "Settings Saved",
                                "Your settings have been saved.")

    def convert_file(self):
        file_path = self.file_entry.text()
        if not file_path:
            QMessageBox.warning(self, "Warning", "Please select a file first")
            self.logger.warning(
                "Conversion attempted without selecting a file")
            return

        if not os.path.exists(file_path):
            error_msg = f"File not found: {file_path}"
            self.log_error(error_msg)
            return

        # Check if the file is a log file by name
        if os.path.basename(file_path).lower() == "conversion_log.txt":
            error_msg = "The selected file appears to be a log file, not a reference file."
            QMessageBox.warning(self, "Invalid File", error_msg)
            self.logger.warning(error_msg)
            return

        # Check if a conversion is already running
        if self.conversion_worker and self.conversion_worker.isRunning():
            QMessageBox.warning(self, "Conversion in Progress",
                                "A conversion is already in progress. Please wait or cancel it first.")
            return

        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as file:
                file_data = file.read()

            # Improved log file detection
            log_file_pattern = r'\[\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}\]'
            if re.search(log_file_pattern, file_data) and ("INFO:" in file_data or "ERROR:" in file_data or "WARNING:" in file_data):
                error_msg = "The selected file appears to be a log file, not a reference file."
                QMessageBox.warning(self, "Invalid File", error_msg)
                self.logger.warning(error_msg)
                return

            # Reset UI elements
            self.progress_label.setText("Preparing conversion...")
            self.complete_label.setText("")
            self.log_text.clear()
            self.progress_bar.setValue(0)
            self.save_button.hide()
            self.quick_save_button.hide()
            self.cancel_button.show()
            self.converted_text = None

            # Log the conversion attempt
            self.logger.info(f"Starting conversion of file: {file_path}")

            # Prepare settings for the worker thread
            settings = {
                'suppress_warnings': self.suppress_warnings.isChecked(),
                'api_enabled': hasattr(self, 'enhanced_conversion_radio') and self.enhanced_conversion_radio.isChecked(),
                'styled_text': self.styled_text.isChecked(),
                'use_acm_style': hasattr(self, 'acm_bibtex_radio') and self.acm_bibtex_radio.isChecked(),
                'use_string_defs': hasattr(self, 'use_string_defs') and self.use_string_defs.isChecked(),
                'use_biblatex': hasattr(self, 'use_biblatex') and self.use_biblatex.isChecked(),
                'escape_latex': hasattr(self, 'escape_latex') and self.escape_latex.isChecked()
            }

            # Create and configure the worker thread
            self.conversion_worker = ConversionWorker(
                self.xml_converter, file_data, settings)

            # Connect signals
            self.conversion_worker.progress_updated.connect(
                self.update_progress)
            self.conversion_worker.progress_text_updated.connect(
                self.update_progress_text)
            self.conversion_worker.log_message.connect(self.add_log_message)
            self.conversion_worker.conversion_finished.connect(
                self.on_conversion_finished)
            self.conversion_worker.conversion_failed.connect(
                self.on_conversion_failed)

            # Start the progress monitor
            self.progress_monitor.start_monitoring()

            # Start the conversion worker
            self.conversion_worker.start()

        except Exception as e:
            error_message = f"Error starting conversion: {str(e)}"
            self.log_error(error_message)
            self.logger.error(
                f"Exception starting conversion of {file_path}: {str(e)}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")

    def cancel_conversion(self):
        """Cancel the ongoing conversion."""
        if self.conversion_worker and self.conversion_worker.isRunning():
            self.conversion_worker.cancel_conversion()
            self.conversion_worker.quit()
            self.conversion_worker.wait(3000)  # Wait up to 3 seconds

            self.progress_monitor.stop_monitoring()

            self.progress_label.setText("Conversion Cancelled")
            self.progress_bar.setValue(0)
            self.cancel_button.hide()
            self.complete_label.setText("Conversion was cancelled by user")
            self.complete_label.setStyleSheet("color: orange;")

            self.logger.info("Conversion cancelled by user")

    def update_progress(self, value):
        """Update the progress bar."""
        self.progress_bar.setValue(value)

    def update_progress_text(self, text):
        """Update the progress label text."""
        self.progress_label.setText(text)

    def add_log_message(self, message):
        """Add a message to the log display."""
        self.log_text.append(message)

    def on_conversion_finished(self, bib_entry):
        """Handle successful conversion completion."""
        try:
            self.progress_monitor.stop_monitoring()
            self.cancel_button.hide()

            self.progress_bar.setValue(100)
            self.progress_label.setText("Conversion Complete")
            self.complete_label.setText("Conversion completed successfully!")
            self.complete_label.setStyleSheet("color: white;")
            self.converted_text = bib_entry
            self.save_button.show()
            self.quick_save_button.show()

            # Create preview of the converted text
            preview = bib_entry[:500] + \
                "..." if len(bib_entry) > 500 else bib_entry
            self.log_text.append("\nPreview of converted BibTeX:\n")
            self.log_text.append(preview)

            # Log success
            entry_count = bib_entry.count('@')
            self.log_text.append(f"\nGenerated {entry_count} BibTeX entries")
            self.log_text.append("Conversion completed successfully!")

            # Log detailed success information
            conversion_method = "EndNote XML to BibTeX"
            if hasattr(self, 'acm_bibtex_radio') and self.acm_bibtex_radio.isChecked():
                conversion_method += " (ACM Style)"

            # Add conversion mode to the method description
            if hasattr(self, 'enhanced_conversion_radio') and self.enhanced_conversion_radio.isChecked():
                conversion_method += " - Enhanced Mode"
            else:
                conversion_method += " - Standard Mode"

            success_msg = (
                f"Conversion completed successfully. "
                f"File: {os.path.basename(self.file_entry.text())}, "
                f"Method: {conversion_method}, "
                f"Entries: {entry_count}"
            )
            self.logger.success(success_msg)

        except Exception as e:
            self.logger.error(f"Error in on_conversion_finished: {str(e)}")

    def on_conversion_failed(self, error_message):
        """Handle conversion failure."""
        try:
            self.progress_monitor.stop_monitoring()
            self.cancel_button.hide()

            self.log_error(error_message)
            self.progress_label.setText("Conversion Failed")
            self.complete_label.setText("An error occurred during conversion.")
            self.complete_label.setStyleSheet("color: red;")
            self.progress_bar.setValue(0)

        except Exception as e:
            self.logger.error(f"Error in on_conversion_failed: {str(e)}")

    def save_file(self):
        if not self.converted_text:
            QMessageBox.warning(self, "Warning", "No converted data to save")
            self.logger.warning("Save attempted with no converted data")
            return

        try:
            print("DEBUG: Starting save_file()")
            self.logger.info("Starting save file dialog")

            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save BibTeX File",
                os.path.join(os.path.expanduser("~"), "converted.bib"),
                "BibTeX Files (*.bib);;Text Files (*.txt);;All Files (*.*)",
                options=QFileDialog.DontUseNativeDialog  # Avoid native dialog on macOS
            )

            print(f"DEBUG: Save dialog returned: {file_path}")

            if file_path:
                self.logger.info(f"Saving file as: {file_path}")
                self._save_to_path(file_path)
            else:
                print("DEBUG: Save cancelled by user")
                self.logger.info("Save cancelled by user")

        except Exception as e:
            error_msg = f"Error in save_file(): {str(e)}"
            print(f"DEBUG ERROR: {error_msg}")
            print(f"DEBUG TRACEBACK: {traceback.format_exc()}")
            self.logger.error(error_msg)
            self.logger.error(f"Traceback: {traceback.format_exc()}")

            # Show error to user
            QMessageBox.critical(self, "Save Dialog Error",
                                 f"An error occurred while opening the save dialog:\n{str(e)}")

    def quick_save_file(self):
        if not self.converted_text:
            QMessageBox.warning(self, "Warning", "No converted data to save")
            self.logger.warning("Quick save attempted with no converted data")
            return

        try:
            print("DEBUG: Starting quick_save_file()")
            self.logger.info("Starting quick save directory dialog")

            # Ask user to select a directory
            dir_path = QFileDialog.getExistingDirectory(
                self,
                "Select Directory to Save",
                os.path.expanduser("~"),  # Start in user's home directory
                options=QFileDialog.DontUseNativeDialog  # Avoid native dialog on macOS
            )

            print(f"DEBUG: Quick save dialog returned: {dir_path}")

            if not dir_path:
                self.logger.info("Directory selection canceled by user")
                print("DEBUG: No directory selected")
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
                    self.logger.info(
                        "User chose not to overwrite existing file")
                    return
                else:
                    self.logger.info("User chose to overwrite existing file")

            # Save the file
            self._save_to_path(file_path)

        except Exception as e:
            error_msg = f"Error in quick_save_file(): {str(e)}"
            print(f"DEBUG ERROR: {error_msg}")
            print(f"DEBUG TRACEBACK: {traceback.format_exc()}")
            self.logger.error(error_msg)
            self.logger.error(f"Traceback: {traceback.format_exc()}")

            # Show error to user
            QMessageBox.critical(self, "Quick Save Error",
                                 f"An error occurred during quick save:\n{str(e)}")

    def _save_to_path(self, file_path):
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(self.converted_text)

            self.complete_label.setText(
                f"File saved as {os.path.basename(file_path)}")
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
        # Switch to log tab to show the error
        self.tab_widget.setCurrentIndex(1)

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

    def update_log_display(self, new_content):
        """Update the log display with new content from the log file."""
        if hasattr(self, 'log_text'):
            # Move cursor to end and append new content
            cursor = self.log_text.textCursor()
            cursor.movePosition(cursor.End)
            cursor.insertText(new_content)
            # Auto-scroll to bottom
            self.log_text.ensureCursorVisible()

    def closeEvent(self, event):
        """Handle application close event to clean up threads."""
        try:
            # Stop the progress monitor
            if hasattr(self, 'progress_monitor') and self.progress_monitor:
                self.progress_monitor.stop_monitoring()

            # Cancel any running conversion
            if hasattr(self, 'conversion_worker') and self.conversion_worker and self.conversion_worker.isRunning():
                self.conversion_worker.cancel_conversion()
                self.conversion_worker.quit()
                self.conversion_worker.wait(3000)  # Wait up to 3 seconds

            self.logger.info("Application closing - threads cleaned up")

        except Exception as e:
            print(f"Error during cleanup: {str(e)}")

        event.accept()


class ConversionWorker(QThread):
    """Worker thread for handling file conversion without blocking the GUI."""

    # Define signals for communication with the main thread
    progress_updated = pyqtSignal(int)  # Progress percentage (0-100)
    progress_text_updated = pyqtSignal(str)  # Progress text message
    log_message = pyqtSignal(str)  # Log messages to display
    conversion_finished = pyqtSignal(str)  # Finished with result (BibTeX text)
    conversion_failed = pyqtSignal(str)  # Failed with error message

    def __init__(self, xml_converter, file_data, settings):
        super().__init__()
        self.xml_converter = xml_converter
        self.file_data = file_data
        self.settings = settings
        self.is_cancelled = False
        self.total_records = 0
        self.current_record = 0

    def cancel_conversion(self):
        """Cancel the conversion process."""
        self.is_cancelled = True

    def run(self):
        """Main conversion process running in background thread."""
        try:
            self.progress_text_updated.emit("Starting conversion...")
            self.progress_updated.emit(5)

            if self.is_cancelled:
                return

            # Apply settings to XML converter
            self.xml_converter.suppress_warnings = self.settings.get(
                'suppress_warnings', True)
            self.xml_converter.set_api_enhancement(
                self.settings.get('api_enabled', False))
            self.xml_converter.extract_styled_text = self.settings.get(
                'styled_text', True)
            self.xml_converter.use_acm_style = self.settings.get(
                'use_acm_style', False)

            if self.settings.get('use_string_defs'):
                self.xml_converter.use_string_definitions = self.settings['use_string_defs']
            if self.settings.get('use_biblatex'):
                self.xml_converter.use_biblatex_fields = self.settings['use_biblatex']
            if self.settings.get('escape_latex'):
                self.xml_converter.escape_latex_chars = self.settings['escape_latex']

            self.progress_text_updated.emit("Analyzing XML structure...")
            self.progress_updated.emit(10)

            # First, analyze the XML to count records
            try:
                import xml.etree.ElementTree as ET
                root = ET.fromstring(self.file_data)
                records = root.findall('.//record')
                self.total_records = len(records)
                self.log_message.emit(
                    f"Found {self.total_records} records to process")
                self.progress_text_updated.emit(
                    f"Found {self.total_records} records to process...")
            except Exception as e:
                self.log_message.emit(
                    f"Warning: Could not count records: {str(e)}")
                self.total_records = 0

            self.progress_updated.emit(15)

            # Log the conversion mode being used
            if self.settings.get('api_enabled'):
                self.log_message.emit(
                    "🔍 Enhanced Conversion Mode: Will fetch missing metadata from Semantic Scholar and CrossRef")
                self.log_message.emit(
                    "   This may take longer but will provide more complete references...")
            else:
                self.log_message.emit(
                    "⚡ Standard Conversion Mode: Using only data from your XML file for fast processing")

            if self.is_cancelled:
                return

            conversion_mode = "Enhanced" if self.settings.get(
                'api_enabled') else "Standard"
            self.progress_text_updated.emit(
                f"Processing EndNote XML file ({conversion_mode} mode)...")
            self.progress_updated.emit(20)

            # Set up progress callback for the XML converter
            def progress_callback(current, total, message=""):
                if self.is_cancelled:
                    return False  # Signal to stop processing

                # Calculate progress: 20% to 90% for conversion
                if total > 0:
                    conversion_progress = int(20 + (current / total) * 70)
                    self.progress_updated.emit(conversion_progress)

                # Use the message from the XML converter, or create a default one
                if message:
                    self.progress_text_updated.emit(message)
                else:
                    self.progress_text_updated.emit(
                        f"Processing record {current}/{total}...")

                return True  # Continue processing

            # Try to set the progress callback if the XML converter supports it
            if hasattr(self.xml_converter, 'set_progress_callback'):
                self.xml_converter.set_progress_callback(progress_callback)

            if self.is_cancelled:
                return

            # Perform the actual conversion
            bib_entry = self.xml_converter.convert_to_bibtex(self.file_data)

            if self.is_cancelled:
                return

            if not bib_entry:
                self.conversion_failed.emit(
                    "Conversion failed: No BibTeX entries generated")
                return

            self.progress_text_updated.emit("Finalizing conversion...")
            self.progress_updated.emit(95)

            # Count entries for logging
            entry_count = bib_entry.count('@')
            self.log_message.emit(f"Generated {entry_count} BibTeX entries")

            self.progress_text_updated.emit(
                "Conversion completed successfully!")
            self.progress_updated.emit(100)

            # Signal successful completion
            self.conversion_finished.emit(bib_entry)

        except Exception as e:
            if not self.is_cancelled:
                self.conversion_failed.emit(
                    f"Error during conversion: {str(e)}")


class ProgressMonitor(QThread):
    """Thread for monitoring conversion progress and updating logs."""

    log_updated = pyqtSignal(str)  # New log content

    def __init__(self, log_file="conversion_log.txt"):
        super().__init__()
        self.log_file = log_file
        self.last_position = 0
        self.monitoring = False

    def start_monitoring(self):
        """Start monitoring the log file."""
        self.monitoring = True
        try:
            # Get current file size to start reading from the end
            if os.path.exists(self.log_file):
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    f.seek(0, 2)  # Go to end of file
                    self.last_position = f.tell()
        except:
            self.last_position = 0
        self.start()

    def stop_monitoring(self):
        """Stop monitoring the log file."""
        self.monitoring = False
        self.quit()
        self.wait()

    def run(self):
        """Monitor log file for new content."""
        while self.monitoring:
            try:
                if os.path.exists(self.log_file):
                    with open(self.log_file, 'r', encoding='utf-8') as f:
                        f.seek(self.last_position)
                        new_content = f.read()
                        if new_content:
                            self.log_updated.emit(new_content)
                            self.last_position = f.tell()

                # Sleep for a short time before checking again
                self.msleep(100)  # Check every 100ms

            except Exception:
                # If there's an error reading the file, continue monitoring
                self.msleep(500)


def main():
    print("DEBUG: Starting main() function")

    try:
        print("DEBUG: Creating QApplication")
        app = QApplication(sys.argv)
        print("DEBUG: QApplication created successfully")

        print("DEBUG: Creating MainApp window")
        window = MainApp()
        print("DEBUG: MainApp window created successfully")

        print("DEBUG: Showing window")
        window.show()
        print("DEBUG: Window shown successfully")

        print("DEBUG: Starting application event loop")
        sys.exit(app.exec_())

    except Exception as e:
        error_msg = f"Error in main(): {str(e)}"
        print(f"DEBUG ERROR: {error_msg}")
        print(f"DEBUG TRACEBACK: {traceback.format_exc()}")

        # Try to log the error if possible
        try:
            logger = Logger()
            logger.error(error_msg)
            logger.error(f"Traceback: {traceback.format_exc()}")
        except:
            pass  # If logging fails, just print

        raise


if __name__ == "__main__":
    print("DEBUG: Script started")
    main()
