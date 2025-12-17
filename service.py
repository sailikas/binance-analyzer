"""
后台定时服务
"""
import time
from threading import Thread
from analysis_core import BinanceAnalyzer
from database import DatabaseManager
from notification_manager import NotificationManager
from config_manager import ConfigManager

class AnalysisService:
    def __init__(self):
        self.config_manager = ConfigManager()
        self.db_manager = DatabaseManager()
        self.notif_manager = NotificationManager()
        self.is_running = False
        self.thread = None
    
    def start_service(self):
        if self.is_running:
            print("服务已在运行中")
            return False
        
        self.is_running = True
        self.thread = Thread(target=self._service_loop, daemon=True)
        self.thread.start()
        print("后台服务已启动")
        return True
    
    def stop_service(self):
        if not self.is_running:
            return False
        
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=5)
        print("后台服务已停止")
        return True
    
    def _service_loop(self):
        while self.is_running:
            if self.config_manager.get("schedule_enabled", False):
                try:
                    self._run_analysis()
                except Exception as e:
                    print(f"定时分析出错: {e}")
                    if self.config_manager.get("notify_on_complete", True):
                        self.notif_manager.notify_error(str(e))
            
            interval = self.config_manager.get("schedule_interval", 7200)
            for _ in range(interval):
                if not self.is_running:
                    break
                time.sleep(1)
    
    def _run_analysis(self):
        print("开始定时分析...")
        
        analyzer_config = self.config_manager.get_analyzer_config()
        analyzer = BinanceAnalyzer(config=analyzer_config)
        results = analyzer.analyze()
        
        last_analysis = self.db_manager.get_latest_analysis()
        self.db_manager.save_analysis(results, analyzer_config)
        
        if self.config_manager.get("notify_on_complete", True):
            self.notif_manager.notify_analysis_complete(len(results))
        
        if last_analysis and self.config_manager.get("notify_on_change", True):
            comparison = self.db_manager.compare_results(
                last_analysis["results"],
                results
            )
            
            if comparison["has_changes"]:
                self.notif_manager.notify_changes_detected(
                    len(comparison["new"]),
                    len(comparison["removed"])
                )
        
        print(f"定时分析完成，找到 {len(results)} 个符合条件的币种")
        return results

service_instance = None

def get_service():
    global service_instance
    if service_instance is None:
        service_instance = AnalysisService()
    return service_instance
