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
        print(f"[通知] 准备发送: {title} - {message}")
        
        if not PLYER_AVAILABLE:
            print(f"[通知] plyer不可用,仅打印日志")
            return False
        
        try:
            # 尝试使用plyer发送通知
            notification.notify(
                title=title,
                message=message,
                app_name=self.app_name,
                timeout=timeout
            )
            print(f"[通知] 发送成功")
            return True
        except Exception as e:
            print(f"[通知] plyer发送失败: {e}")
            
            # 尝试Android原生通知
            try:
                from android.runnable import run_on_ui_thread
                from jnius import autoclass, cast
                
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                NotificationBuilder = autoclass('android.app.Notification$Builder')
                NotificationManager = autoclass('android.app.NotificationManager')
                Context = autoclass('android.content.Context')
                
                activity = PythonActivity.mActivity
                notification_service = cast(NotificationManager, 
                    activity.getSystemService(Context.NOTIFICATION_SERVICE))
                
                builder = NotificationBuilder(activity)
                builder.setContentTitle(title)
                builder.setContentText(message)
                builder.setSmallIcon(activity.getApplicationInfo().icon)
                
                notification_service.notify(1, builder.build())
                print(f"[通知] Android原生通知发送成功")
                return True
            except Exception as e2:
                print(f"[通知] Android原生通知也失败: {e2}")
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
