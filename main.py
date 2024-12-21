from datetime import datetime
import json
import re
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
import platform
import requests


start_date = datetime.strptime("2024-01-01 00:00:00", "%Y-%m-%d %H:%M:%S")
end_date = datetime.strptime("2024-12-31 23:59:59", "%Y-%m-%d %H:%M:%S")
all_data = {}


if __name__ == "__main__":
    # 读入账户信息
    try:
        with open("config.json", "r", encoding='utf-8') as f:
            account = json.load(f)
            userid = account["userid"]
            access_token = account["access_token"]
    except Exception as e:
        print("账户信息读取失败，请重新输入")
        userid = input("请输入学号: ")
        access_token = input("请输入访问令牌: ")
        with open("config.json", "w", encoding='utf-8') as f:
            json.dump({"userid": userid, "access_token": access_token}, f, indent=4)
    
    # 发送请求，得到总页数
    url = "https://seat.lib.tsinghua.edu.cn/user/index/book/"
    cookie = {
        "userid": userid,
        "access_token": access_token
    }
    response = requests.post(url, cookies=cookie)
    soup = BeautifulSoup(response.text, 'html.parser')

    links = soup.find_all('a')

    max_page = 1
    for link in links:
        if 'class' in link.attrs and 'num' in link['class']:
            max_page = max(max_page, int(link['href'].split('p/')[1]))
        if 'class' in link.attrs and 'end' in link['class']:
            max_page = int(link['href'].split('p/')[1])
            break

    # 发送请求，得到所有数据
    reservations = {}
    for page in range(1, max_page + 1):
        url = f"https://seat.lib.tsinghua.edu.cn/user/index/book/p/{page}"
        cookie = {
            "userid": userid,
            "access_token": access_token
        }
        response = requests.post(url, cookies=cookie)
        soup = BeautifulSoup(response.text, 'html.parser')

        # 找到所有的表格行
        rows = soup.find_all('tr')

        # 遍历每一行，提取需要的信息
        for row in rows:
            # 找到所有的单元格
            cols = row.find_all('td')
            if len(cols) > 5:  # 确保行中有足够的单元格
                reservation_id = cols[0].text.strip()
                places = re.sub(r'【.*?】', '', cols[1].text.strip()).split('-')
                lib = places[0]
                floor = places[1]
                seat = places[2].split(':')
                section = seat[0]
                code = seat[1]
                starttime = cols[2].text.strip()
                endtime = cols[3].text.strip()
                
                # 将信息添加到字典中
                reservations[reservation_id] = {
                    'lib': lib,
                    'floor': floor,
                    'section': section,
                    'code': code,
                    'starttime': starttime,
                    'endtime': endtime
                }

    # 整理数据
    for item in reservations.values():
        place = item["lib"] + "-" + item["floor"] + "-" + item["section"]
        data_date = datetime.strptime(item["starttime"], "%Y-%m-%d %H:%M:%S")

        if start_date <= data_date <= end_date:
            try:
                if place in all_data:
                    all_data[place] += 1
                else:
                    all_data[place] = 1
            except Exception as e:
                pass

    # 输出结果
    all_data = dict(sorted(all_data.items(), key=lambda x: x[1], reverse=False))
    if platform.system() == "Darwin":
        plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
    elif platform.system() == "Linux":
        plt.rcParams['font.family'] = ['Droid Sans Fallback', 'DejaVu Sans']
    else:
        plt.rcParams['font.sans-serif'] = ['SimHei']
        
    plt.figure(figsize=(20, 8))
    plt.barh(list(all_data.keys()), list(all_data.values()))
    for index, value in enumerate(list(all_data.values())):
        plt.text(value + 0.01 * max(all_data.values()),
                index,
                str(value),
                va='center')
        
    # plt.tight_layout()
    plt.xlim(0, 1.2 * max(all_data.values()))
    plt.title("华清大学自习情况")
    plt.xlabel("自习次数（次）")
    plt.savefig("result.png")
    plt.show()
