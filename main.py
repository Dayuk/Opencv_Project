import requests
from datetime import datetime
import xmltodict
import pandas as pd
import sys
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QMovie
import json
import warnings
import numpy as np
import cv2
import torch

#.py file import
from image_processing_utils import grayscale, canny, gaussian_blur, region_of_interest, draw_fit_line, hough_lines, weighted_img, get_fitline
from styles import StyleButton, StyleLabel

class OpenCVMRunning(QThread):
    def __init__(self, my_app, parent=None):
        super(OpenCVMRunning, self).__init__(parent)
        self.my_app = my_app
        self.is_running = True  # 스레드 실행 상태를 제어하는 플래그
        self.OpenCVFrame = my_app.Open_CV_Frame  # MyApp 객체에서 OpenCVFrame 인스턴스를 가져와 저장

    def run(self):
        self.save_result = []
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True).to(self.device)
        self.model.eval()
        self.my_app.Loading_Frame.hide()
        warnings.filterwarnings('ignore')

        self.cap = cv2.VideoCapture("Open_CV_data\\opencv_youtube.mp4")

        frame_size = (int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
        print('frame_size =', frame_size)
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        self.my_app.hide_unused_frames([self.OpenCVFrame])
        while True:
            retval, frame = self.cap.read()
            if not retval or not self.is_running:
                break
            try:
                cv2.imwrite("Open_CV_data\\RGB_IMG.jpg", cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                image = cv2.imread('Open_CV_data\\RGB_IMG.jpg')

                height, width = image.shape[:2]  # 이미지 높이, 너비

                gray_img = grayscale(image)  # 흑백이미지로 변환

                blur_img = gaussian_blur(gray_img, 3)  # Blur 효과

                canny_img = canny(blur_img, 70, 210)  # Canny edge 알고리즘

                vertices = np.array([[(0, height),
                                    (width / 2, height / 2 +100),
                                    (width / 2, height / 2 +100),
                                    (width, height)
                                    ]], dtype=np.int32)
            except:
                self.cap.release()
                cv2.destroyAllWindows()
                break
            try:
                ROI_img = region_of_interest(canny_img, vertices)  # ROI 설정

                line_arr = hough_lines(ROI_img, 1, 1 * np.pi / 180, 30, 10, 20)  # 허프 변환
                line_arr = np.squeeze(line_arr)

                # 기울기 구하기
                try:
                    slope_degree = (np.arctan2(line_arr[:, 1] - line_arr[:, 3], line_arr[:, 0] - line_arr[:, 2]) * 180) / np.pi
                except:
                    break

                # 수평 기울기 제한
                line_arr = line_arr[np.abs(slope_degree) < 150]
                slope_degree = slope_degree[np.abs(slope_degree) < 150]
                # 수직 기울기 제한
                line_arr = line_arr[np.abs(slope_degree) > 95]
                slope_degree = slope_degree[np.abs(slope_degree) > 95]
                # 필터링된 직선 버리기
                L_lines, R_lines = line_arr[(slope_degree > 0), :], line_arr[(slope_degree < 0), :]
                temp = np.zeros((image.shape[0], image.shape[1], 3), dtype=np.uint8)
                L_lines, R_lines = L_lines[:, None], R_lines[:, None]
                # 왼쪽, 오른쪽 각각 대표선 구하기
                left_fit_line = get_fitline(image, L_lines)
                right_fit_line = get_fitline(image, R_lines)
                fit_line_xy = np.array([[left_fit_line[0], left_fit_line[1]],
                                        [right_fit_line[0],right_fit_line[1]],
                                        [left_fit_line[2]+15, left_fit_line[3]+15],
                                        [right_fit_line[2]-15,right_fit_line[3]+15]], np.int32)

                # 대표선 그리기
                draw_fit_line(temp, fit_line_xy)
                result = weighted_img(temp, image)  # 원본 이미지에 검출된 선 overlap
            except:
                continue

            ## 자동차 인식 및 추적 ##
            preds = self.model(image)
            preds = preds.pandas().xyxy[0]

            # 자동차 검출 및 추적
            for index, row in preds.iterrows():
                if row['confidence'] > 0.4:
                    x1, y1, x2, y2 = int(row['xmin']), int(row['ymin']), int(row['xmax']), int(row['ymax'])
                    cv2.rectangle(result, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(result, f'car {row["confidence"]:.2f}', (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            image = cv2.resize(result, None, fx=0.3, fy=0.3, interpolation=cv2.INTER_AREA)
            cv2.imwrite("Open_CV_data\\RGB_IMG.jpg", cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            pixmap = QPixmap("Open_CV_data\\RGB_IMG.jpg")
            self.OpenCVFrame.CV_Img_Label.setPixmap(pixmap)
        self.cap.release()
        cv2.destroyAllWindows()

    def stop(self):
        self.is_running = False  # 스레드 종료를 위해 플래그를 False로 설정

class WeatherThread(QThread):
    weather_updated = pyqtSignal(str)  # 날씨 정보를 전달할 시그널

    def __init__(self, my_app, update=False, parent=None):
        super().__init__(parent)
        self.my_app = my_app
        self.update = update

    def run(self):
        try:
            current_date = datetime.now().date()
            self.current_date = current_date.strftime("%Y%m%d")

            now = datetime.now()
            if now.minute < 45:  # base_time와 base_date 구하는 함수
                if now.hour == 0:
                    base_time = "2330"
                else:
                    pre_hour = now.hour - 1
                    if pre_hour < 10:
                        base_time = "0" + str(pre_hour) + "30"
                    else:
                        base_time = str(pre_hour) + "30"
            else:
                if now.hour < 10:
                    base_time = "0" + str(now.hour) + "30"
                else:
                    base_time = str(now.hour) + "30"

            self.current_hour = base_time

            if self.update:
                adress = self.my_app.Weather_Frame.Line_Edit_Auto_Adress.text()
            else:
                key = "83a3388f6fbf7d02001e6ec90ff31562"
                send_url = 'http://api.ipstack.com/check?access_key=' + key
                r = requests.get(send_url)
                j = json.loads(r.text)
                j = j["region_name"]

                dict = {
                    "Seoul": "서울특별시",
                    "Gyeonggi-do": "경기도",
                    "Busan": "부산광역시",
                    "Daegu": "대구광역시",
                    "Incheon": "인천광역시",
                    "Gwangju": "광주광역시",
                    "Daejeon": "대전광역시",
                    "Ulsan": "울산광역시",
                    "Sejong-si": "세종특별자치시",
                    "Chungcheongbuk-do": "충청북도",
                    "Chungcheongnam-do": "충청남도",
                    "Jeollabuk-do": "전라북도",
                    "Jeollanam-do": "전라남도",
                    "Gyeongsangbuk-do": "경상북도",
                    "Gyeongsangnam-do": "경상남도",
                    "Jeju-do": "제주특별자치도",
                    "이어도": "이어도",
                    "Gangwon-do": "강원특별자치도"
                }
                adress = dict[j]
            file = "nx_ny.csv"
            df = pd.read_excel(file, engine="openpyxl")
            adress_value = df.loc[(df["1단계"] == adress) | (df["2단계"] == adress) | (df["3단계"] == adress)]
            nx_ny = adress_value[["격자 X", "격자 Y"]]
            nx_ny = nx_ny.values.tolist()
            self.nx_ny = nx_ny[0]

            keys = 'K/cNvfRxMOAp3FabzorD5fiL8qm17xTCSbi4FMXRMDImLFizFEUvi13VBV/2em83vf1aZgCczE+LCetrTbkhCg=='
            self.url = 'http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtFcst'
            self.params = {'serviceKey': keys,
                        'pageNo': '1',
                        'numOfRows': '1000',
                        'dataType': 'XML',
                        'base_date': self.current_date,
                        'base_time': self.current_hour,
                        'nx': self.nx_ny[0],
                        'ny': self.nx_ny[1]}

            res = requests.get(self.url, params=self.params)
            xml_data = res.text
            dict_data = xmltodict.parse(xml_data)
            weather_data = {}
            for item in dict_data['response']['body']['items']['item']:
                if item['category'] == 'T1H':
                    weather_data['tmp'] = item['fcstValue']
                if item['category'] == 'REH':
                    weather_data['hum'] = item['fcstValue']
                if item['category'] == 'SKY':
                    weather_data['sky'] = item['fcstValue']
                if item['category'] == 'PTY':
                    weather_data['sky2'] = item['fcstValue']
            str_sky = adress
            if weather_data['sky'] != None or weather_data['sky2'] != None:
                str_sky += " "
                if weather_data['sky2'] == '0':
                    if weather_data['sky'] == '1':
                        str_sky += "맑음"
                    elif weather_data['sky'] == '3':
                        str_sky += "구름많음"
                    elif weather_data['sky'] == '4':
                        str_sky += "흐림"
                elif weather_data['sky2'] == '1':
                    str_sky += "비"
                elif weather_data['sky2'] == '2':
                    str_sky += "비와 눈"
                elif weather_data['sky2'] == '3':
                    str_sky += "눈"
                elif weather_data['sky2'] == '5':
                    str_sky += "빗방울이 떨어짐"
                elif weather_data['sky2'] == '6':
                    str_sky += "빗방울과 눈"
                elif weather_data['sky2'] == '7':
                    str_sky += "눈이 날림"
                str_sky += " "
            if weather_data['tmp'] != None:
                str_sky += weather_data['tmp'] + '°C '
            if weather_data['hum'] != None:
                str_sky += weather_data['hum'] + '%'
            self.weather_updated.emit(str_sky)
        except:
            self.weather_updated.emit("None")

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