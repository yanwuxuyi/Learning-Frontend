from bs4 import BeautifulSoup
from DrissionPage import WebPage
from time import sleep
import json
import time
from datetime import datetime, timedelta
from flask import jsonify

class FlightCrawler:
    def __init__(self):
        self.page = None
        self.max_wait_time = 10
        
    def init_page(self):
        """初始化WebPage"""
        try:
            self.page = WebPage()
            return self.page
        except Exception as e:
            print(f"初始化WebPage失败: {e}")
            return None
    
    def get_city_code(self, city_name):
        """获取城市代码"""
        city_mapping = {
            '北京': 'bjs', '上海': 'sha', '广州': 'can', '深圳': 'szx',
            '杭州': 'hgh', '南京': 'nkg', '成都': 'ctu', '重庆': 'ckg',
            '西安': 'sia', '武汉': 'wuh', '长沙': 'csx', '青岛': 'tao',
            '厦门': 'xmn', '大连': 'dlc', '天津': 'tsn', '沈阳': 'she',
            '哈尔滨': 'hrb', '济南': 'tna', '郑州': 'cgo', '昆明': 'kmg',
            '贵阳': 'kwe', '南宁': 'nng', '海口': 'hak', '三亚': 'syx',
            '福州': 'foc', '南昌': 'khn', '合肥': 'hfe', '太原': 'tyn',
            '石家庄': 'sjw', '呼和浩特': 'het', '兰州': 'lhw', '西宁': 'xnn',
            '银川': 'inc', '乌鲁木齐': 'urc', '拉萨': 'lxa'
        }
        return city_mapping.get(city_name, city_name.lower())
    
    def search_flights(self, departure, arrival, departure_date, return_date=None):
        """搜索机票"""
        try:
            print(f"开始搜索机票: {departure} -> {arrival}, 日期: {departure_date}")
            
            # 初始化页面
            if not self.page:
                self.page = self.init_page()
                if not self.page:
                    return {"success": False, "message": "页面初始化失败"}
            
            # 获取城市代码
            departure_code = self.get_city_code(departure)
            arrival_code = self.get_city_code(arrival)
            
            print(f"城市代码: {departure_code} -> {arrival_code}")
            
            # 构建URL
            url = f'https://flights.ctrip.com/online/list/oneway-{departure_code}-{arrival_code}?depdate={departure_date}&cabin=y_s_c_f&adult=1&child=0&infant=0'
            
            print(f"访问URL: {url}")
            
            # 访问页面
            self.page.get(url)
            sleep(2)
            
            # 点击筛选按钮
            try:
                self.page('#filter_item_other').click()
                sleep(1)
                self.page("@@u_key=filter_toggle_entry@@u_remark=点击筛选项[FILTER_GROUP_OTHER.HIDE_SHARED_FLIGHTS/隐藏共享航班]").click()
            except Exception as e:
                print(f"点击筛选按钮失败: {e}")
            
            # 滚动页面加载更多内容
            for i in range(4):
                sleep(3)
                self.page.scroll.to_bottom()
            
            sleep(1)
            
            # 解析页面内容
            soup = BeautifulSoup(self.page.html, "html.parser")
            flights = self.parse_flight_results(soup)
            
            return {
                "success": True,
                "flights": flights,
                "message": f"找到 {len(flights)} 个航班"
            }
            
        except Exception as e:
            print(f"搜索机票失败: {e}")
            return {
                "success": False,
                "message": f"搜索失败: {str(e)}",
                "flights": []
            }
    
    def parse_flight_results(self, soup):
        """解析航班搜索结果"""
        flights = []
        try:
            # 获取所有航班div
            flight_divs = soup.find_all("div", {"class": "flight-box"})
            print(f"找到 {len(flight_divs)} 个航班div")
            
            # 跳过第一个（通常是标题行）
            for flight_div in flight_divs[1:11]:  # 只取前10个航班
                try:
                    flight_info = self.extract_flight_info(flight_div)
                    if flight_info:
                        flights.append(flight_info)
                except Exception as e:
                    print(f"解析航班信息失败: {e}")
                    continue
                    
        except Exception as e:
            print(f"解析航班结果失败: {e}")
        
        return flights
    
    def extract_flight_info(self, flight_div):
        """提取单个航班信息"""
        try:
            # 获取航空公司名称
            airline_name = self.get_airline_name(flight_div)
            
            # 获取出发信息
            departure_airport = self.get_departure_airport(flight_div)
            departure_time = self.get_departure_time(flight_div)
            
            # 获取到达信息
            arrival_airport = self.get_arrival_airport(flight_div)
            arrival_time = self.get_arrival_time(flight_div)
            
            # 获取航班信息
            flight_information = self.get_flight_information(flight_div)
            
            # 获取价格
            price = self.get_flight_price(flight_div)
            
            return {
                "airline": airline_name,
                "departureAirport": departure_airport,
                "arrivalAirport": arrival_airport,
                "departureTime": departure_time,
                "arrivalTime": arrival_time,
                "flightInformation": flight_information,
                "price": price,
                "cabin": "经济舱"
            }
            
        except Exception as e:
            print(f"提取航班信息失败: {e}")
            return None
    
    def get_airline_name(self, flight_div):
        """获取航空公司名称"""
        try:
            # 尝试获取ariline-name类的div
            airline_divs = flight_div.find_all("div", {"class": "ariline-name"})
            if len(airline_divs) == 2:
                return [airline_divs[0].contents[0], airline_divs[1].contents[0]]
            elif len(airline_divs) == 0:
                # 尝试获取airline-name类的div
                airline_divs = flight_div.find_all("div", {"class": "airline-name"})
                if airline_divs:
                    return airline_divs[0].text
            return "未知航空公司"
        except Exception as e:
            print(f"获取航空公司名称失败: {e}")
            return "未知航空公司"
    
    def get_departure_airport(self, flight_div):
        """获取出发机场"""
        try:
            depart_div = flight_div.find("div", {"class": "depart-box"})
            if depart_div:
                airport_div = depart_div.find("div", {"class": "airport"})
                if airport_div:
                    return airport_div.text.strip()
            return "未知机场"
        except Exception as e:
            print(f"获取出发机场失败: {e}")
            return "未知机场"
    
    def get_departure_time(self, flight_div):
        """获取出发时间"""
        try:
            depart_div = flight_div.find("div", {"class": "depart-box"})
            if depart_div:
                time_div = depart_div.find("div", {"class": "time"})
                if time_div:
                    return time_div.text.strip()
            return "未知时间"
        except Exception as e:
            print(f"获取出发时间失败: {e}")
            return "未知时间"
    
    def get_arrival_airport(self, flight_div):
        """获取到达机场"""
        try:
            arrive_div = flight_div.find("div", {"class": "arrive-box"})
            if arrive_div:
                airport_div = arrive_div.find("div", {"class": "airport"})
                if airport_div:
                    return airport_div.text.strip()
            return "未知机场"
        except Exception as e:
            print(f"获取到达机场失败: {e}")
            return "未知机场"
    
    def get_arrival_time(self, flight_div):
        """获取到达时间"""
        try:
            arrive_div = flight_div.find("div", {"class": "arrive-box"})
            if arrive_div:
                time_div = arrive_div.find("div", {"class": "time"})
                if time_div:
                    return time_div.text.strip()
            return "未知时间"
        except Exception as e:
            print(f"获取到达时间失败: {e}")
            return "未知时间"
    
    def get_flight_information(self, flight_div):
        """获取航班信息"""
        try:
            info_div = flight_div.find("div", {"class": "transfer-info-group"})
            if info_div:
                return info_div.text.strip()
            return "无中转信息"
        except Exception as e:
            print(f"获取航班信息失败: {e}")
            return "无中转信息"
    
    def get_flight_price(self, flight_div):
        """获取航班价格"""
        try:
            price_span = flight_div.find("span", {"class": "price"})
            if price_span:
                price_text = price_span.text.strip()
                # 提取数字部分
                import re
                price_match = re.search(r'\d+', price_text)
                if price_match:
                    return int(price_match.group())
            return 0
        except Exception as e:
            print(f"获取航班价格失败: {e}")
            return 0
    
    def close(self):
        """关闭页面"""
        if self.page:
            try:
                self.page.quit()
            except:
                pass
            self.page = None

# 全局爬虫实例
flight_crawler = None

def get_flight_crawler():
    """获取爬虫实例"""
    global flight_crawler
    if flight_crawler is None:
        flight_crawler = FlightCrawler()
    return flight_crawler

def search_flights_api(departure, arrival, departure_date, return_date=None):
    """机票搜索API"""
    try:
        crawler = get_flight_crawler()
        result = crawler.search_flights(departure, arrival, departure_date, return_date)
        return result
    except Exception as e:
        print(f"机票搜索API错误: {e}")
        return {
            "success": False,
            "message": f"搜索失败: {str(e)}",
            "flights": []
        }

def cleanup_crawler():
    """清理爬虫资源"""
    global flight_crawler
    if flight_crawler:
        flight_crawler.close()
        flight_crawler = None 