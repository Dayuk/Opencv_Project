import cv2
import numpy as np

def grayscale(img):
    return cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

def canny(img, low_threshold, high_threshold):
    return cv2.Canny(img, low_threshold, high_threshold)

def gaussian_blur(img, kernel_size):
    return cv2.GaussianBlur(img, (kernel_size, kernel_size), 0)

def hough_lines(img, rho, theta, threshold, min_line_len, max_line_gap):
    lines = cv2.HoughLinesP(img, rho, theta, threshold, np.array([]), minLineLength=min_line_len, maxLineGap=max_line_gap)
    return lines

def region_of_interest(img, vertices, color3=(255, 255, 255), color1=255):
    mask = np.zeros_like(img)
    if len(img.shape) > 2:
        color = color3
    else:
        color = color1
    cv2.fillPoly(mask, vertices, color)
    return cv2.bitwise_and(img, mask)

def draw_lines(img, lines, color=[255, 0, 0], thickness=2):
    for line in lines:
        for x1, y1, x2, y2 in line:
            cv2.line(img, (x1, y1), (x2, y2), color, thickness)

def draw_fit_line(img, lines, color=[59, 141, 255], thickness=13):
    cv2.fillPoly(img, [lines], color)
    cv2.polylines(img, [lines], True, [0, 74, 177], thickness)

def weighted_img(img, initial_img, α=1, β=1., λ=0.):
    return cv2.addWeighted(initial_img, α, img, β, λ)

def get_fitline(img, lines):
    if lines is None or len(lines) == 0:
        raise ValueError("No lines to process for fitLine.")
    
    # lines 배열이 예상한 형태인지 확인하고, 필요하면 재구성
    if lines.ndim == 2 and lines.shape[1] == 4:
        lines = lines.reshape(lines.shape[0] * 2, 2)
    elif lines.ndim != 2 or lines.shape[1] != 2:
        raise ValueError("Lines array has an unexpected shape.")

    # cv2.fitLine 호출 전에 데이터 검증
    if lines.size > 0:
        output = cv2.fitLine(lines, cv2.DIST_L2, 0, 0.01, 0.01)
        return output
    else:
        raise ValueError("No valid data in lines array for fitLine.")

def cars_find(image, cars):
    for (x, y, w, h) in cars:
        cv2.rectangle(image, (x, y), (x+w, y+h), (0, 255, 0), 2)

def color_filter(image):
    # 흰색과 노란색 마스크 생성
    white_mask = cv2.inRange(image, (200, 200, 200), (255, 255, 255))
    yellow_mask = cv2.inRange(image, (190, 190, 0), (255, 255, 255))
    full_mask = cv2.bitwise_or(white_mask, yellow_mask)
    filtered_image = cv2.bitwise_and(image, image, mask=full_mask)
    return filtered_image

def dynamic_roi(shape, expand=False, more=False):
    height, width = shape[:2]
    if expand:
        increment = 50  # 확장할 픽셀 수
        if more:
            increment = 100  # 더 확장할 경우 픽셀 수
        return np.array([[(0, height + increment), (width / 2, height / 2 + 100 - increment), (width / 2, height / 2 + 100 - increment), (width, height + increment)]], dtype=np.int32)
    else:
        return np.array([[(0, height), (width / 2, height / 2 + 100), (width / 2, height / 2 + 100), (width, height)]], dtype=np.int32)
def dynamic_canny(image):
    sigma = 0.33
    v = np.median(image)
    lower = int(max(0, (1.0 - sigma) * v))
    upper = int(min(255, (1.0 + sigma) * v))
    return cv2.Canny(image, lower, upper)

def dynamic_hough(image):
    return cv2.HoughLinesP(image, 1, np.pi / 180, threshold=50, minLineLength=40, maxLineGap=200)

def expand_roi(vertices, increment=50):
    # ROI를 확장합니다. increment는 확장할 픽셀 수입니다.
    vertices[:, :, 1] -= increment  # y 좌표를 감소시켜 영역을 확장
    return vertices