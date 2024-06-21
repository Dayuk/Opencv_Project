import pandas as pd
import datetime
import xmltodict
import requests
import json
import os
import logging

from django.conf import settings
from .translations import WEATHER_STATUS_TRANSLATIONS

def get_weather_data(address):
    try:
        current_date = datetime.datetime.now().date()
        current_date = current_date.strftime("%Y%m%d")

        now = datetime.datetime.now()
        if now.minute < 45:
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

        current_hour = base_time

        send_url = 'http://api.ipstack.com/' + address + '?access_key=' + settings.IPSTACK_KEY
        r = requests.get(send_url)
        j = json.loads(r.text)
        region_name = j.get("region_name")

        if region_name:
            region_translations = {
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
            if region_name in region_translations:
                address = region_translations.get(region_name, region_name)  # Default to original if not found in dict
                file = os.path.join(settings.BASE_DIR, "static", "data", "nx_ny.csv")
                df = pd.read_excel(file, engine="openpyxl", usecols=["1단계", "2단계", "3단계", "격자 X", "격자 Y"])
                address_value = df.loc[(df["1단계"] == address) | (df["2단계"] == address) | (df["3단계"] == address)]
                nx_ny = address_value[["격자 X", "격자 Y"]]
                nx_ny = nx_ny.values.tolist()
                nx_ny = nx_ny[0]

                url = 'http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtFcst'
                params = {'serviceKey': settings.WEATHER_API_KEY,
                        'pageNo': '1',
                        'numOfRows': '1000',
                        'dataType': 'XML',
                        'base_date': current_date,
                        'base_time': current_hour,
                        'nx': nx_ny[0],
                        'ny': nx_ny[1]}

                res = requests.get(url, params=params)
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
                
                weather_status = ""
                if weather_data['sky2'] == '0':
                    if weather_data['sky'] == '1':
                        weather_status = "맑음"
                    elif weather_data['sky'] == '3':
                        weather_status = "구름많음"
                    elif weather_data['sky'] == '4':
                        weather_status = "흐림"
                elif weather_data['sky2'] == '1':
                    weather_status = "비"
                elif weather_data['sky2'] == '2':
                    weather_status = "비와 눈"
                elif weather_data['sky2'] == '3':
                    weather_status = "눈"
                elif weather_data['sky2'] == '5':
                    weather_status = "빗방울이 떨어짐"
                elif weather_data['sky2'] == '6':
                    weather_status = "빗방울과 눈"
                elif weather_data['sky2'] == '7':
                    weather_status = "눈이 날림"

                return {
                    'date': current_date,
                    'location': address,
                    'status': weather_status,
                    'icon' : os.path.join(settings.BASE_DIR, "static", "weather_image", weather_status + ".png"),
                    'temperature': weather_data['tmp'],
                    'humidity': weather_data['hum']
                }
            else:
                # Use WeatherAPI as a fallback
                weather_api_key = settings.WEATHER_API_KEY2
                weather_url = f'http://api.weatherapi.com/v1/current.json?key={weather_api_key}&q={region_name}'
                weather_response = requests.get(weather_url)
                weather_data = json.loads(weather_response.text)

                address = weather_data['location']['region']

                weather_date = weather_data['location']['localtime'].split(' ')[0]
                weather_location = f"{weather_data['location']['name']}, {weather_data['location']['region']}, {weather_data['location']['country']}"
                weather_icon = weather_data['current']['condition']['icon']
                weather_status = weather_data['current']['condition']['text']
                temperature = weather_data['current']['temp_c']
                humidity = weather_data['current']['humidity']

                icon_url = "https:" + weather_icon
                weather_status = WEATHER_STATUS_TRANSLATIONS.get(weather_status, "상태 미확인")

                return {
                    'date': weather_date,
                    'location': weather_location,
                    'icon': icon_url,
                    'status': weather_status,
                    'temperature': temperature,
                    'humidity': humidity
                }

    except requests.exceptions.RequestException as e:
        logging.error(f"Request error: {e}")
        return None
    except json.JSONDecodeError as e:
        logging.error(f"JSON Decode error: {e}")
        return None
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return None
