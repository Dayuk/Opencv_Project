import sys
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QMovie
import requests
from datetime import datetime
import xmltodict
import pandas as pd
import json
import config

#.py file import
from styles import StyleButton, StyleLabel
from OpenCVMRunning import OpenCVMRunning
from weather_thread import WeatherThread

class LoadingFrame(QFrame):
    def __init__(self, my_app, parent=None):
        super().__init__(parent)
        self.my_app = my_app
        self.initUI()

    def initUI(self):
        self.Loading_Label = QLabel(self)
        self.movie = QMovie("Loading.gif")
        self.movie.setScaledSize(QSize().scaled(100, 100, Qt.KeepAspectRatio))
        self.Loading_Label.setMovie(self.movie)
        self.movie.start()

        layout = QHBoxLayout()
        layout.addStretch(1)
        layout.addWidget(self.Loading_Label)
        layout.addStretch(1)
        self.setLayout(layout)

class WeatherFrame(QFrame):
    def __init__(self, my_app, parent=None):
        super().__init__(parent)
        self.my_app = my_app
        self.initUI()

    def initUI(self):
        self.setupLabels()
        self.setupLineEdit()
        self.setupButton()
        self.setupLayouts()

    def setupLabels(self):
        self.Weather_Adress = StyleLabel(text=" ", font_size=15, alignment=Qt.AlignCenter)
        self.Weather_sky = StyleLabel(text=" ", font_size=15, alignment=Qt.AlignCenter)
        self.Weather_Hum = StyleLabel(text=" ", alignment=Qt.AlignCenter)
        self.Date_Label = StyleLabel(text=QDate.currentDate().toString(Qt.DefaultLocaleLongDate), alignment=Qt.AlignCenter, font_size=13)
        self.CV_Img_Label = QLabel(self, alignment=Qt.AlignCenter)

    def setupLineEdit(self):
        self.Line_Edit_Auto_Adress = QLineEdit(placeholderText="다른 곳의 날씨도 검색해 보세요!", alignment=Qt.AlignCenter)
        self.Line_Edit_Auto_Adress.setStyleSheet("color:white; font-size:11px;")
        self.setupCompleter()

    def setupCompleter(self):
        string_list = self.my_app.load_string_list_from_file()
        self.Completer_model = QStringListModel()
        self.Completer_model.setStringList(string_list)

        completer = QCompleter()
        completer.setModel(self.Completer_model)
        completer.popup().setStyleSheet(
            """
            color: white;
            background-color: #2b2b2b;
            font-size: 11px;
            border: 2px solid #4d4d4d;
            """
        )
        self.Line_Edit_Auto_Adress.setCompleter(completer)

    def setupButton(self):
        self.Weather_Update_Button = StyleButton(text="⏎", clicked=lambda: self.my_app.get_Weather(update=True))

    def setupLayouts(self):
        layout = QVBoxLayout(self, spacing=10)
        layout.addWidget(self.Date_Label)
        layout.addWidget(self.Weather_Adress)
        layout.addWidget(self.CV_Img_Label)
        layout.addWidget(self.Weather_sky)
        layout.addWidget(self.Weather_Hum)

        # 위젯을 별도로 추가
        weather_update_box = QHBoxLayout()
        weather_update_box.addWidget(self.Line_Edit_Auto_Adress)
        weather_update_box.addWidget(self.Weather_Update_Button)
        layout.addLayout(weather_update_box)

        self.setLayout(layout)
        self.setStyleSheet("background:#222222; border-radius: 10px;")

class OpenCVFrame(QFrame):
    def __init__(self, my_app, parent=None):
        super().__init__(parent)
        self.my_app = my_app
        self.initUI()

    def initUI(self):
        self.CV_Img_Label = QLabel(self)
        self.CV_Img_Label.setAlignment(Qt.AlignCenter)

        layout = QVBoxLayout()
        layout.addWidget(self.CV_Img_Label)
        self.setLayout(layout)

class ControlButtons(QFrame):
    def __init__(self, my_app, parent=None):
        super().__init__(parent)
        self.my_app = my_app
        self.initUI()

    def initUI(self):
        self.Exit_button = StyleButton(text="×", clicked=self.my_app.Exit_button_click)
        self.Minimize_button = StyleButton(text="─", clicked=self.my_app.Minimize_button_click)
        self.Main_Back_button = StyleButton(text="◀", clicked=self.my_app.Main_Back_button_clicked)

        layout = QHBoxLayout()
        layout.addWidget(self.Main_Back_button)
        layout.addStretch(1)
        layout.addWidget(self.Minimize_button)
        layout.addWidget(self.Exit_button)
        self.setLayout(layout)
        self.setMaximumHeight(40)  # 프레임의 최대 높이 설정

class MyApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setupUI()
        self.open_cv_thread = OpenCVMRunning(self)

    def setupUI(self):
        self.setupWindow()
        self.setupFrames()
        self.setupLayouts()
        self.finalizeSetup()
        self.hide_unused_frames([self.Main_Frame, self.Control_Frame])

    def setupWindow(self):
        self.round_widget = QWidget(self)
        self.round_widget.resize(300, 500)
        self.round_widget.setStyleSheet("background:#2b2b2b; border-radius: 10px;")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setWindowTitle('Portfolio_1')
        self.setAttribute(Qt.WA_TranslucentBackground)

    def setupFrames(self):
        self.Loading_Frame = LoadingFrame(self)
        self.Weather_Frame = WeatherFrame(self)
        self.Open_CV_Frame = OpenCVFrame(self)
        self.Control_Frame = ControlButtons(self)
        self.Main_Frame = QFrame()

        layout = QVBoxLayout()
        self.Weather_Butten = StyleButton(text="날씨 확인", font_size=15, clicked=self.get_Weather)
        self.Open_CV_Button = StyleButton(text="차선 및 차량인식", font_size=15, clicked=self.Open_CV_MP4)
        layout.addWidget(self.Weather_Butten)
        layout.addWidget(self.Open_CV_Button)
        self.Main_Frame.setLayout(layout)

    def setupLayouts(self):
        self.Main_Window_Layout = QVBoxLayout()
        self.Main_Window_Layout.addWidget(self.Control_Frame)
        self.Main_Window_Layout.addWidget(self.Main_Frame)
        self.Main_Window_Layout.addWidget(self.Loading_Frame)
        self.Main_Window_Layout.addWidget(self.Weather_Frame)
        self.Main_Window_Layout.addWidget(self.Open_CV_Frame)

    def finalizeSetup(self):
        self.round_widget.setLayout(self.Main_Window_Layout)
        self.show()

    def load_string_list_from_file(self):
        with open('string_list_1.ini', 'r', encoding='utf-8') as file:
            data = file.read()
            # 줄바꿈으로 문자열을 분리
            string_list = data.strip().split(',')
            # 리스트의 각 요소에서 불필요한 공백과 따옴표 제거
            string_list = [item.strip(" '[]") for item in string_list]
        return string_list

    def hide_unused_frames(self, frames_to_show):
        try:
            all_frames = [self.Main_Frame, self.Loading_Frame, self.Weather_Frame, self.Open_CV_Frame]
            for frame in all_frames:
                if frame not in frames_to_show:
                    frame.hide()
                else:
                    frame.show()
        except Exception as e:
            print("hide_unused_frames Error:"+ str(e))
            pass

    def Open_CV_MP4(self):
        self.open_cv_thread.start()
        self.open_cv_thread.is_running = True
        self.hide_unused_frames([self.Loading_Frame])

    def get_Weather(self, update=False):
        self.hide_unused_frames([self.Loading_Frame])
        self.weather_thread = WeatherThread(self, update=update)  # update 인자를 여기에 추가
        self.weather_thread.weather_updated.connect(self.get_Weather_End)
        self.weather_thread.start()

    def get_Weather_End(self, Weather):
        self.hide_unused_frames([self.Weather_Frame])
        if Weather == "None":
            self.Weather_Frame.Weather_Adress.setText(" ")
            self.Weather_Frame.Weather_sky.setText(" ")
            self.Weather_Frame.Weather_Hum.setText(" ")
            self.Weather_Frame.Line_Edit_Auto_Adress.setText("해당 지역을 찾을 수 없습니다.")
        else:
            self.Weather = str(Weather)
            self.Weather = self.Weather.split(" ")
            self.Weather_Frame.Weather_Adress.setText(self.Weather[0])
            self.Weather_Frame.Weather_sky.setText(self.Weather[1] + " " +self.Weather[2])
            self.Weather_Frame.Weather_Hum.setText("습도 "+self.Weather[3])
            pixmap = QPixmap("Weather_IMG\\"+str(self.Weather[1])+".PNG")
            self.Weather_Frame.CV_Img_Label.setPixmap(pixmap)

    def Main_Back_button_clicked(self):
        self.hide_unused_frames([self.Main_Frame])
        if self.open_cv_thread.isRunning():
            self.open_cv_thread.stop()  # 스레드 종료 요청

    def Minimize_button_click(self):
        self.showMinimized()

    def Exit_button_click(self):
        sys.exit(app.exec_())

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.m_flag = True
            self.m_Position = event.globalPos() - self.pos()  # Get the position of the mouse relative to the window
            event.accept()
            self.setCursor(QCursor(Qt.OpenHandCursor))  # Change mouse icon

    def mouseMoveEvent(self, QMouseEvent):
        if Qt.LeftButton and self.m_flag:
            self.move(QMouseEvent.globalPos() - self.m_Position)  # Change window position
            QMouseEvent.accept()

    def mouseReleaseEvent(self, QMouseEvent):
        self.m_flag = False
        self.setCursor(QCursor(Qt.ArrowCursor))

if __name__ == '__main__':
   app = QApplication(sys.argv)
   ex = MyApp()
   sys.exit(app.exec_())