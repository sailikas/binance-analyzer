"""
后台启动器 - 用于启动应用但不显示UI
适用于Android 13+和iQOO设备
"""
import sys
import os


def start_background_service():
    """启动后台服务，不显示主界面"""
    print("[后台启动器] 正在启动后台服务...")
    
    try:
        # 导入必要模块
        from service import get_service
        from config_manager import ConfigManager
        from notification_manager import NotificationManager
        
        # 初始化配置
        config_manager = ConfigManager()
        notif_manager = NotificationManager()
        
        # 检查是否启用定时任务
        if not config_manager.get("schedule_enabled", False):
            print("[后台启动器] 定时任务未启用，退出")
            return False
        
        # 获取并启动服务
        service = get_service()
        service.start_service()
        
        print("[后台启动器] 后台服务已启动")
        
        # 发送启动通知
        notif_manager.send_notification(
            "后台服务已启动",
            "币安分析工具正在后台运行",
            timeout=5
        )
        
        # 保持运行
        import time
        while True:
            time.sleep(60)
            if not service.is_running:
                print("[后台启动器] 服务已停止")
                break
        
        return True
        
    except Exception as e:
        print(f"[后台启动器] 启动失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_and_acquire_wakelock():
    """检查并获取WakeLock"""
    try:
        from jnius import autoclass
        
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        Context = autoclass('android.content.Context')
        PowerManager = autoclass('android.os.PowerManager')
        
        activity = PythonActivity.mActivity
        power_manager = activity.getSystemService(Context.POWER_SERVICE)
        
        wake_lock = power_manager.newWakeLock(
            PowerManager.PARTIAL_WAKE_LOCK,
            'BinanceAnalyzer::BackgroundWakeLock'
        )
        wake_lock.acquire()
        
        print("[后台启动器] WakeLock已获取")
        return wake_lock
        
    except Exception as e:
        print(f"[后台启动器] WakeLock获取失败: {e}")
        return None


if __name__ == '__main__':
    print("[后台启动器] ========== 后台模式启动 ==========")
    
    # 获取WakeLock
    wake_lock = check_and_acquire_wakelock()
    
    try:
        # 启动后台服务
        start_background_service()
    finally:
        # 释放WakeLock
        if wake_lock:
            try:
                wake_lock.release()
                print("[后台启动器] WakeLock已释放")
            except:
                pass
