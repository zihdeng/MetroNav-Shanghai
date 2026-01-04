# MetroNav-Shanghai - 上海轨道交通最优路径规划系统

## 📖 项目简介

**MetroNav-Shanghai** 是一个高效、直观的 Web 应用程序，专为上海市轨道交通出行设计。该系统旨在为用户提供最优的乘坐方案。用户只需输入起始站点和终点站点，系统即可快速计算并展示出最佳路径。

核心功能包括：
- **最优路径规划**：综合考虑时间、换乘次数等因素，提供最佳出行建议。
- **可视化地图**：基于 Leaflet 的交互式地图，直观展示线路和站点。
- **实时计算**：后端采用高效算法实时计算路径。

## 🛠️ 技术栈

本项目采用前后端分离的架构：

### 后端 (Backend)
- **语言**：Python 3
- **框架**：Flask (Web 框架), Flask-CORS (跨域处理)
- **数据库驱动**：PyMySQL
- **算法**：Dijkstra / BFS (用于路径搜索)

### 前端 (Frontend)
- **核心框架**：Vue.js 3
- **UI 组件库**：Element Plus
- **地图引擎**：Leaflet
- **HTTP 客户端**：Axios
- **基础技术**：HTML5, CSS3

### 数据库 (Database)
- **数据库**：MySQL
- **字符集**：utf8mb4

## 📂 目录结构

```
MetroNav-Shanghai/
├── backend/                # 后端代码目录
│   ├── App.py              # Flask 主应用程序入口
│   └── requirements.txt    # Python 依赖列表
├── frontend/               # 前端代码目录
│   └── index.html          # 单页应用入口文件
├── sql/                    # 数据库相关文件
│   ├── metronav_shanghai_backup.sql  # 数据库备份/初始化 SQL 文件
│   └── mysql.md            # 数据库建表语句说明
├── docs/                   # 项目文档
├── scripts/                # 辅助脚本
└── README.md               # 项目说明文档
```

## 🚀 快速开始 (部署指南)

请按照以下步骤在本地环境部署和运行本项目。

### 1. 环境准备
确保您的系统已安装以下软件：
- Python 3.8+
- MySQL 5.7+ 或 8.0+
- Git

### 2. 克隆项目
```bash
git clone https://github.com/zihdeng/MetroNav-Shanghai.git
cd MetroNav-Shanghai
```

### 3. 数据库配置
1.  登录 MySQL 数据库。
2.  创建数据库 `metronav_shanghai`：
    ```sql
    CREATE DATABASE metronav_shanghai CHARACTER SET utf8mb4;
    ```
3.  导入数据。使用 `sql/metronav_shanghai_backup.sql` 文件初始化数据库：
    ```bash
    mysql -u root -p metronav_shanghai < sql/metronav_shanghai_backup.sql
    ```
    *(或者使用 Navicat、DBeaver 等工具导入 SQL 文件)*

### 4. 后端配置与启动
1.  进入 `backend` 目录：
    ```bash
    cd backend
    ```
2.  安装 Python 依赖：
    ```bash
    pip install -r requirements.txt
    ```
3.  **重要**：修改 `App.py` 中的数据库连接配置。打开 `backend/App.py`，找到 `DB_CONFIG` 部分，填入您的 MySQL 密码：
    ```python
    DB_CONFIG = {
        'host': 'localhost',
        'user': 'root',
        'password': 'YOUR_PASSWORD',  # <--- 在这里修改您的数据库密码
        'database': 'metronav_shanghai',
        # ...
    }
    ```
4.  启动 Flask 服务：
    ```bash
    python App.py
    ```
    服务默认将在 `http://127.0.0.1:5000` 运行。

### 5. 前端运行
由于前端是纯静态的 HTML 文件，您可以直接在浏览器中打开 `frontend/index.html` 文件即可使用。

为了更好的体验（避免跨域限制等问题），建议使用简单的 HTTP 服务器运行：
```bash
cd ../frontend
python -m http.server 8000
```
然后在浏览器访问 `http://localhost:8000`。

## 📝 功能说明

1.  **站点查询**：在左侧面板输入起点和终点，支持模糊搜索。
2.  **路径规划**：点击“查询路线”按钮，系统将计算并在地图上绘制路线。
3.  **详情展示**：显示预计耗时、经过站点、换乘指引等详细信息。

## ✨ 项目亮点 (相比现有软件)

虽然市面上已有成熟的地图软件，但 MetroNav-Shanghai 仍具有以下独特优势：

- **轻量级与纯净体验**：专注于地铁路径规划，无广告干扰，无冗余功能，加载速度快。
- **开源与可定制**：代码完全开源，适合开发者学习、研究图算法（如 Dijkstra）在实际场景中的应用，也可根据需求自由定制换乘策略。
- **数据透明与隐私保护**：所有数据存储在本地 MySQL 数据库中，无需担心个人出行数据的隐私泄露问题。
- **算法透明**：后端路径计算逻辑清晰可见，便于学术研究或教学演示。

## 🤝 贡献

欢迎提交 Issue 或 Pull Request 来改进本项目！

## 📄 许可证

[MIT License](LICENSE)
