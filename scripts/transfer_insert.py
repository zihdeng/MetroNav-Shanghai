import pymysql
import math
import random

# 数据库配置（请确认你的密码和库名）
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'your_password',
    'database': 'metronav_shanghai',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

def haversine(lat1, lon1, lat2, lon2):
    """计算两个经纬度坐标之间的物理距离（米）"""
    R = 6371000 
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def generate_enhanced_transfers():
    conn = pymysql.connect(**DB_CONFIG)
    try:
        with conn.cursor() as cursor:
            print("--- 开始生成增强版换乘关系 (适配 subway_transfers) ---")
            
            # 1. 重置你的换乘表
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
            cursor.execute("TRUNCATE TABLE subway_transfers")
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1")

            # 2. 获取站点坐标
            cursor.execute("SELECT station_id, station_name, longitude, latitude FROM subway_stations")
            all_stations = cursor.fetchall()
            
            # 3. 获取站点与线路关系 (用于识别跨线)
            cursor.execute("SELECT station_id, line_id FROM subway_line_stations")
            line_relations = {}
            for row in cursor.fetchall():
                line_relations.setdefault(row['station_id'], set()).add(row['line_id'])

            count = 0
            # 4. 逻辑对比
            for i in range(len(all_stations)):
                for j in range(i + 1, len(all_stations)):
                    s1, s2 = all_stations[i], all_stations[j]
                    
                    # 计算物理距离
                    dist = haversine(s1['latitude'], s1['longitude'], s2['latitude'], s2['longitude'])
                    
                    # 判定条件：1. ID相同（逻辑换乘） 2. 距离 < 1500米（物理近邻换乘）
                    is_same = (s1['station_id'] == s2['station_id'])
                    is_near = (dist < 1500)

                    if is_same or is_near:
                        l1, l2 = line_relations.get(s1['station_id'], set()), line_relations.get(s2['station_id'], set())
                        
                        # 只有当涉及不同线路时，换乘才有意义
                        if l1 and l2 and (l1 != l2 or is_near):
                            # 随机化时间：180s - 480s (3到8分钟)
                            # 模拟早晚高峰或不同车站步行长度的差异
                            rand_time = random.randint(180, 480)
                            
                            sql = "INSERT INTO subway_transfers (from_station_id, to_station_id, transfer_time) VALUES (%s, %s, %s)"
                            cursor.execute(sql, (s1['station_id'], s2['station_id'], rand_time))
                            cursor.execute(sql, (s2['station_id'], s1['station_id'], rand_time))
                            count += 2

            conn.commit()
            print(f"成功！已向 subway_transfers 写入 {count} 条随机化换乘权重。")
            
    except Exception as e:
        conn.rollback()
        print(f"执行失败: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    generate_enhanced_transfers()