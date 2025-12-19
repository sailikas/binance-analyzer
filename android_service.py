"""
Android后台服务入口
用于在Android系统中运行定时分析任务
支持WakeLock保持唤醒和前台服务保活
"""
import os
import sys
import time
import datetime

def acquire_wakelock():
    """获取WakeLock，防止系统休眠"""
    try:
        from jnius import autoclass
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        Context = autoclass('android.content.Context')
        PowerManager = autoclass('android.os.PowerManager')
        
        activity = PythonActivity.mActivity
        power_manager = activity.getSystemService(Context.POWER_SERVICE)
        
        # 创建WakeLock (PARTIAL_WAKE_LOCK: CPU保持运行，屏幕可以关闭)
        wake_lock = power_manager.newWakeLock(
            PowerManager.PARTIAL_WAKE_LOCK,
            'BinanceAnalyzer::ServiceWakeLock'
        )
        wake_lock.acquire()
        print(f"[Android服务] WakeLock已获取")
        return wake_lock
    except Exception as e:
        print(f"[Android服务] WakeLock获取失败: {e}")
        return None

def start_foreground_service():
    """启动前台服务，显示持久通知"""
    try:
        from jnius import autoclass
        
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        NotificationBuilder = autoclass('android.app.Notification$Builder')
        NotificationChannel = autoclass('android.app.NotificationChannel')
        NotificationManager = autoclass('android.app.NotificationManager')
        Context = autoclass('android.content.Context')
        Intent = autoclass('android.content.Intent')
        PendingIntent = autoclass('android.app.PendingIntent')
        
        activity = PythonActivity.mActivity
        notification_service = activity.getSystemService(Context.NOTIFICATION_SERVICE)
        
        # 创建前台服务通知渠道
        channel_id = "foreground_service_channel"
        channel_name = "后台服务"
        importance = NotificationManager.IMPORTANCE_LOW
        
        channel = NotificationChannel(channel_id, channel_name, importance)
        channel.setDescription("保持应用后台运行")
        notification_service.createNotificationChannel(channel)
        
        # 创建点击通知的Intent
        intent = Intent(activity, activity.getClass())
        intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP)
        
        try:
            pending_intent = PendingIntent.getActivity(
                activity, 0, intent,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE
            )
        except:
            pending_intent = PendingIntent.getActivity(
                activity, 0, intent, PendingIntent.FLAG_UPDATE_CURRENT
            )
        
        # 创建前台服务通知
        builder = NotificationBuilder(activity, channel_id)
        builder.setContentTitle("币安分析工具")
        builder.setContentText("后台服务运行中...")
        builder.setSmallIcon(activity.getApplicationInfo().icon)
        builder.setContentIntent(pending_intent)
        builder.setOngoing(True)  # 不可滑动删除
        
        notification = builder.build()
        
        # 启动前台服务 (通知ID使用999，避免与普通通知冲突)
        try:
            Service = autoclass('android.app.Service')
            # 注意：这里需要Service实例，但在PythonActivity中无法直接调用
            # 作为替代，我们直接显示持久通知
            notification_service.notify(999, notification)
            print(f"[Android服务] 前台服务通知已显示")
        except Exception as e:
            print(f"[Android服务] 前台服务启动失败: {e}")
            # 降级为普通持久通知
            notification_service.notify(999, notification)
        
        return True
    except Exception as e:
        print(f"[Android服务] 前台服务创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False

# 添加项目目录到Python路径
if __name__ == '__main__':
    # 获取应用的私有存储目录
    from jnius import autoclass
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    context = PythonActivity.mActivity
    
    # 设置工作目录
    files_dir = context.getFilesDir().getAbsolutePath()
    os.chdir(files_dir)
    
    print(f"[Android服务] 服务启动 - {datetime.datetime.now()}")
    print(f"[Android服务] 工作目录: {files_dir}")
    
    # 获取WakeLock保持唤醒
    wake_lock = acquire_wakelock()
    
    # 启动前台服务
    start_foreground_service()
    
    try:
        # 导入服务模块
        from service import get_service
        from config_manager import ConfigManager
        
        config_manager = ConfigManager()
        service = get_service()
        
        print(f"[Android服务] 服务实例创建完成")
        
        # 启动服务循环
        service.start_service()
        
        print(f"[Android服务] 进入服务循环...")
        
        # 保持服务运行
        while True:
            time.sleep(60)
            print(f"[Android服务] 心跳检查 - {datetime.datetime.now()}")
            
            # 检查服务是否还在运行
            if not service.is_running:
                print(f"[Android服务] 服务已停止,退出")
                break
    
    except Exception as e:
        print(f"[Android服务] 服务出错: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 释放WakeLock
        if wake_lock:
            try:
                wake_lock.release()
                print(f"[Android服务] WakeLock已释放")
            except:
                pass
