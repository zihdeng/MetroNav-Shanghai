import pymysql
import re
from metro_data import METRO_DATA 

# 数据库连接配置 (请确保填入你的实际信息)
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'your_password', 
    'database': 'metronav_shanghai',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

def clean_station_name(name):
    """清洗名称，去除各种括号备注"""
    name = re.sub(r'\(.*?\)', '', name)
    name = re.sub(r'（.*?）', '', name)
    return name.strip()

def run_sync():
    conn = pymysql.connect(**db_config)
    try:
        with conn.cursor() as cursor:
            # 1. 加载库中现有的 219 个合法站点映射
            cursor.execute("SELECT station_id, station_name FROM subway_stations")
            db_stations = {row['station_name']: row['station_id'] for row in cursor.fetchall()}
            print(f"--- 已加载库中 {len(db_stations)} 个站点数据 ---")

            # 2. 清空旧的线路关联数据（重置拓扑）
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
            cursor.execute("TRUNCATE TABLE subway_line_stations")
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1")

            # 3. 初始化全局线路去重容器
            # 格式: { line_id: set(已处理的station_id) }
            global_line_processed = {}

            # 4. 遍历 METRO_DATA 字典
            for line_label, stations in METRO_DATA.items():
                # 提取纯净线路名，如 "11号线"
                line_name = re.sub(r'（.*?）', '', line_label).strip()
                
                # 获取该线路对应的 line_id
                cursor.execute("SELECT line_id FROM subway_lines WHERE line_name = %s", (line_name,))
                line_info = cursor.fetchone()
                if not line_info:
                    print(f"跳过: {line_name} (未在数据库找到)")
                    continue
                
                l_id = line_info['line_id']
                
                # 如果是这条线路第一次出现，初始化集合
                if l_id not in global_line_processed:
                    global_line_processed[l_id] = set()
                
                # 当前线路的起始序号应接着已有的站数往后排
                current_seq = len(global_line_processed[l_id]) + 1
                
                for raw_s in stations:
                    s_clean = clean_station_name(raw_s)
                    
                    # 规则：只记录库中已有的站点
                    if s_clean in db_stations:
                        s_id = db_stations[s_clean]
                        
                        # 核心防重逻辑：如果该 line_id 下已经插入过该站，则跳过
                        if s_id in global_line_processed[l_id]:
                            continue
                            
                        # 插入数据库
                        insert_sql = """
                            INSERT INTO subway_line_stations (line_id, station_id, station_order) 
                            VALUES (%s, %s, %s)
                        """
                        cursor.execute(insert_sql, (l_id, s_id, current_seq))
                        
                        # 更新内存状态
                        global_line_processed[l_id].add(s_id)
                        current_seq += 1
                
                print(f"处理中: {line_label} -> 已入库总站数: {len(global_line_processed[l_id])}")

            conn.commit()
            print("\n" + "="*40)
            print("【同步成功】拓扑关联已全部写入数据库！")
            print("="*40)

    except Exception as e:
        conn.rollback()
        print(f"\n【执行失败】事务已回滚。错误详情: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    run_sync()