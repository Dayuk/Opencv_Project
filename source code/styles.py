from PyQt5.QtWidgets import QPushButton, QLineEdit, QLabel, QTableWidget, QComboBox, QTableWidgetItem, QMessageBox, QCompleter, QTabWidget, QDateEdit
from PyQt5.QtGui import QFont, QFontDatabase
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QStringListModel, Qt

class FontManager:
    def __init__(self, font_file="NotoSansKR-Medium.ttf", font_size=12):
        self.font_file = font_file
        self.font_size = font_size
        self.font_id = QFontDatabase.addApplicationFont(self.font_file)
        self.font_family = QFontDatabase.applicationFontFamilies(self.font_id)[0]

    def get_font(self):
        return QFont(self.font_family, self.font_size)


class StyleButton(QPushButton):
    def __init__(self, text, font_size=11, clicked=None, parent=None):
        super(StyleButton, self).__init__(text, parent)
        self.font_size = font_size  # font_size를 인스턴스 변수로 저장
        if clicked:
            self.clicked.connect(clicked)
        self.init_ui()

    def init_ui(self):
        font_manager = FontManager(font_size=self.font_size)  # 인스턴스 변수 사용
        self.setFont(font_manager.get_font())
        self.setStyleSheet(self.get_style())

    @staticmethod
    def get_style():
        return """
        QPushButton {
            font: bold;
            color: #ffffff;
            background-color: #2b2b2b;
            border: 2px solid #ffffff;
            border-radius: 5px;
        }
        QPushButton:hover {
            background-color: #ffffff;
            color: #222222;
        }
        """

class StyleLabel(QLabel):
    def __init__(self, text, parent=None, placeholderText=None, echoMode=None, alignment=None, font_size=11):
        super(StyleLabel, self).__init__(text, parent)
        self.font_size = font_size  # font_size를 인스턴스 변수로 저장
        if alignment:
            self.setAlignment(alignment)  # alignment 설정
        self.init_ui()

    def init_ui(self):
        font_manager = FontManager(font_size=self.font_size)  # 인스턴스 변수 사용
        self.setFont(font_manager.get_font())
        self.setStyleSheet(self.get_style())

    @staticmethod
    def get_style():
        return """
        color:white;
        """