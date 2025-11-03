#!/usr/bin/env python3
"""
Test the upload dialog functionality
"""
import sys
from PyQt5.QtWidgets import QApplication
from ui.upload_dialog import UploadDialog

def main():
    app = QApplication(sys.argv)
    
    dialog = UploadDialog()
    dialog.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()