"""
通知管理模块
"""
try:
    from plyer import notification
    PLYER_AVAILABLE = True
except ImportError:
    PLYER_AVAILABLE = False
    print("警告: plyer 未安装，通知功能不可用")

class NotificationManager:
    def __init__(self):
        self.app_name = "币安分析工具"
    
    def send_notification(self, title, message, timeout=10):
        if not PLYER_AVAILABLE:
            print(f"[通知] {title}: {message}")
            return False
        
        try:
            notification.notify(
                title=title,
                message=message,
                app_name=self.app_name,
                timeout=timeout
            )
            return True
        except Exception as e:
            print(f"发送通知失败: {e}")
            return False
    
    def notify_analysis_complete(self, symbol_count):
        title = "分析完成"
        message = f"找到 {symbol_count} 个符合条件的交易对"
        return self.send_notification(title, message)
    
    def notify_changes_detected(self, new_count, removed_count):
        title = "检测到变化"
        parts = []
        if new_count > 0:
            parts.append(f"新增 {new_count} 个币种")
        if removed_count > 0:
            parts.append(f"移除 {removed_count} 个币种")
        message = "、".join(parts)
        return self.send_notification(title, message, timeout=15)
    
    def notify_error(self, error_msg):
        title = "分析出错"
        return self.send_notification(title, error_msg[:100])
