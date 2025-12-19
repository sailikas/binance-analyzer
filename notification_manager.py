"""
通知管理模块
"""
import sys

try:
    from plyer import notification
    PLYER_AVAILABLE = True
except ImportError:
    PLYER_AVAILABLE = False
    print("警告: plyer 未安装，通知功能不可用")

from config_manager import ConfigManager

class NotificationManager:
    def __init__(self):
        self.app_name = "币安分析工具"
        self.config_manager = ConfigManager()
        self.channel_created = False
    
    def _create_notification_channel(self):
        """为Android 8.0+创建通知渠道"""
        if self.channel_created:
            return True
        
        try:
            from jnius import autoclass
            
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            NotificationChannel = autoclass('android.app.NotificationChannel')
            NotificationManager = autoclass('android.app.NotificationManager')
            Context = autoclass('android.content.Context')
            
            activity = PythonActivity.mActivity
            notification_service = activity.getSystemService(Context.NOTIFICATION_SERVICE)
            
            # 创建通知渠道
            channel_id = "binance_analyzer_channel"
            channel_name = "币安分析通知"
            importance = NotificationManager.IMPORTANCE_HIGH
            
            channel = NotificationChannel(channel_id, channel_name, importance)
            channel.setDescription("币安合约分析结果通知")
            channel.enableVibration(True)
            channel.enableLights(True)
            
            notification_service.createNotificationChannel(channel)
            self.channel_created = True
            print(f"[通知] 通知渠道创建成功")
            return True
        except Exception as e:
            print(f"[通知] 创建通知渠道失败: {e}")
            return False
    
    def _send_android_native(self, title, message):
        """发送Android原生通知(支持Android 13+)，包含时间和点击跳转"""
        try:
            from jnius import autoclass, cast
            from datetime import datetime
            
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            NotificationBuilder = autoclass('android.app.Notification$Builder')
            NotificationManager = autoclass('android.app.NotificationManager')
            Context = autoclass('android.content.Context')
            Intent = autoclass('android.content.Intent')
            PendingIntent = autoclass('android.app.PendingIntent')
            
            activity = PythonActivity.mActivity
            notification_service = cast(NotificationManager, 
                activity.getSystemService(Context.NOTIFICATION_SERVICE))
            
            # 为Android 8.0+创建通知渠道
            self._create_notification_channel()
            
            # 创建点击通知时的Intent（跳转到应用主界面）
            intent = Intent(activity, activity.getClass())
            intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP)
            intent.putExtra("notification_action", "open_results")  # 传递参数，可用于跳转到结果页面
            
            # 创建PendingIntent
            try:
                # Android 12+ 需要设置 FLAG_IMMUTABLE
                pending_intent = PendingIntent.getActivity(
                    activity, 
                    0, 
                    intent, 
                    PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE
                )
            except:
                # 兼容旧版本
                pending_intent = PendingIntent.getActivity(
                    activity, 
                    0, 
                    intent, 
                    PendingIntent.FLAG_UPDATE_CURRENT
                )
            
            # 在消息中添加时间
            current_time = datetime.now().strftime("%H:%M:%S")
            message_with_time = f"[{current_time}] {message}"
            
            # 创建通知
            channel_id = "binance_analyzer_channel"
            builder = NotificationBuilder(activity, channel_id)
            builder.setContentTitle(title)
            builder.setContentText(message_with_time)
            builder.setSmallIcon(activity.getApplicationInfo().icon)
            builder.setAutoCancel(True)
            builder.setContentIntent(pending_intent)  # 设置点击Intent
            builder.setWhen(int(datetime.now().timestamp() * 1000))  # 设置通知时间戳
            builder.setShowWhen(True)  # 显示时间
            
            # Android 8.0+需要设置优先级
            try:
                NotificationCompat = autoclass('androidx.core.app.NotificationCompat')
                builder.setPriority(NotificationCompat.PRIORITY_HIGH)
            except:
                pass
            
            notification_service.notify(1, builder.build())
            print(f"[通知] Android原生通知发送成功 (时间: {current_time})")
            return True
        except Exception as e:
            print(f"[通知] Android原生通知失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _send_plyer(self, title, message, timeout=10):
        """使用plyer发送通知"""
        if not PLYER_AVAILABLE:
            print(f"[通知] plyer不可用")
            return False
        
        try:
            notification.notify(
                title=title,
                message=message,
                app_name=self.app_name,
                timeout=timeout
            )
            print(f"[通知] plyer通知发送成功")
            return True
        except Exception as e:
            print(f"[通知] plyer发送失败: {e}")
            return False
    
    def _send_serverchan(self, title, message):
        """使用Server酱发送通知"""
        try:
            if not self.config_manager.get("serverchan_enabled", True):
                print(f"[通知] Server酱未启用")
                return False
            
            sendkey = self.config_manager.get("serverchan_key", "")
            if not sendkey:
                print(f"[通知] Server酱SendKey未配置")
                return False
            
            import requests
            url = f"https://sctapi.ftqq.com/{sendkey}.send"
            data = {
                "title": title,
                "desp": message
            }
            
            response = requests.post(url, data=data, timeout=10)
            if response.status_code == 200:
                result = response.json()
                if result.get("code") == 0:
                    print(f"[通知] Server酱发送成功")
                    return True
                else:
                    print(f"[通知] Server酱返回错误: {result.get('message')}")
                    return False
            else:
                print(f"[通知] Server酱HTTP错误: {response.status_code}")
                return False
        except Exception as e:
            print(f"[通知] Server酱发送失败: {e}")
            return False
    
    def send_notification(self, title, message, timeout=10):
        """发送通知,同时尝试所有通知方式"""
        print(f"[通知] 准备发送: {title} - {message}")
        
        import platform
        is_android = platform.system() == 'Linux' and hasattr(sys, 'getandroidapilevel')
        
        success_count = 0
        
        # 尝试所有通知方式,不要提前返回
        if is_android:
            # Android环境: 尝试原生和plyer
            if self._send_android_native(title, message):
                success_count += 1
            if self._send_plyer(title, message, timeout):
                success_count += 1
        else:
            # Windows/桌面环境: 尝试plyer
            if self._send_plyer(title, message, timeout):
                success_count += 1
        
        # 总是尝试Server酱(如果启用)
        if self._send_serverchan(title, message):
            success_count += 1
        
        if success_count > 0:
            print(f"[通知] 成功发送 {success_count} 种通知")
            return True
        else:
            print(f"[通知] 所有通知方式均失败")
            return False
    
    def notify_analysis_complete(self, symbol_count, results=None):
        title = self.config_manager.get("serverchan_title", "分析完成")
        message_template = self.config_manager.get("serverchan_content", "找到 {count} 个符合条件的交易对")
        message = message_template.replace("{count}", str(symbol_count))
        
        # 如果有结果数据,添加前3个币种的详细信息
        if results and len(results) > 0:
            message += "\n\n【前3名币种】"
            for i, r in enumerate(results[:3], 1):
                gain_1d = r.get('gain_1d', 0) * 100
                gain_2d = r.get('gain_2d', 0) * 100
                gain_3d = r.get('gain_3d', 0) * 100
                message += f"\n{i}. {r['symbol']}"
                message += f"\n   1日: {gain_1d:+.2f}% | 2日: {gain_2d:+.2f}% | 3日: {gain_3d:+.2f}%"
        
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
    
    def notify_zero_result(self, previous_count):
        """当从有结果变成0结果时发送通知"""
        title = "匹配结果清零"
        message = f"之前有 {previous_count} 个币种符合条件，现在已全部不符合条件"
        return self.send_notification(title, message, timeout=15)
    
    def notify_error(self, error_msg):
        title = "分析出错"
        return self.send_notification(title, error_msg[:100])
    
    def notify_zero_result(self, previous_count):
        """发送匹配数量变为0的通知"""
        title = "匹配数量清零"
        message = f"之前有 {previous_count} 个币种符合条件\n现在匹配数量已降为 0"
        return self.send_notification(title, message, timeout=15)
