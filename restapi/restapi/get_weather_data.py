import pandas as pd
import datetime
import xmltodict
import requests
import json

from django.conf import settings

def get_weather_data(adress, update):
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

        if update:
            adress = adress
        else:
            key = settings.IPSTACK_KEY
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
        nx_ny = nx_ny[0]

        keys = settings.WEATHER_API_KEY
        url = 'http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtFcst'
        params = {'serviceKey': keys,
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
            'location': adress,
            'status': weather_status,
            'temperature': weather_data['tmp'],
            'humidity': weather_data['hum']
        }
    except Exception as e:
        print("Error in WeatherThread:", e)
        return None
