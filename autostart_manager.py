"""
自启动和电池优化管理模块
处理应用被杀死后的自启动和电池优化白名单
"""
import sys

class AutostartManager:
    def __init__(self):
        self.is_android = self._check_android()
    
    def _check_android(self):
        """检查是否为Android平台"""
        try:
            import platform
            return platform.system() == 'Linux' and hasattr(sys, 'getandroidapilevel')
        except:
            return False
    
    def request_battery_optimization_exemption(self):
        """请求忽略电池优化（加入白名单）"""
        if not self.is_android:
            print("[电池优化] 非Android平台，跳过")
            return False
        
        try:
            from jnius import autoclass
            
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            Intent = autoclass('android.content.Intent')
            Settings = autoclass('android.provider.Settings')
            Uri = autoclass('android.net.Uri')
            PowerManager = autoclass('android.os.PowerManager')
            Context = autoclass('android.content.Context')
            
            activity = PythonActivity.mActivity
            package_name = activity.getPackageName()
            
            # 检查是否已在白名单中
            power_manager = activity.getSystemService(Context.POWER_SERVICE)
            is_ignoring = power_manager.isIgnoringBatteryOptimizations(package_name)
            
            if is_ignoring:
                print("[电池优化] 应用已在白名单中")
                return True
            
            # 请求加入白名单
            print("[电池优化] 请求忽略电池优化...")
            intent = Intent()
            intent.setAction(Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS)
            intent.setData(Uri.parse(f"package:{package_name}"))
            activity.startActivity(intent)
            
            print("[电池优化] 已打开设置页面，请手动允许")
            return True
            
        except Exception as e:
            print(f"[电池优化] 请求失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def open_battery_settings(self):
        """打开电池设置页面（通用方法）"""
        if not self.is_android:
            print("[电池设置] 非Android平台，跳过")
            return False
        
        try:
            from jnius import autoclass
            
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            Intent = autoclass('android.content.Intent')
            Settings = autoclass('android.provider.Settings')
            Uri = autoclass('android.net.Uri')
            
            activity = PythonActivity.mActivity
            package_name = activity.getPackageName()
            
            # 尝试打开应用详情页面
            intent = Intent()
            intent.setAction(Settings.ACTION_APPLICATION_DETAILS_SETTINGS)
            intent.setData(Uri.parse(f"package:{package_name}"))
            activity.startActivity(intent)
            
            print("[电池设置] 已打开应用设置页面")
            print("[提示] 请手动进入'电池'或'省电策略'设置")
            return True
            
        except Exception as e:
            print(f"[电池设置] 打开失败: {e}")
            return False
    
    def open_autostart_settings(self):
        """尝试打开自启动设置页面（各厂商不同）"""
        if not self.is_android:
            print("[自启动] 非Android平台，跳过")
            return False
        
        try:
            from jnius import autoclass
            
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            Intent = autoclass('android.content.Intent')
            ComponentName = autoclass('android.content.ComponentName')
            
            activity = PythonActivity.mActivity
            manufacturer = self._get_manufacturer()
            
            print(f"[自启动] 检测到设备厂商: {manufacturer}")
            
            # 不同厂商的自启动设置页面
            autostart_intents = {
                'xiaomi': [
                    ('com.miui.securitycenter', 'com.miui.permcenter.autostart.AutoStartManagementActivity'),
                    ('com.miui.securitycenter', 'com.miui.powercenter.PowerSettings')
                ],
                'huawei': [
                    ('com.huawei.systemmanager', 'com.huawei.systemmanager.startupmgr.ui.StartupNormalAppListActivity'),
                    ('com.huawei.systemmanager', 'com.huawei.systemmanager.optimize.process.ProtectActivity')
                ],
                'oppo': [
                    ('com.coloros.safecenter', 'com.coloros.safecenter.permission.startup.StartupAppListActivity'),
                    ('com.oppo.safe', 'com.oppo.safe.permission.startup.StartupAppListActivity')
                ],
                'vivo': [
                    ('com.vivo.permissionmanager', 'com.vivo.permissionmanager.activity.BgStartUpManagerActivity'),
                    ('com.iqoo.secure', 'com.iqoo.secure.ui.phoneoptimize.AddWhiteListActivity')
                ],
                'samsung': [
                    ('com.samsung.android.lool', 'com.samsung.android.sm.ui.battery.BatteryActivity')
                ],
                'oneplus': [
                    ('com.oneplus.security', 'com.oneplus.security.chainlaunch.view.ChainLaunchAppListActivity')
                ]
            }
            
            # 尝试打开对应厂商的设置页面
            intents_to_try = autostart_intents.get(manufacturer.lower(), [])
            
            for package, activity_name in intents_to_try:
                try:
                    intent = Intent()
                    intent.setComponent(ComponentName(package, activity_name))
                    activity.startActivity(intent)
                    print(f"[自启动] 成功打开 {manufacturer} 自启动设置")
                    return True
                except:
                    continue
            
            # 如果没有找到特定厂商的设置，打开应用详情
            print(f"[自启动] 未找到 {manufacturer} 的自启动设置，打开应用详情")
            self.open_battery_settings()
            return False
            
        except Exception as e:
            print(f"[自启动] 打开设置失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _get_manufacturer(self):
        """获取设备厂商"""
        try:
            from jnius import autoclass
            Build = autoclass('android.os.Build')
            manufacturer = Build.MANUFACTURER
            return manufacturer if manufacturer else "unknown"
        except:
            return "unknown"
    
    def check_battery_optimization_status(self):
        """检查电池优化状态"""
        if not self.is_android:
            return None
        
        try:
            from jnius import autoclass
            
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            Context = autoclass('android.content.Context')
            PowerManager = autoclass('android.os.PowerManager')
            
            activity = PythonActivity.mActivity
            package_name = activity.getPackageName()
            power_manager = activity.getSystemService(Context.POWER_SERVICE)
            
            is_ignoring = power_manager.isIgnoringBatteryOptimizations(package_name)
            
            status = "已忽略" if is_ignoring else "未忽略"
            print(f"[电池优化] 当前状态: {status}")
            return is_ignoring
            
        except Exception as e:
            print(f"[电池优化] 状态检查失败: {e}")
            return None
    
    def show_optimization_guide(self):
        """显示各厂商电池优化和自启动设置指南"""
        manufacturer = self._get_manufacturer().lower()
        
        guides = {
            'xiaomi': """
【小米/红米手机设置指南】
1. 自启动管理：
   设置 → 应用设置 → 应用管理 → 币安分析工具 → 自启动 → 开启
   
2. 省电策略：
   设置 → 应用设置 → 应用管理 → 币安分析工具 → 省电策略 → 无限制
   
3. 后台锁定：
   最近任务 → 长按应用卡片 → 点击锁定图标
            """,
            'huawei': """
【华为/荣耀手机设置指南】
1. 自启动管理：
   设置 → 应用 → 应用启动管理 → 币安分析工具 → 手动管理 → 全部开启
   
2. 电池优化：
   设置 → 电池 → 应用启动管理 → 币安分析工具 → 允许后台活动
   
3. 后台运行：
   设置 → 电池 → 更多电池设置 → 休眠时始终保持网络连接
            """,
            'oppo': """
【OPPO手机设置指南】
1. 自启动管理：
   设置 → 应用管理 → 应用列表 → 币安分析工具 → 自启动 → 开启
   
2. 后台冻结：
   设置 → 电池 → 应用耗电管理 → 币安分析工具 → 允许后台运行
   
3. 省电模式：
   设置 → 电池 → 高耗电应用 → 币安分析工具 → 允许
            """,
            'vivo': """
【vivo/iQOO手机设置指南】
1. 自启动管理：
   i管家 → 应用管理 → 权限管理 → 自启动 → 币安分析工具 → 开启
   
2. 后台高耗电：
   i管家 → 省电管理 → 后台高耗电 → 币安分析工具 → 允许
   
3. 后台冻结：
   设置 → 电池 → 后台耗电管理 → 币安分析工具 → 允许后台高耗电
            """,
            'samsung': """
【三星手机设置指南】
1. 电池优化：
   设置 → 应用程序 → 币安分析工具 → 电池 → 优化电池用量 → 关闭
   
2. 后台限制：
   设置 → 应用程序 → 币安分析工具 → 电池 → 后台限制 → 取消限制
   
3. 休眠应用：
   设置 → 电池和设备维护 → 电池 → 后台使用限制 → 从不休眠应用中添加
            """,
            'oneplus': """
【一加手机设置指南】
1. 自启动管理：
   设置 → 应用管理 → 币安分析工具 → 自启动 → 开启
   
2. 电池优化：
   设置 → 电池 → 电池优化 → 币安分析工具 → 不优化
   
3. 后台运行：
   设置 → 应用管理 → 币安分析工具 → 电池使用 → 不限制
            """
        }
        
        guide = guides.get(manufacturer, """
【通用设置指南】
请在手机设置中进行以下操作：

1. 关闭电池优化：
   设置 → 应用管理 → 币安分析工具 → 电池 → 不优化/无限制

2. 允许自启动：
   设置 → 应用管理 → 币安分析工具 → 自启动 → 开启

3. 允许后台运行：
   设置 → 应用管理 → 币安分析工具 → 后台运行 → 允许

4. 锁定后台：
   最近任务 → 找到应用 → 下拉/长按 → 锁定
        """)
        
        print(guide)
        return guide


# 全局单例
_autostart_manager = None

def get_autostart_manager():
    """获取自启动管理器单例"""
    global _autostart_manager
    if _autostart_manager is None:
        _autostart_manager = AutostartManager()
    return _autostart_manager
