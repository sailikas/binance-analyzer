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
        import datetime
        self._log("[定时服务] 已启动")
        
        while self.is_running:
            schedule_enabled = self.config_manager.get("schedule_enabled", False)
            
            if schedule_enabled:
                try:
                    self._log("[定时分析] 开始执行...")
                    self._run_analysis()
                    self._log("[定时分析] 执行完成")
                except Exception as e:
                    self._log(f"[定时分析] 出错: {str(e)[:50]}")
                    import traceback
                    traceback.print_exc()
                    if self.config_manager.get("notify_on_complete", True):
                        self.notif_manager.notify_error(str(e))
            
            interval = self.config_manager.get("schedule_interval", 7200)
            
            for i in range(interval):
                if not self.is_running:
                    self._log("[定时服务] 已停止")
                    break
                time.sleep(1)
    
    def _log(self, message):
        """发送日志到回调函数"""
        print(message)
        if hasattr(self, 'log_callback') and self.log_callback:
            try:
                self.log_callback(message)
            except:
                pass
    
    def _run_analysis(self):
        analyzer_config = self.config_manager.get_analyzer_config()
        analyzer = BinanceAnalyzer(config=analyzer_config)
        
        results = analyzer.analyze()
        self._log(f"[定时分析] 找到 {len(results)} 个币种")
        
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
                self._log(f"[定时分析] 检测到变化: +{len(comparison['new'])} -{len(comparison['removed'])}")
                self.notif_manager.notify_changes_detected(
                    len(comparison["new"]),
                    len(comparison["removed"])
                )
        
        return results

service_instance = None

def get_service():
    global service_instance
    if service_instance is None:
        service_instance = AnalysisService()
    return service_instance
