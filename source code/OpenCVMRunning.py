import cv2
import numpy as np
import torch
from PyQt5.QtCore import QThread
from PyQt5.QtGui import QPixmap

# 필요한 추가 모듈 임포트
from image_processing_utils import grayscale, canny, gaussian_blur, region_of_interest, draw_fit_line, hough_lines, weighted_img, get_fitline

class OpenCVMRunning(QThread):
    def __init__(self, my_app, parent=None):
        super(OpenCVMRunning, self).__init__(parent)
        self.my_app = my_app
        self._is_running = True  # private 변수로 변경
        self.OpenCVFrame = my_app.Open_CV_Frame

    def run(self):
        self.save_result = []
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True).to(self.device)
        self.model.eval()

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
                height, width = image.shape[:2]
                gray_img = grayscale(image)
                blur_img = gaussian_blur(gray_img, 3)
                canny_img = canny(blur_img, 70, 210)
                vertices = np.array([[(0, height), (width / 2, height / 2 +100), (width / 2, height / 2 +100), (width, height)]], dtype=np.int32)
                ROI_img = region_of_interest(canny_img, vertices)
                line_arr = hough_lines(ROI_img, 1, 1 * np.pi / 180, 30, 10, 20)
                line_arr = np.squeeze(line_arr)
                slope_degree = (np.arctan2(line_arr[:, 1] - line_arr[:, 3], line_arr[:, 0] - line_arr[:, 2]) * 180) / np.pi
                line_arr = line_arr[np.abs(slope_degree) < 150]
                slope_degree = slope_degree[np.abs(slope_degree) < 150]
                line_arr = line_arr[np.abs(slope_degree) > 95]
                slope_degree = slope_degree[np.abs(slope_degree) > 95]
                L_lines, R_lines = line_arr[(slope_degree > 0), :], line_arr[(slope_degree < 0), :]
                temp = np.zeros((image.shape[0], image.shape[1], 3), dtype=np.uint8)
                L_lines, R_lines = L_lines[:, None], R_lines[:, None]
                left_fit_line = get_fitline(image, L_lines)
                right_fit_line = get_fitline(image, R_lines)
                fit_line_xy = np.array([[left_fit_line[0], left_fit_line[1]], [right_fit_line[0],right_fit_line[1]], [left_fit_line[2]+15, left_fit_line[3]+15], [right_fit_line[2]-15,right_fit_line[3]+15]], np.int32)
                draw_fit_line(temp, fit_line_xy)
                result = weighted_img(temp, image)
                preds = self.model(image)
                preds = preds.pandas().xyxy[0]
                for index, row in preds.iterrows():
                    if row['confidence'] > 0.4:
                        x1, y1, x2, y2 = int(row['xmin']), int(row['ymin']), int(row['xmax']), int(row['ymax'])
                        cv2.rectangle(result, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        cv2.putText(result, f'car {row["confidence"]:.2f}', (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                image = cv2.resize(result, None, fx=0.3, fy=0.3, interpolation=cv2.INTER_AREA)
                cv2.imwrite("Open_CV_data\\RGB_IMG.jpg", cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
                pixmap = QPixmap("Open_CV_data\\RGB_IMG.jpg")
                self.OpenCVFrame.CV_Img_Label.setPixmap(pixmap)
            except:
                continue
        self.cap.release()
        cv2.destroyAllWindows()

    def stop(self):
        self._is_running = False  # 외부에서 접근할 수 있는 메서드를 통해 변수 조작

    def is_running(self):
        return self._is_running  # 상태 확인을 위한 메서드