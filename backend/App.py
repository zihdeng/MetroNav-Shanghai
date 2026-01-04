from flask import Flask, jsonify, request
from flask_cors import CORS
import pymysql
import pymysql.cursors
import heapq
import math
from collections import defaultdict

app = Flask(__name__)
CORS(app)

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': ' ', # 这里填写mysql密码
    'database': 'metronav_shanghai',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

def get_db_connection():
    """获取数据库连接"""
    return pymysql.connect(**DB_CONFIG)

# --- 辅助函数：计算地理距离（Haversine公式） ---
def haversine_distance(lat1, lon1, lat2, lon2):
    """计算两点间的估算时间（秒），假设地铁平均时速 35km/h"""
    R = 6371  # 地球半径 km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2) * math.sin(dlat/2) + \
        math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * \
        math.sin(dlon/2) * math.sin(dlon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    distance_km = R * c
    
    # 估算时间：距离 / 速度。假设速度 35km/h = ~0.58 km/min = ~0.0097 km/s
    # 这里返回秒
    return int(distance_km / (35 / 3600))

# --- 核心算法逻辑 ---

def build_graph(cursor):
    """
    从数据库构建邻接表图。
    结构: graph[u][v] = {'weight': time_seconds, 'line_name': '1号线', 'line_id': 1}
    """
    graph = defaultdict(dict)
    
    # 1. 获取所有站点信息 (用于计算默认距离)
    cursor.execute("SELECT station_id, station_name, latitude, longitude FROM subway_stations")
    stations = {row['station_id']: row for row in cursor.fetchall()}
    
    # 2. 获取线路的相邻关系
    # 按线路和顺序排序，这样相邻的记录就是相邻的站点
    cursor.execute("""
        SELECT ls.line_id, ls.station_id, ls.station_order, l.line_name 
        FROM subway_line_stations ls
        JOIN subway_lines l ON ls.line_id = l.line_id
        ORDER BY ls.line_id, ls.station_order
    """)
    line_stations = cursor.fetchall()
    
    # 遍历列表，连接相邻站点
    for i in range(len(line_stations) - 1):
        curr = line_stations[i]
        next_stat = line_stations[i+1]
        
        # 必须是同一条线且顺序相邻
        if curr['line_id'] == next_stat['line_id'] and next_stat['station_order'] == curr['station_order'] + 1:
            u, v = curr['station_id'], next_stat['station_id']
            
            # 默认权重：计算物理距离
            s_u = stations[u]
            s_v = stations[v]
            default_weight = haversine_distance(s_u['latitude'], s_u['longitude'], s_v['latitude'], s_v['longitude'])
            
            # 添加双向边
            # 注意：如果是换乘站，两个站点间可能有多条线连接（如1号线和2号线都经过人民广场-南京东路...不对，是不同路段）
            # 这里简单处理：如果已存在边，保留权重最小的（虽然物理上很少见两站间多条线完全重合）
            if v not in graph[u] or default_weight < graph[u][v]['weight']:
                graph[u][v] = {'weight': default_weight, 'line_name': curr['line_name'], 'line_id': curr['line_id']}
                graph[v][u] = {'weight': default_weight, 'line_name': curr['line_name'], 'line_id': curr['line_id']}

    # 3. 使用数据库中定义的精确时间覆盖默认估算时间
    # 你的SQL中 `subway_transfers` 表看起来存储的是站间运行时间 (transfer_time)
    cursor.execute("SELECT from_station_id, to_station_id, transfer_time FROM subway_transfers")
    transfers = cursor.fetchall()
    
    for t in transfers:
        u, v = t['from_station_id'], t['to_station_id']
        weight = t['transfer_time']
        
        # 如果这两个站在图里已经通过线路连接了，更新时间为数据库里的精确时间
        if u in graph and v in graph[u]:
            graph[u][v]['weight'] = weight
            graph[v][u]['weight'] = weight # 假设双向时间一致
            
    return graph, stations

def dijkstra(graph, start_id, end_id):
    """
    标准的 Dijkstra 最短路径算法
    """
    # 优先队列: (累积时间, 当前节点ID, 路径列表)
    # 路径列表存储: [(station_id, line_name_used_to_get_here), ...]
    pq = [(0, start_id, [])]
    visited = set()
    min_times = {start_id: 0}
    
    while pq:
        current_time, current_node, path = heapq.heappop(pq)
        
        if current_node in visited:
            continue
        visited.add(current_node)
        
        # 到达终点
        if current_node == end_id:
            return current_time, path
        
        # 遍历邻居
        for neighbor, edge_info in graph[current_node].items():
            weight = edge_info['weight']
            line_name = edge_info['line_name']
            new_time = current_time + weight
            
            if new_time < min_times.get(neighbor, float('inf')):
                min_times[neighbor] = new_time
                # 记录路径：保存 (neighbor_id, edge_line_name)
                new_path = path + [{'id': neighbor, 'line': line_name}]
                heapq.heappush(pq, (new_time, neighbor, new_path))
                
    return None, None

# --- 1. 基础数据接口 ---

@app.route('/api/stations', methods=['GET'])
def get_stations():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # 确保返回浮点数类型的 lat/lng
            sql = "SELECT station_id, station_name, longitude as lng, latitude as lat FROM subway_stations"
            cursor.execute(sql)
            stations = cursor.fetchall()
            # 转换 Decimal 为 float，防止 JSON 序列化报错
            for s in stations:
                s['lng'] = float(s['lng'])
                s['lat'] = float(s['lat'])
            return jsonify(stations)
    finally:
        conn.close()

# --- 2. 统计信息接口 ---

@app.route('/api/stats', methods=['GET'])
def get_stats():
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # 1. 线路总数
            cursor.execute("SELECT COUNT(*) as count FROM subway_lines")
            l_res = cursor.fetchone()
            line_count = int(l_res['count']) if l_res else 0
            
            # 2. 站点总数
            cursor.execute("SELECT COUNT(DISTINCT station_id) as count FROM subway_stations")
            s_res = cursor.fetchone()
            station_count = int(s_res['count']) if s_res else 0
            
            # 3. 最繁忙站点
            cursor.execute("""
                SELECT s.station_name, COUNT(ls.line_id) as line_count
                FROM subway_stations s 
                JOIN subway_line_stations ls ON s.station_id = ls.station_id 
                GROUP BY s.station_id, s.station_name
                ORDER BY line_count DESC 
                LIMIT 1
            """)
            busy = cursor.fetchone()
            
            return jsonify({
                "lineCount": line_count,
                "stationCount": station_count,
                "busyStation": busy['station_name'] if busy else "无数据",
                "busyStationLines": int(busy['line_count']) if busy else 0
            })
    except Exception as e:
        print(f"统计接口详细报错: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()

# --- 3. 核心算法接口  ---

@app.route('/api/route', methods=['POST'])
def plan_route():
    data = request.json
    start_id = data.get('start_station_id')
    end_id = data.get('end_station_id')
    
    if not start_id or not end_id:
        return jsonify({"error": "缺少起始站或终点站ID"}), 400
        
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # 1. 构建图
            graph, stations_info = build_graph(cursor)
            
            # 2. 运行 Dijkstra
            total_seconds, raw_path = dijkstra(graph, start_id, end_id)
            
            if raw_path is None and start_id != end_id:
                 return jsonify({"error": "无法找到路径"}), 404
                 
            # 3. 格式化返回结果以适配前端
            # 起点需手动加入 path 的第一个
            start_station_info = stations_info[start_id]
            formatted_path = [{
                "station_id": start_id,
                "station_name": start_station_info['station_name'],
                "lat": float(start_station_info['latitude']),
                "lng": float(start_station_info['longitude']),
                "line_name": "起点", # 起点没有上一站线路
                "transfer_line": None 
            }]
            
            current_line = None
            
            if raw_path:
                for step in raw_path:
                    sid = step['id']
                    line = step['line']
                    info = stations_info[sid]
                    
                    # 判断是否换乘：如果当前线路和上一段线路不同，且不是起点
                    transfer = None
                    if current_line and line != current_line:
                        transfer = line # 标记换乘到了哪条线
                    
                    current_line = line
                    
                    formatted_path.append({
                        "station_id": sid,
                        "station_name": info['station_name'],
                        "lat": float(info['latitude']),
                        "lng": float(info['longitude']),
                        "line_name": line,
                        "transfer_line": transfer
                    })

            result = {
                "path": formatted_path,
                "total_stations": len(formatted_path),
                "estimated_time": math.ceil(total_seconds / 60) if total_seconds else 0 # 秒转分钟
            }
            return jsonify(result)
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

if __name__ == '__main__':
    app.run(debug=True, port=8000)