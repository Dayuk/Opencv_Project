import youtube_dl

def download_video_from_url(url, output_path):
    ydl_opts = {
        'format': 'bestvideo',
        'outtmpl': output_path,
        'noplaylist': True,
        'quiet': True
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return output_path