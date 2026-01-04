import requests
import pymysql
import time

# --- 配置区 ---
AMAP_KEY = ' '  # 替换为你申请的Key（高德API Key，需要在高德开放平台申请）
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'your_password',  # 替换为你的数据库密码
    'database': 'metronav_shanghai'
}

def fetch_and_save_pois():
    page = 1
    total_count = 0
    
    # 建立数据库连接
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()

    print(f"开始爬取上海地铁站点数据...")

    while True:
        # 高德POI搜索接口地址
        url = "https://restapi.amap.com/v3/place/text"
        params = {
            'key': AMAP_KEY,
            'keywords': '地铁站',
            'types': '150500',      # 地铁站专属分类代码
            'city': '上海',
            'citylimit': True,      # 仅限上海市内
            'offset': 20,           # 每页记录数
            'page': page,
            'output': 'JSON'
        }

        response = requests.get(url, params=params)
        data = response.json()

        if data['status'] == '1' and data['pois']:
            pois = data['pois']
            for poi in pois:
                name = poi['name'].replace('地铁站', '') # 去掉后缀保持纯净
                location = poi['location'] # 格式: "lng,lat"
                lng, lat = location.split(',')

                # 写入数据库 (规范化后的表名: subway_stations)
                sql = """
                INSERT INTO subway_stations (station_name, longitude, latitude) 
                VALUES (%s, %s, %s) 
                ON DUPLICATE KEY UPDATE longitude=%s, latitude=%s
                """
                cursor.execute(sql, (name, lng, lat, lng, lat))
                total_count += 1
            
            print(f"已处理第 {page} 页，当前累计抓取 {total_count} 个站点")
            
            # 判断是否还有下一页
            if len(pois) < 20: 
                break
            page += 1
            time.sleep(0.2) # 稍微停顿，避免触发API频率限制
        else:
            print("抓取完毕或遇到错误")
            break

    conn.commit()
    cursor.close()
    conn.close()
    print(f"总计存入 {total_count} 个站点。")

if __name__ == '__main__':
    fetch_and_save_pois()