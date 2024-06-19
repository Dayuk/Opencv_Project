import yt_dlp
import uuid
import os
from .settings import STATICFILES_DIRS, MODEL
import asyncio
import logging
import imageio
import cv2

logger = logging.getLogger(__name__)

def download_and_process_video(youtube_url, start_time, end_time, username):
    # 시작 시간과 끝나는 시간을 초 단위로 계산
    if start_time == 0 and end_time == 0:
        duration = 180  # start_time과 end_time이 0일 경우, 180초로 제한
    else:
        duration = end_time - start_time
    try:
        # 랜덤 파일 이름 생성
        random_filename = f"{uuid.uuid4()}.mp4"
        # 사용자별 폴더 경로 설정
        output_directory = f"{STATICFILES_DIRS}/tmp/{username}/{random_filename}"
        # 폴더가 없으면 생성
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)
        # 최종 파일 경로
        output_path = os.path.join(output_directory, random_filename)

        ydl_opts = {
            'format': 'bestvideo[height<=720]+bestaudio/best[height<=720]',  # 720p 이하의 최고 화질 비디오
            'outtmpl': output_path,  # 저장될 파일 이름
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',  # 비디오 포맷을 mp4로 설정
            }],
            'external_downloader_args': {
                'ffmpeg': ['-ss', str(start_time), '-t', str(duration)]  # 시작 시간과 지속 시간 설정
            },
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([youtube_url])

        run_process_video_frames(output_directory, random_filename)
    except Exception as e:
        return e

def run_process_video_frames(path, filename):
    new_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(new_loop)
    try:
        new_loop.run_until_complete(process_video_frames(path, filename))
    finally:
        new_loop.close()

async def process_video_frames(user_dir, filename):
    try:
        logger.debug(f"Processing video frames for {filename} in directory {user_dir}")

        reader = imageio.get_reader(f'{user_dir}/{filename}')
        fps = reader.get_meta_data()['fps']
        writer = imageio.get_writer(f'{user_dir}/{filename}_output.mp4', fps=fps)

        for i, frame in enumerate(reader):
            try:
                preds = MODEL(frame)
                preds = preds.pandas().xyxy[0]
                print(preds)
                for index, row in preds.iterrows():
                    if row['confidence'] > 0.4:
                        x1, y1, x2, y2 = int(row['xmin']), int(row['ymin']), int(row['xmax']), int(row['ymax'])
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        cv2.putText(frame, f'car {row["confidence"]:.2f}', (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                writer.append_data(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))  # 최종 결과를 RGB로 변환하여 writer에 저장
            except Exception as e:
                logger.error(f"Error processing video {filename}: {e}", exc_info=True)
                continue
    finally:    
        writer.close()
        reader.close()
        output_file_path = f'{user_dir}/{filename}_output.mp4'
        return output_file_path