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
        self._log("[定时服务] 已启动 - 24小时保活模式")
        
        last_heartbeat = datetime.datetime.now()
        heartbeat_interval = 300  # 每5分钟打印一次心跳
        
        while self.is_running:
            try:
                # 心跳检测
                now = datetime.datetime.now()
                if (now - last_heartbeat).total_seconds() >= heartbeat_interval:
                    self._log(f"[心跳] 服务运行中 - {now.strftime('%Y-%m-%d %H:%M:%S')}")
                    last_heartbeat = now
                
                schedule_enabled = self.config_manager.get("schedule_enabled", False)
                
                if schedule_enabled:
                    try:
                        self._log("[定时分析] 开始执行...")
                        self._run_analysis()
                        self._log("[定时分析] 执行完成")
                    except Exception as e:
                        self._log(f"[定时分析] 出错: {str(e)[:100]}")
                        import traceback
                        traceback.print_exc()
                        
                        # 发送错误通知
                        try:
                            if self.config_manager.get("notify_on_complete", True):
                                self.notif_manager.notify_error(str(e))
                        except:
                            pass
                        
                        # 等待30秒后继续（避免频繁出错）
                        time.sleep(30)
                        continue
                
                interval = self.config_manager.get("schedule_interval", 7200)
                
                # 分段睡眠，每10秒检查一次是否需要停止
                for i in range(0, interval, 10):
                    if not self.is_running:
                        self._log("[定时服务] 收到停止信号")
                        break
                    time.sleep(min(10, interval - i))
                    
            except Exception as e:
                # 服务循环出错，记录日志但不退出
                self._log(f"[定时服务] 循环异常: {str(e)[:100]}")
                import traceback
                traceback.print_exc()
                time.sleep(60)  # 等待1分钟后重试
        
        self._log("[定时服务] 已停止")
    
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
        current_count = len(results)
        self._log(f"[定时分析] 找到 {current_count} 个币种")
        
        # 获取上次分析结果
        last_analysis = self.db_manager.get_latest_analysis()
        last_count = len(last_analysis["results"]) if last_analysis else 0
        
        # 保存本次分析结果
        self.db_manager.save_analysis(results, analyzer_config)
        
        # 通知逻辑：
        # 1. 当前结果为0 且 上次也是0 -> 不通知
        # 2. 当前结果为0 且 上次>0 -> 通知（从有变无）
        # 3. 当前结果>0 -> 正常通知
        
        should_notify = False
        notify_type = None
        
        if current_count == 0:
            if last_count > 0:
                # 从有结果变成无结果，发送特殊通知
                should_notify = True
                notify_type = "zero_from_nonzero"
                self._log(f"[通知逻辑] 匹配数量从 {last_count} 变为 0，将发送通知")
            else:
                # 持续为0，不通知
                self._log(f"[通知逻辑] 匹配数量为 0，跳过通知")
        else:
            # 有结果，正常通知
            should_notify = True
            notify_type = "normal"
            self._log(f"[通知逻辑] 找到 {current_count} 个币种，将发送通知")
        
        # 发送通知
        if should_notify and self.config_manager.get("notify_on_complete", True):
            self._log("[定时分析] 准备发送完成通知...")
            
            if notify_type == "zero_from_nonzero":
                # 发送特殊的"清零"通知
                result = self.notif_manager.notify_zero_result(last_count)
            else:
                # 正常通知
                result = self.notif_manager.notify_analysis_complete(current_count, results)
            
            self._log(f"[定时分析] 通知发送{'成功' if result else '失败'}")
        
        # 检测变化通知（仅当两次都有结果时）
        if last_analysis and self.config_manager.get("notify_on_change", True):
            if current_count > 0 and last_count > 0:
                comparison = self.db_manager.compare_results(
                    last_analysis["results"],
                    results
                )
                
                if comparison["has_changes"]:
                    self._log(f"[定时分析] 检测到变化: +{len(comparison['new'])} -{len(comparison['removed'])}")
                    
                    # 准备币种详细信息
                    new_coins = []
                    removed_coins = []
                    
                    # 新增币种（包含涨幅信息）
                    for coin_data in comparison["new"]:
                        symbol = coin_data.get("symbol", "")
                        # 从当前结果中获取涨幅信息
                        for result in results:
                            if result.get("symbol") == symbol:
                                new_coins.append({
                                    "symbol": symbol,
                                    "changes": result.get("changes", {})
                                })
                                break
                    
                    # 移除币种
                    for coin_data in comparison["removed"]:
                        symbol = coin_data.get("symbol", "")
                        removed_coins.append({"symbol": symbol})
                    
                    self.notif_manager.notify_changes_detected(new_coins, removed_coins)
        
        return results

service_instance = None

def get_service():
    global service_instance
    if service_instance is None:
        service_instance = AnalysisService()
    return service_instance
