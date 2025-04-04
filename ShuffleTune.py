import os
import random
import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QFileDialog, QMessageBox,
                             QProgressBar, QGroupBox, QCheckBox)
from PySide6.QtCore import Qt, QTimer, QThread, Signal
from PySide6.QtGui import QFont

class RenameWorker(QThread):
    progress_updated = Signal(int, str)
    finished = Signal(bool, str)
    
    def __init__(self, files, folder, pattern, add_number_prefix, parent=None):
        super().__init__(parent)
        self.files = files
        self.folder = folder
        self.pattern = pattern
        self.add_number_prefix = add_number_prefix
        self._is_running = True
        
    def run(self):
        try:
            for i, file in enumerate(self.files):
                if not self._is_running:
                    break
                    
                index = str(i + 1).zfill(len(str(len(self.files))))
                name, ext = os.path.splitext(file)
                
                if self.add_number_prefix:
                    new_name = f"{index} - {name}{ext}"
                else:
                    new_name = self.pattern.replace("{index}", index).replace("{name}", name) + ext
                
                old_path = os.path.join(self.folder, file)
                new_path = os.path.join(self.folder, new_name)
                
                # Handle potential name collisions
                counter = 1
                while os.path.exists(new_path):
                    new_name = f"{name} ({counter}){ext}"
                    new_path = os.path.join(self.folder, new_name)
                    counter += 1
                
                os.rename(old_path, new_path)
                self.progress_updated.emit(i + 1, new_name)
                
            self.finished.emit(self._is_running, "Operation completed successfully" if self._is_running else "Operation cancelled")
            
        except Exception as e:
            self.finished.emit(False, f"Error: {str(e)}")
            
    def stop(self):
        self._is_running = False

class ShuffleTune(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Window settings
        self.setWindowTitle("ShuffleTune - MP3 Shuffler")
        self.setGeometry(100, 100, 900, 500)
        self.setMinimumSize(700, 400)
        
        # State variables
        self.files = []
        self.language = "en"  # "pt" or "en"
        self.rename_worker = None
        
        # Create widgets
        self.create_widgets()
        self.setup_ui()
        self.setup_styles()
        self.connect_signals()
        
        # Initialize with English
        self.set_language("en")
        
    def create_widgets(self):
        """Create all necessary widgets"""
        # Folder selection widgets
        self.lbl_folder = QLabel()
        self.txt_folder = QLineEdit()
        self.txt_folder.setPlaceholderText("Select folder containing MP3 files")
        self.btn_browse = QPushButton()
        
        # Format widgets
        self.lbl_format = QLabel()
        self.txt_format = QLineEdit("{index} - {name}")
        self.chk_add_prefix = QCheckBox("Add sequential number prefix")
        self.chk_add_prefix.setChecked(True)
        
        # Action buttons
        self.btn_shuffle = QPushButton()
        self.btn_rename = QPushButton()
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setVisible(False)
        
        # Progress bar
        self.progress = QProgressBar()
        self.progress.setAlignment(Qt.AlignCenter)
        self.lbl_status = QLabel("Ready")
        self.lbl_status.setAlignment(Qt.AlignCenter)
        
        # Language buttons
        self.btn_lang_pt = QPushButton("Português")
        self.btn_lang_en = QPushButton("English")
        
        # Instructions group
        self.grp_instructions = QGroupBox()
        self.lbl_instructions = QLabel()
        self.lbl_instructions.setWordWrap(True)
        
        # Preview
        self.grp_preview = QGroupBox("Preview")
        self.lbl_preview = QLabel("Original name -> New name")
        self.lbl_preview.setWordWrap(True)
        
    def setup_ui(self):
        """Organize widgets in the interface"""
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # Main layout
        main_layout = QHBoxLayout()
        main_widget.setLayout(main_layout)
        
        # Left panel (controls)
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        left_panel.setLayout(left_layout)
        
        # Right panel (instructions and preview)
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        right_panel.setLayout(right_layout)
        
        # Add widgets to left panel
        left_layout.addWidget(self.lbl_folder)
        left_layout.addWidget(self.txt_folder)
        left_layout.addWidget(self.btn_browse)
        left_layout.addSpacing(15)
        
        left_layout.addWidget(self.lbl_format)
        left_layout.addWidget(self.txt_format)
        left_layout.addWidget(self.chk_add_prefix)
        left_layout.addSpacing(15)
        
        # Layout for action buttons
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.btn_shuffle)
        btn_layout.addWidget(self.btn_rename)
        btn_layout.addWidget(self.btn_cancel)
        left_layout.addLayout(btn_layout)
        left_layout.addSpacing(15)
        
        left_layout.addWidget(self.progress)
        left_layout.addWidget(self.lbl_status)
        left_layout.addStretch()
        
        # Layout for language buttons
        lang_layout = QHBoxLayout()
        lang_layout.addWidget(self.btn_lang_pt)
        lang_layout.addWidget(self.btn_lang_en)
        left_layout.addLayout(lang_layout)
        
        # Add instructions to right panel
        right_layout.addWidget(self.grp_instructions)
        instructions_inner = QVBoxLayout()
        instructions_inner.addWidget(self.lbl_instructions)
        self.grp_instructions.setLayout(instructions_inner)
        
        # Add preview to right panel
        right_layout.addWidget(self.grp_preview)
        preview_inner = QVBoxLayout()
        preview_inner.addWidget(self.lbl_preview)
        self.grp_preview.setLayout(preview_inner)
        
        right_layout.addStretch()
        
        # Add panels to main layout
        main_layout.addWidget(left_panel, 60)
        main_layout.addWidget(right_panel, 40)
        
    def setup_styles(self):
        """Apply CSS styles"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2C3E50;
            }
            QLabel, QGroupBox {
                color: white;
                font-size: 14px;
            }
            QGroupBox {
                border: 1px solid #34495E;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QLineEdit, QPushButton {
                padding: 8px;
                font-size: 14px;
                border-radius: 4px;
            }
            QPushButton {
                min-width: 100px;
                background-color: #3498db;
                color: white;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #1c6da8;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
            #btn_shuffle {
                background-color: #f39c12;
            }
            #btn_shuffle:hover {
                background-color: #e67e22;
            }
            #btn_rename {
                background-color: #2ecc71;
            }
            #btn_rename:hover {
                background-color: #27ae60;
            }
            #btn_cancel {
                background-color: #e74c3c;
            }
            #btn_cancel:hover {
                background-color: #c0392b;
            }
            QProgressBar {
                height: 25px;
                text-align: center;
                border: 1px solid #34495E;
                border-radius: 4px;
            }
            QProgressBar::chunk {
                background-color: #3498db;
                border-radius: 2px;
            }
            QLineEdit {
                background-color: #34495E;
                color: white;
                border: 1px solid #3d566e;
            }
            QCheckBox {
                color: white;
                spacing: 5px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
        """)
        
        # IDs for specific styling
        self.btn_shuffle.setObjectName("btn_shuffle")
        self.btn_rename.setObjectName("btn_rename")
        self.btn_cancel.setObjectName("btn_cancel")
        
        # Font for status label
        font = QFont()
        font.setItalic(True)
        self.lbl_status.setFont(font)
        
    def connect_signals(self):
        """Connect signals to slots"""
        self.btn_browse.clicked.connect(self.browse_folder)
        self.btn_shuffle.clicked.connect(self.shuffle_files)
        self.btn_rename.clicked.connect(self.rename_files)
        self.btn_cancel.clicked.connect(self.cancel_operation)
        self.btn_lang_pt.clicked.connect(lambda: self.set_language("pt"))
        self.btn_lang_en.clicked.connect(lambda: self.set_language("en"))
        self.txt_folder.textChanged.connect(self.update_file_list)
        self.txt_format.textChanged.connect(self.update_preview)
        self.chk_add_prefix.toggled.connect(self.on_add_prefix_toggled)
        
    def on_add_prefix_toggled(self, checked):
        """Enable/disable format field based on checkbox"""
        self.txt_format.setEnabled(not checked)
        self.update_preview()
        
    def update_file_list(self):
        """Update the file list when folder changes"""
        folder = self.txt_folder.text()
        if folder and os.path.isdir(folder):
            self.files = [f for f in os.listdir(folder) if f.lower().endswith('.mp3')]
            self.lbl_status.setText(f"Found {len(self.files)} MP3 files")
            self.update_preview()
        else:
            self.files = []
            self.lbl_status.setText("Ready")
            
    def update_preview(self):
        """Update the preview of renaming"""
        if not self.files:
            self.lbl_preview.setText("Original name -> New name")
            return
            
        sample_file = self.files[0]
        name, ext = os.path.splitext(sample_file)
        
        if self.chk_add_prefix.isChecked():
            new_name = f"001 - {name}{ext}"
        else:
            pattern = self.txt_format.text()
            new_name = pattern.replace("{index}", "001").replace("{name}", name) + ext
            
        self.lbl_preview.setText(f"{sample_file} -> {new_name}")
        
    def browse_folder(self):
        """Open dialog to select folder"""
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.txt_folder.setText(folder)
            
    def shuffle_files(self):
        """Shuffle the MP3 files"""
        if not self.txt_folder.text():
            self.show_message("Error", "Please select a folder first", QMessageBox.Warning)
            return
            
        if not self.files:
            self.show_message("Error", "No MP3 files found", QMessageBox.Warning)
            return
            
        random.shuffle(self.files)
        self.show_message("Success", "Files shuffled successfully!", QMessageBox.Information)
        self.update_preview()
        
    def rename_files(self):
        """Rename files according to the pattern"""
        folder = self.txt_folder.text()
        if not folder:
            self.show_message("Error", "Please select a folder first", QMessageBox.Warning)
            return
            
        if not self.files:
            self.show_message("Error", "No MP3 files found", QMessageBox.Warning)
            return
            
        if not self.chk_add_prefix.isChecked():
            pattern = self.txt_format.text()
            if "{index}" not in pattern and "{name}" not in pattern:
                self.show_message("Error", "Pattern must contain {index} or {name}", QMessageBox.Warning)
                return
                
        # Disable buttons during operation
        self.btn_shuffle.setDisabled(True)
        self.btn_rename.setDisabled(True)
        self.btn_browse.setDisabled(True)
        self.btn_cancel.setVisible(True)
        
        self.progress.setMaximum(len(self.files))
        self.progress.setValue(0)
        self.lbl_status.setText("Starting renaming...")
        
        # Start worker thread
        self.rename_worker = RenameWorker(
            self.files,
            folder,
            self.txt_format.text(),
            self.chk_add_prefix.isChecked()
        )
        self.rename_worker.progress_updated.connect(self.on_rename_progress)
        self.rename_worker.finished.connect(self.on_rename_finished)
        self.rename_worker.start()
        
    def on_rename_progress(self, current, new_name):
        """Update progress during renaming"""
        self.progress.setValue(current)
        self.lbl_status.setText(f"Renaming: {new_name}")
        
    def on_rename_finished(self, success, message):
        """Handle completion of renaming"""
        self.btn_shuffle.setDisabled(False)
        self.btn_rename.setDisabled(False)
        self.btn_browse.setDisabled(False)
        self.btn_cancel.setVisible(False)
        
        if success:
            self.lbl_status.setText("Operation completed successfully")
            self.show_message("Success", message, QMessageBox.Information)
        else:
            self.lbl_status.setText("Operation failed")
            self.show_message("Error", message, QMessageBox.Critical)
            
        # Refresh file list
        self.update_file_list()
        
    def cancel_operation(self):
        """Cancel the current renaming operation"""
        if self.rename_worker and self.rename_worker.isRunning():
            self.rename_worker.stop()
            self.lbl_status.setText("Cancelling operation...")
            
    def set_language(self, lang):
        """Change the interface language"""
        self.language = lang
        if lang == "pt":
            self.setWindowTitle("ShuffleTune - Embaralhador de MP3")
            self.lbl_folder.setText("Pasta:")
            self.txt_folder.setPlaceholderText("Selecione a pasta com arquivos MP3")
            self.btn_browse.setText("Procurar")
            self.lbl_format.setText("Formato:")
            self.chk_add_prefix.setText("Adicionar prefixo numérico sequencial")
            self.btn_shuffle.setText("Embaralhar")
            self.btn_rename.setText("Renomear")
            self.btn_cancel.setText("Cancelar")
            self.grp_instructions.setTitle("Instruções:")
            self.lbl_instructions.setText(
                "1. Selecione uma pasta com arquivos MP3\n"
                "2. Defina o formato de renomeação\n"
                "3. Embaralhe os arquivos\n"
                "4. Renomeie com a nova ordem\n\n"
                "Dicas:\n"
                "- Use {index} para o número sequencial\n"
                "- Use {name} para o nome original\n"
                "- Marque a opção para adicionar prefixo automático"
            )
            self.grp_preview.setTitle("Pré-visualização")
            self.lbl_preview.setText("Nome original -> Novo nome")
            self.btn_lang_pt.setStyleSheet("background-color: #16a085;")
            self.btn_lang_en.setStyleSheet("")
        else:
            self.setWindowTitle("ShuffleTune - MP3 Shuffler")
            self.lbl_folder.setText("Folder:")
            self.txt_folder.setPlaceholderText("Select folder containing MP3 files")
            self.btn_browse.setText("Browse")
            self.lbl_format.setText("Format:")
            self.chk_add_prefix.setText("Add sequential number prefix")
            self.btn_shuffle.setText("Shuffle")
            self.btn_rename.setText("Rename")
            self.btn_cancel.setText("Cancel")
            self.grp_instructions.setTitle("Instructions:")
            self.lbl_instructions.setText(
                "1. Select a folder with MP3 files\n"
                "2. Set the renaming pattern\n"
                "3. Shuffle the files\n"
                "4. Rename with new order\n\n"
                "Tips:\n"
                "- Use {index} for sequential number\n"
                "- Use {name} for original name\n"
                "- Check option for automatic prefix"
            )
            self.grp_preview.setTitle("Preview")
            self.lbl_preview.setText("Original name -> New name")
            self.btn_lang_pt.setStyleSheet("")
            self.btn_lang_en.setStyleSheet("background-color: #16a085;")
            
    def show_message(self, title, message, icon):
        """Show a message box"""
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.setIcon(icon)
        msg.exec()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = ShuffleTune()
    window.show()
    sys.exit(app.exec())
