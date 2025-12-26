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
    """获取并保持WakeLock"""
    try:
        from jnius import autoclass
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        Context = autoclass('android.content.Context')
        PowerManager = autoclass('android.os.PowerManager')
        
        activity = PythonActivity.mActivity
        power_manager = activity.getSystemService(Context.POWER_SERVICE)
        
        # 使用ACQUIRE_CAUSES_WAKEUP + ON_AFTER_RELEASE标志增强WakeLock
        wake_lock = power_manager.newWakeLock(
            PowerManager.PARTIAL_WAKE_LOCK | PowerManager.ACQUIRE_CAUSES_WAKEUP | PowerManager.ON_AFTER_RELEASE,
            'BinanceAnalyzer::ServiceWakeLock'
        )
        # 设置10分钟超时，需要定期续期
        wake_lock.acquire(10*60*1000)  # 10分钟超时
        print(f"[Android服务] WakeLock已获取（10分钟超时）")
        return wake_lock
    except Exception as e:
        print(f"[Android服务] WakeLock获取失败: {e}")
        return None

def renew_wakelock(wake_lock):
    """定期续期WakeLock"""
    if wake_lock:
        try:
            if hasattr(wake_lock, 'isHeld') and wake_lock.isHeld():
                # 先释放再重新获取
                wake_lock.release()
            wake_lock.acquire(10*60*1000)  # 续期10分钟
            print(f"[Android服务] WakeLock已续期")
            return True
        except Exception as e:
            print(f"[Android服务] WakeLock续期失败: {e}")
            return False
    return False

def heartbeat_loop(wake_lock):
    """保活心跳循环 - 防止iQOO系统杀死进程"""
    import time
    import datetime
    
    last_wakelock_renew = datetime.datetime.now()
    wakelock_interval = 300  # 5分钟续期一次WakeLock
    heartbeat_count = 0
    
    print(f"[保活心跳] 心跳循环已启动")
    
    while True:
        try:
            now = datetime.datetime.now()
            heartbeat_count += 1
            
            # 定期续期WakeLock
            if (now - last_wakelock_renew).total_seconds() >= wakelock_interval:
                renew_wakelock(wake_lock)
                last_wakelock_renew = now
            
            # iQOO专用：轻微CPU活动防止被判定为"无活动"
            # 这个计算量很小，但能保持CPU活跃
            dummy_sum = sum(range(1000))
            
            # 每30秒一次心跳
            if heartbeat_count % 2 == 0:  # 每分钟打印一次
                print(f"[保活心跳] 心跳 #{heartbeat_count} - {now.strftime('%H:%M:%S')}")
            
            time.sleep(30)
            
        except Exception as e:
            print(f"[保活心跳] 心跳异常: {e}")
            time.sleep(30)

def start_foreground_service():
    """启动真正的前台服务"""
    try:
        from jnius import autoclass
        
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        Service = autoclass('android.app.Service')
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
        channel_name = "后台分析服务"
        importance = NotificationManager.IMPORTANCE_LOW
        
        channel = NotificationChannel(channel_id, channel_name, importance)
        channel.setDescription("保持币安分析工具后台运行")
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
        builder.setContentText("后台服务运行中，定时分析进行中...")
        builder.setSmallIcon(activity.getApplicationInfo().icon)
        builder.setContentIntent(pending_intent)
        builder.setOngoing(True)  # 不可滑动删除
        
        notification = builder.build()
        
        # 关键修复：真正启动前台服务
        try:
            # 在Android Service模式下，PythonActivity就是Service实例
            # 使用startForeground()方法真正启动前台服务
            activity.startForeground(999, notification)
            print(f"[Android服务] 真正的前台服务已启动")
            return True
        except Exception as e:
            print(f"[Android服务] startForeground调用失败: {e}")
            # 降级：显示持久通知
            notification_service.notify(999, notification)
            print(f"[Android服务] 降级为持久通知")
            return False
        
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
        
        # 启动保活心跳线程
        import threading
        heartbeat_thread = threading.Thread(target=heartbeat_loop, args=(wake_lock,), daemon=True)
        heartbeat_thread.start()
        print(f"[Android服务] 保活心跳线程已启动")
        
        # 启动服务循环
        service.start_service()
        
        print(f"[Android服务] 进入主服务循环...")
        
        # 保持服务运行
        while True:
            time.sleep(60)
            print(f"[Android服务] 主循环心跳 - {datetime.datetime.now()}")
            
            # 检查服务是否还在运行
            if not service.is_running:
                print(f"[Android服务] 分析服务已停止，重启")
                service.start_service()
    
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
