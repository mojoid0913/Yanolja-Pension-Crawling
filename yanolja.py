import time
import pandas as pd
from selenium import webdriver
from urllib.request import urlopen, urlretrieve
from urllib import parse as urlps
from urllib.request import Request
from urllib.error import HTTPError
import json
import os

driver = webdriver.Chrome(executable_path='chromedriver.exe')
driver.implicitly_wait(3)


# naver api
api_url = 'https://naveropenapi.apigw.ntruss.com/map-geocode/v2/geocode?query='
client_id = '59etfe59sm'
client_pw = 'tZVabt5zcB1zx29HNlc9hJMfNxyTrRrUK3FbOYgV'



# 저장소
regionDict = {
    '강원 전체' : 'r-900592',
    '경기 전체' : 'r-900591',
    '인천 전체' : 'r-900594',
    '경남 전체' : 'r-910224',
    '경북 전체' : 'r-900598',
    '전남 전체' : 'r-900599',
    '전북 전체' : 'r-900600',
    '제주 전체' : 'r-900593',
    '충남 전체' : 'r-900595',
    '충북 전체' : 'r-900596',
    '부산 전체' : 'r-900272',
    '울산 전체' : 'r-900575',
    '서울 전체' : 'r-900270'
}





# 지역별 크롤링
for key in regionDict.keys():
    url = "https://www.yanolja.com/pension/"+regionDict[key]

    try:
        os.mkdir('./result/'+key)
    except:
        pass
    df = pd.DataFrame(columns = ['pension_name', 'address', 'phone',  'email', 'zzim_count', 'discount', 'owner', 'coordx', 'coordy'])
    

    driver.get(url)

    SCROLL_PAUSE_TIME = 2
    LOAD_PAUSE_TIME = 2

    # 무한 스크롤
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(SCROLL_PAUSE_TIME)
            new_height = driver.execute_script("return document.body.scrollHeight")
            
            if last_height == new_height:
                time.sleep(SCROLL_PAUSE_TIME)
                break
            last_height = new_height
    
    # 펜션별 주소 받아와 저장
    pensionList = driver.find_elements_by_tag_name('.PlaceListBody_placeListBodyContainer__1u70R .PlaceListBody_placeListBodyGroup__1oN5N div div a')
    pensionLinks = []
    for pension in pensionList: 
        link = pension.get_attribute('href')
        pensionLinks.append(link)

    #펜션 주소에 들어가 상세정보 크롤
    for link in pensionLinks:
        driver.get(link)
        try:
            os.mkdir('./result/'+key+'/img')
        except:
            pass


        #펜션 이름
        try:
            pension_name = driver.find_element_by_class_name('PlaceDetailTitle_title__9jpRM').text
        except:
            pension_name = "UNDEFINED"


        #펜션 이름으로 폴더 생성 후 이미지 크롤
        try: # 이미지 폴더 (최상)
            os.mkdir('./result/'+key+'/img/'+pension_name)
        except:
            pass
        try: # 메인이미지 폴더
            os.mkdir('./result/'+key+'/img/'+pension_name+'/main_img')
        except:
            pass
        try: #서브이미지 폴더
            os.mkdir('./result/'+key+'/img/'+pension_name+'/sub_img')
        except:
            pass

        # 메인이미지 다운
        mainImgList = driver.find_elements_by_css_selector('.swiper-wrapper .swiper-slide .PlaceDetailImageHeader_image__3dt_0')
        img_cnt = 0
        for img in mainImgList:
            style = img.get_attribute('style')
            img_url = style.split('"')[1]
            urlretrieve(img_url, f'./result/{key}/img/{pension_name}/main_img/{img_cnt}.jpg')
            img_cnt+=1
            if img_cnt >= 10:
                break


        # 서브이미지 다운
        roomList = driver.find_elements_by_class_name('RoomItem_roomItemContainerStyle__3XjIR')
        room_cnt = 0
        for room in roomList:
            style = room.find_element_by_class_name('RoomItem_imageStyle__2RzAl').get_attribute('style')
            img_url = style.split('"')[1]
            urlretrieve(img_url, f'./result/{key}/img/{pension_name}/sub_img/{room_cnt}.jpg')
            room_cnt+=1



        #펜션 주소
        try:
            pension_addr = driver.find_element_by_class_name('LocationMap_addressDetail__2u0NF').text
        except:
            pension_addr = "UNDEFINED"

        #위도, 경도 가져오기
        add_urlenc = urlps.quote(pension_addr)
        url = api_url + add_urlenc
        request = Request(url)
        request.add_header('X-NCP-APIGW-API-KEY-ID', client_id)
        request.add_header('X-NCP-APIGW-API-KEY', client_pw)
        
        try:
            response = urlopen(request)
        except HTTPError as e:
            print('HTTP Error!')
            latitude = None
            longitude = None
        else:
            rescode = response.getcode()
            if rescode == 200:
                response_body = response.read().decode('utf-8')
                response_body = json.loads(response_body)   # json
                if response_body['addresses'] == [] :
                    print("'result' not exist!")
                    latitude = None
                    longitude = None
                else:
                    latitude = response_body['addresses'][0]['y']
                    longitude = response_body['addresses'][0]['x']
                    print("Success!")
            else:
                print('Response error code : %d' % rescode)
                latitude = None
                longitude = None


        #판매자 정보 들어가기
        driver.execute_script("arguments[0].click();",   driver.find_element_by_class_name('_place_no__vendorButton__1axHb'))
        titleList = driver.find_elements_by_class_name('VendorContentItem_container__2tFn6')

        #소유주, 전번, email
        pension_rep = []
        pension_cll = []
        pension_eml = []
        for title in titleList:
            if "대표자명" in title.find_element_by_class_name('VendorContentItem_label__2FjG0').text:
                try:
                    pension_rep.append(title.find_element_by_class_name('VendorContentItem_content__zy3FX').text)
                except:
                    pension_rep.append(" ")
            if "연락처" in title.find_element_by_class_name('VendorContentItem_label__2FjG0').text:
                try:
                    pension_rep.append(title.find_element_by_class_name('VendorContentItem_content__zy3FX').text)
                except:
                    pension_cll.append(" ")
            if "전자우편주소" in title.find_element_by_class_name('VendorContentItem_label__2FjG0').text:
                try:
                    pension_rep.append(title.find_element_by_class_name('VendorContentItem_content__zy3FX').text)
                except:
                    pension_eml.append(" ")

        # df에 추가될 내용
        new_data = {
            'pension_name': pension_name ,
            'address' : pension_addr,
            'phone' : ', '.join(pension_cll),
            'email' : ', '.join(pension_eml),
            'zzim_count' : '0',
            'discount' : '0',
            'owner' : ', '.join(pension_rep),
            'coordx' : latitude,
            'coordy' : longitude
        }

        df = df.append(new_data, ignore_index=True)
    
    df.to_excel('./result/'+key+'/result.xlsx')
