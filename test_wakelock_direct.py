"""
测试直接WakeLock获取
"""
import platform

def test_direct_wakelock():
    """测试直接获取WakeLock"""
    if platform != 'android':
        print("非Android平台，跳过测试")
        return
    
    try:
        from jnius import autoclass
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        Context = autoclass('android.content.Context')
        PowerManager = autoclass('android.os.PowerManager')
        
        activity = PythonActivity.mActivity
        power_manager = activity.getSystemService(Context.POWER_SERVICE)
        
        wake_lock = power_manager.newWakeLock(
            PowerManager.PARTIAL_WAKE_LOCK | PowerManager.ACQUIRE_CAUSES_WAKEUP | PowerManager.ON_AFTER_RELEASE,
            'BinanceAnalyzer::TestWakeLock'
        )
        
        wake_lock.acquire(10*60*1000)  # 10分钟超时
        print("✓ 直接获取WakeLock成功")
        
        # 测试续期
        wake_lock.release()
        wake_lock.acquire(10*60*1000)
        print("✓ WakeLock续期成功")
        
        # 释放
        wake_lock.release()
        print("✓ WakeLock已释放")
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")

if __name__ == "__main__":
    print(f"平台: {platform}")
    test_direct_wakelock()