"""
数据库管理模块 - 历史记录存储
"""
import sqlite3
import json
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_file="analysis_history.db"):
        self.db_file = db_file
        self.init_database()
    
    def init_database(self):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        # 创建新表（如果不存在）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analysis_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                duration REAL NOT NULL,
                results_json TEXT NOT NULL,
                symbol_count INTEGER NOT NULL,
                config_json TEXT
            )
        """)
        
        # 检查是否需要添加timestamp列（兼容旧版本）
        cursor.execute("PRAGMA table_info(analysis_history)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'timestamp' not in columns:
            cursor.execute("ALTER TABLE analysis_history ADD COLUMN timestamp TEXT")
        
        conn.commit()
        conn.close()
    
    def save_analysis(self, analysis_data, config=None):
        """保存分析结果，支持新的时间结构"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # 兼容新旧数据格式
            if isinstance(analysis_data, dict) and "results" in analysis_data:
                # 新格式：包含时间信息的字典
                results = analysis_data["results"]
                start_time = analysis_data.get("start_time", datetime.now().isoformat())
                end_time = analysis_data.get("end_time", datetime.now().isoformat())
                duration = analysis_data.get("duration", 0)
            else:
                # 旧格式：只有结果列表
                results = analysis_data
                now = datetime.now().isoformat()
                start_time = end_time = now
                duration = 0
            
            results_json = json.dumps(results, ensure_ascii=False)
            symbol_count = len(results)
            config_json = json.dumps(config, ensure_ascii=False) if config else None
            
            cursor.execute("""
                INSERT INTO analysis_history (start_time, end_time, duration, results_json, symbol_count, config_json)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (start_time, end_time, duration, results_json, symbol_count, config_json))
            
            conn.commit()
            record_id = cursor.lastrowid
            conn.close()
            
            return record_id
        except Exception as e:
            print(f"保存分析结果失败: {e}")
            return None
    
    def get_latest_analysis(self):
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # 检查表结构，兼容新旧版本
            cursor.execute("PRAGMA table_info(analysis_history)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if "start_time" in columns:
                # 新表结构
                cursor.execute("""
                    SELECT id, start_time, end_time, duration, results_json, symbol_count, config_json
                    FROM analysis_history
                    ORDER BY id DESC
                    LIMIT 1
                """)
                row = cursor.fetchone()
                conn.close()
                
                if row:
                    return {
                        "id": row[0],
                        "timestamp": row[2],  # 使用end_time作为主要时间戳
                        "start_time": row[1],
                        "end_time": row[2],
                        "duration": row[3],
                        "results": json.loads(row[4]),
                        "symbol_count": row[5],
                        "config": json.loads(row[6]) if row[6] else None
                    }
            else:
                # 旧表结构（兼容性）
                cursor.execute("""
                    SELECT id, timestamp, results_json, symbol_count, config_json
                    FROM analysis_history
                    ORDER BY id DESC
                    LIMIT 1
                """)
                row = cursor.fetchone()
                conn.close()
                
                if row:
                    return {
                        "id": row[0],
                        "timestamp": row[1],
                        "start_time": row[1],
                        "end_time": row[1],
                        "duration": 0,
                        "results": json.loads(row[2]),
                        "symbol_count": row[3],
                        "config": json.loads(row[4]) if row[4] else None
                    }
            return None
        except Exception as e:
            print(f"获取最新分析失败: {e}")
            return None
    
    def get_history_list(self, limit=50):
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # 检查表结构，兼容新旧版本
            cursor.execute("PRAGMA table_info(analysis_history)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if "end_time" in columns:
                # 新表结构
                cursor.execute("""
                    SELECT id, end_time, symbol_count, duration
                    FROM analysis_history
                    ORDER BY id DESC
                    LIMIT ?
                """, (limit,))
                rows = cursor.fetchall()
                conn.close()
                
                return [
                    {
                        "id": r[0], 
                        "timestamp": r[1],  # 使用end_time
                        "symbol_count": r[2],
                        "duration": r[3]
                    } 
                    for r in rows
                ]
            else:
                # 旧表结构（兼容性）
                cursor.execute("""
                    SELECT id, timestamp, symbol_count
                    FROM analysis_history
                    ORDER BY id DESC
                    LIMIT ?
                """, (limit,))
                rows = cursor.fetchall()
                conn.close()
                
                return [
                    {
                        "id": r[0], 
                        "timestamp": r[1], 
                        "symbol_count": r[2],
                        "duration": 0
                    } 
                    for r in rows
                ]
        except Exception as e:
            print(f"获取历史列表失败: {e}")
            return []
    
    def get_analysis_by_id(self, record_id):
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # 检查表结构，兼容新旧版本
            cursor.execute("PRAGMA table_info(analysis_history)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if "start_time" in columns:
                # 新表结构
                cursor.execute("""
                    SELECT id, start_time, end_time, duration, results_json, symbol_count, config_json
                    FROM analysis_history
                    WHERE id = ?
                """, (record_id,))
                row = cursor.fetchone()
                conn.close()
                
                if row:
                    return {
                        "id": row[0],
                        "timestamp": row[2],  # 使用end_time作为主要时间戳
                        "start_time": row[1],
                        "end_time": row[2],
                        "duration": row[3],
                        "results": json.loads(row[4]),
                        "symbol_count": row[5],
                        "config": json.loads(row[6]) if row[6] else None
                    }
            else:
                # 旧表结构（兼容性）
                cursor.execute("""
                    SELECT id, timestamp, results_json, symbol_count, config_json
                    FROM analysis_history
                    WHERE id = ?
                """, (record_id,))
                row = cursor.fetchone()
                conn.close()
                
                if row:
                    return {
                        "id": row[0],
                        "timestamp": row[1],
                        "start_time": row[1],
                        "end_time": row[1],
                        "duration": 0,
                        "results": json.loads(row[2]),
                        "symbol_count": row[3],
                        "config": json.loads(row[4]) if row[4] else None
                    }
            return None
        except Exception as e:
            print(f"获取分析记录失败: {e}")
            return None
    
    def compare_results(self, results1, results2):
        symbols1 = set([r["symbol"] for r in results1])
        symbols2 = set([r["symbol"] for r in results2])
        
        new_symbols = symbols2 - symbols1
        removed_symbols = symbols1 - symbols2
        common_symbols = symbols1 & symbols2
        
        return {
            "new": list(new_symbols),
            "removed": list(removed_symbols),
            "common": list(common_symbols),
            "has_changes": len(new_symbols) > 0 or len(removed_symbols) > 0
        }
    
    def delete_old_records(self, keep_count=100):
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            cursor.execute("""
                DELETE FROM analysis_history
                WHERE id NOT IN (
                    SELECT id FROM analysis_history
                    ORDER BY id DESC
                    LIMIT ?
                )
            """, (keep_count,))
            
            deleted = cursor.rowcount
            conn.commit()
            conn.close()
            
            return deleted
        except Exception as e:
            print(f"删除旧记录失败: {e}")
            return 0
