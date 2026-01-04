CREATE DATABASE IF NOT EXISTS metronav_shanghai CHARACTER SET utf8mb4;
USE metronav_shanghai;

-- 1. 线路表 (规范化名: subway_lines)
CREATE TABLE subway_lines (
    line_id INT AUTO_INCREMENT PRIMARY KEY,
    line_name VARCHAR(50) NOT NULL UNIQUE,
    line_color VARCHAR(7),
    first_opening DATE
) ENGINE=InnoDB;

-- 2. 站点表 (规范化名: subway_stations)
CREATE TABLE subway_stations (
    station_id INT AUTO_INCREMENT PRIMARY KEY,
    station_name VARCHAR(100) NOT NULL UNIQUE,
    longitude DECIMAL(10, 7) NOT NULL,
    latitude DECIMAL(10, 7) NOT NULL
) ENGINE=InnoDB;

-- 3. 线路-站点关系表 (规范化名: subway_line_stations)
CREATE TABLE subway_line_stations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    line_id INT NOT NULL,
    station_id INT NOT NULL,
    station_order INT NOT NULL,
    FOREIGN KEY (line_id) REFERENCES subway_lines(line_id) ON DELETE CASCADE,
    FOREIGN KEY (station_id) REFERENCES subway_stations(station_id) ON DELETE CASCADE,
    UNIQUE KEY (line_id, station_id)
) ENGINE=InnoDB;

-- 4. 换乘表 (规范化名: subway_transfers)
CREATE TABLE subway_transfers (
    transfer_id INT AUTO_INCREMENT PRIMARY KEY,
    from_station_id INT NOT NULL,
    to_station_id INT NOT NULL,
    transfer_time INT DEFAULT 180,
    FOREIGN KEY (from_station_id) REFERENCES subway_stations(station_id),
    FOREIGN KEY (to_station_id) REFERENCES subway_stations(station_id)
) ENGINE=InnoDB;