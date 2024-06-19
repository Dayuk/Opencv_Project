import cv2
import numpy as np
import os
import uuid
from .settings import MODEL, STATICFILES_DIRS

def process_image(image, username):
    # 이미지를 모델에 맞는 형태로 변환
    img = np.array(image)
    results = MODEL(img)

    # 결과 추출 및 이미지에 바운딩 박스 그리기
    for *xyxy, conf, cls in results.xyxy[0]:
        if conf > 0.4:
            label = MODEL.names[int(cls)]
            cv2.rectangle(img, (int(xyxy[0]), int(xyxy[1])), (int(xyxy[2]), int(xyxy[3])), (0, 255, 0), 2)
            cv2.putText(img, f'{label} {conf:.2f}', (int(xyxy[0]), int(xyxy[1])-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    # 사용자별 디렉토리 생성
    output_dir = f'{STATICFILES_DIRS}/tmp/{username}'
    os.makedirs(output_dir, exist_ok=True)

    # 랜덤 파일명 생성
    filename = f'{uuid.uuid4()}.png'
    output_image_path = os.path.join(output_dir, filename)

    # 이미지를 PNG로 저장
    cv2.imwrite(output_image_path, img)

    return output_image_path
