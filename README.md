웹 애플리케이션 아키텍처 개요

1. 프론트엔드
HTML/CSS/JavaScript: 사용자 인터페이스 구성
Bootstrap: 반응형 디자인을 위한 CSS 프레임워크
JQuery: DOM 조작 및 AJAX 요청을 간소화

2. 백엔드
Django: 웹 애플리케이션 프레임워크
Django Templates: 서버 사이드 렌더링을 위한 템플릿 시스템
Django Static Files: CSS, JavaScript, 이미지 등 정적 파일 관리

3. CSS 구조
index.css: 전체 사이트의 기본 스타일 설정
myapi.css: API 관리 페이지 특화 스타일
process_video.css: 비디오 처리 페이지 스타일
weather.css: 날씨 정보 페이지 스타일

4. 주요 기능 및 페이지
로그인 및 사용자 인증: Google, GitHub을 통한 소셜 로그인 지원
API 관리: API 키 생성, 복사 및 재생성 기능
API 테스트 인터페이스: 날씨 API, 비디오 처리 API 등을 테스트할 수 있는 인터페이스 제공
프로필 관리: 사용자 프로필 페이지 및 로그아웃 기능

5. 인터랙션 및 동적 기능
AJAX 요청: API 키 관리 및 API 테스트 요청
DOM 조작: 사용자 인터페이스 동적 변경
이벤트 리스너: 사용자 입력 및 상호작용 처리

6. API LIST
    '/api/v1/weather/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-API-KEY': 'your_api_key_here',
            'X-IP-ADDRESS': 'ip_address_here'
        }
    }

    '/api/v1/car_recognition/image/', {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'X-API-KEY': 'your_api_key_here',
            'X-BASE64-INCODE-IMAGE': 'base64_incode_image_here'
        }
    }

    '/api/v1/car_recognition/youtube/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-API-KEY': 'your_api_key_here',
            'X-YOUTUBE-LINK': 'youtube_link_here',
            'X-YOUTUBE-STARTTIME-SECONDS': 'youtube_starttime_here',
            'X-YOUTUBE-ENDTIME-SECONDS': 'youtube_endtime_here'
        }
    }
