import cv2
import numpy as np
import torch

from .image_processing_utils import grayscale, canny, gaussian_blur, region_of_interest, draw_fit_line, hough_lines, weighted_img, get_fitline

def process_video(cap):
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True).to(device)
    model.eval()

    frame_size = (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
    print('frame_size =', frame_size)
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    while True:
        retval, frame = cap.read()
        if not retval:
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
            preds = model(image)
            preds = preds.pandas().xyxy[0]
            for index, row in preds.iterrows():
                if row['confidence'] > 0.4:
                    x1, y1, x2, y2 = int(row['xmin']), int(row['ymin']), int(row['xmax']), int(row['ymax'])
                    cv2.rectangle(result, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(result, f'car {row["confidence"]:.2f}', (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            image = cv2.resize(result, None, fx=0.3, fy=0.3, interpolation=cv2.INTER_AREA)
            cv2.imwrite("Open_CV_data\\RGB_IMG.jpg", cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        except:
            continue
    cap.release()
    cv2.destroyAllWindows()