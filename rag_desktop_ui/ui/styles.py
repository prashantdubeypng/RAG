# ui/styles.py

LIGHT = """
QWidget {
    background: #F6F7FB;
    color: #0B2545;
    font-family: 'Segoe UI', 'Inter';
}

#sidebar {
    background: #ffffff;
    border-right: 1px solid #e6e9f0;
}

QPushButton#primary {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, 
        stop:0 #7c3aed, stop:1 #06b6d4);
    color: white;
    border-radius: 12px;
    padding: 10px 16px;
    font-weight: 600;
    border: none;
}

QPushButton#primary:hover {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, 
        stop:0 #8b5cf6, stop:1 #0891b2);
}

QPushButton#ghost {
    background: transparent;
    border: 1px solid #e6e9f0;
    border-radius: 10px;
    padding: 8px 16px;
    color: #374151;
}

QPushButton#ghost:hover {
    background: #f9fafb;
    border-color: #d1d5db;
}

QListWidget {
    background: transparent;
    border: none;
    color: #374151;
}

QListWidget::item {
    padding: 8px 12px;
    border-radius: 6px;
    margin: 2px 0;
}

QListWidget::item:selected {
    background: #e0e7ff;
    color: #3730a3;
}

QListWidget::item:hover {
    background: #f1f5f9;
}

QLineEdit {
    background: #fff;
    border-radius: 12px;
    padding: 12px 16px;
    border: 1px solid #e6e9f0;
    color: #374151;
    font-size: 14px;
}

QLineEdit:focus {
    border-color: #7c3aed;
    background: #fefefe;
}

QScrollArea {
    background: transparent;
    border: none;
}

QFrame {
    background: transparent;
}

#centerTitle {
    font-size: 48px;
    font-weight: 700;
    color: #9AA6B2;
}

#topBar {
    background-color: rgba(255, 255, 255, 0.05);
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}
"""

DARK = """
QWidget {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1, 
        stop:0 #0f1724, stop:1 #0b1220);
    color: #E6EEF8;
    font-family: 'Segoe UI', 'Inter';
}

#sidebar {
    background: #0E1117;
    border-right: 1px solid rgba(255,255,255,0.08);
}

QPushButton#primary {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, 
        stop:0 #7c3aed, stop:1 #06b6d4);
    color: white;
    border-radius: 12px;
    padding: 10px 16px;
    font-weight: 600;
    border: none;
}

QPushButton#primary:hover {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, 
        stop:0 #8b5cf6, stop:1 #0891b2);
}

QPushButton#ghost {
    background: transparent;
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 10px;
    padding: 8px 16px;
    color: #E6EEF8;
}

QPushButton#ghost:hover {
    background: rgba(255,255,255,0.05);
    border-color: rgba(255,255,255,0.2);
}

QListWidget {
    background: transparent;
    border: none;
    color: #E6EEF8;
}

QListWidget::item {
    padding: 8px 12px;
    border-radius: 6px;
    margin: 2px 0;
}

QListWidget::item:selected {
    background: rgba(124, 58, 237, 0.2);
    color: #a78bfa;
}

QListWidget::item:hover {
    background: rgba(255,255,255,0.05);
}

QLineEdit {
    background: rgba(255,255,255,0.05);
    border-radius: 12px;
    padding: 12px 16px;
    border: 1px solid rgba(255,255,255,0.1);
    color: #E6EEF8;
    font-size: 14px;
}

QLineEdit:focus {
    border-color: #7c3aed;
    background: rgba(255,255,255,0.08);
}

QScrollArea {
    background: transparent;
    border: none;
}

QFrame {
    background: transparent;
}

#centerTitle {
    font-size: 48px;
    font-weight: 700;
    color: rgba(255,255,255,0.95);
}

#topBar {
    background-color: rgba(255, 255, 255, 0.08);
    border-bottom: 1px solid rgba(255, 255, 255, 0.15);
}
"""