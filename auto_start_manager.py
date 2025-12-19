"""
自启动和电池优化管理模块
处理应用被杀死后的自启动、电池优化白名单等
"""
import sys


class AutoStartManager:
    """管理自启动和电池优化相关功能"""
    
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
            PowerManager = autoclass('android.os.PowerManager')
            Context = autoclass('android.content.Context')
            Uri = autoclass('android.net.Uri')
            
            activity = PythonActivity.mActivity
            power_manager = activity.getSystemService(Context.POWER_SERVICE)
            package_name = activity.getPackageName()
            
            # 检查是否已在白名单中
            if power_manager.isIgnoringBatteryOptimizations(package_name):
                print("[电池优化] 应用已在电池优化白名单中")
                return True
            
            # 请求加入白名单
            print("[电池优化] 请求加入电池优化白名单...")
            intent = Intent()
            intent.setAction(Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS)
            intent.setData(Uri.parse(f"package:{package_name}"))
            activity.startActivity(intent)
            
            print("[电池优化] 已打开电池优化设置页面，请手动允许")
            return True
            
        except Exception as e:
            print(f"[电池优化] 请求失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def open_battery_settings(self):
        """打开电池设置页面（兼容方案）"""
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
            
            # 尝试打开应用详情页（电池设置）
            intent = Intent()
            intent.setAction(Settings.ACTION_APPLICATION_DETAILS_SETTINGS)
            intent.setData(Uri.parse(f"package:{package_name}"))
            activity.startActivity(intent)
            
            print("[电池设置] 已打开应用详情页，请手动设置电池为'不限制'")
            return True
            
        except Exception as e:
            print(f"[电池设置] 打开失败: {e}")
            return False
    
    def open_autostart_settings(self):
        """打开自启动设置页面（各厂商通用）"""
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
            
            # 各厂商的自启动设置Intent
            autostart_intents = self._get_autostart_intents(manufacturer)
            
            # 尝试打开自启动设置
            for intent_info in autostart_intents:
                try:
                    intent = Intent()
                    intent.setComponent(ComponentName(
                        intent_info['package'],
                        intent_info['class']
                    ))
                    intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                    activity.startActivity(intent)
                    print(f"[自启动] 已打开{manufacturer}自启动设置页面")
                    return True
                except Exception as e:
                    print(f"[自启动] 尝试打开 {intent_info['package']} 失败: {e}")
                    continue
            
            # 如果所有尝试都失败，打开应用详情页
            print("[自启动] 无法直接打开自启动设置，打开应用详情页")
            return self.open_battery_settings()
            
        except Exception as e:
            print(f"[自启动] 打开失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _get_manufacturer(self):
        """获取设备厂商"""
        try:
            from jnius import autoclass
            Build = autoclass('android.os.Build')
            manufacturer = Build.MANUFACTURER.lower()
            return manufacturer
        except:
            return "unknown"
    
    def _get_autostart_intents(self, manufacturer):
        """获取各厂商的自启动设置Intent"""
        intents = {
            "xiaomi": [
                {
                    'package': 'com.miui.securitycenter',
                    'class': 'com.miui.permcenter.autostart.AutoStartManagementActivity'
                },
                {
                    'package': 'com.miui.securitycenter',
                    'class': 'com.miui.powercenter.PowerSettings'
                }
            ],
            "huawei": [
                {
                    'package': 'com.huawei.systemmanager',
                    'class': 'com.huawei.systemmanager.startupmgr.ui.StartupNormalAppListActivity'
                },
                {
                    'package': 'com.huawei.systemmanager',
                    'class': 'com.huawei.systemmanager.appcontrol.activity.StartupAppControlActivity'
                }
            ],
            "honor": [
                {
                    'package': 'com.huawei.systemmanager',
                    'class': 'com.huawei.systemmanager.startupmgr.ui.StartupNormalAppListActivity'
                }
            ],
            "oppo": [
                {
                    'package': 'com.coloros.safecenter',
                    'class': 'com.coloros.safecenter.permission.startup.StartupAppListActivity'
                },
                {
                    'package': 'com.oppo.safe',
                    'class': 'com.oppo.safe.permission.startup.StartupAppListActivity'
                }
            ],
            "vivo": [
                {
                    'package': 'com.vivo.permissionmanager',
                    'class': 'com.vivo.permissionmanager.activity.BgStartUpManagerActivity'
                },
                {
                    'package': 'com.iqoo.secure',
                    'class': 'com.iqoo.secure.ui.phoneoptimize.AddWhiteListActivity'
                }
            ],
            "samsung": [
                {
                    'package': 'com.samsung.android.lool',
                    'class': 'com.samsung.android.sm.ui.battery.BatteryActivity'
                }
            ],
            "oneplus": [
                {
                    'package': 'com.oneplus.security',
                    'class': 'com.oneplus.security.chainlaunch.view.ChainLaunchAppListActivity'
                }
            ]
        }
        
        return intents.get(manufacturer, [])
    
    def check_battery_optimization_status(self):
        """检查电池优化状态"""
        if not self.is_android:
            return None
        
        try:
            from jnius import autoclass
            
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            PowerManager = autoclass('android.os.PowerManager')
            Context = autoclass('android.content.Context')
            
            activity = PythonActivity.mActivity
            power_manager = activity.getSystemService(Context.POWER_SERVICE)
            package_name = activity.getPackageName()
            
            is_ignored = power_manager.isIgnoringBatteryOptimizations(package_name)
            
            if is_ignored:
                print("[电池优化] 状态: 已忽略电池优化 ✅")
            else:
                print("[电池优化] 状态: 受电池优化限制 ⚠️")
            
            return is_ignored
            
        except Exception as e:
            print(f"[电池优化] 状态检查失败: {e}")
            return None
    
    def show_setup_guide(self):
        """显示设置指南"""
        manufacturer = self._get_manufacturer() if self.is_android else "unknown"
        
        guides = {
            "xiaomi": """
【小米/红米设置指南】
1. 自启动管理：设置 → 应用设置 → 应用管理 → 币安分析工具 → 自启动 → 开启
2. 省电策略：设置 → 应用设置 → 应用管理 → 币安分析工具 → 省电策略 → 无限制
3. 后台弹出界面：设置 → 应用设置 → 应用管理 → 币安分析工具 → 后台弹出界面 → 允许
4. 锁屏显示：设置 → 应用设置 → 应用管理 → 币安分析工具 → 锁屏显示 → 允许
            """,
            "huawei": """
【华为/荣耀设置指南】
1. 自启动管理：设置 → 应用 → 应用启动管理 → 币安分析工具 → 手动管理 → 全部开启
2. 电池优化：设置 → 电池 → 应用启动管理 → 币安分析工具 → 手动管理 → 允许后台活动
3. 忽略电池优化：设置 → 电池 → 更多电池设置 → 休眠时始终保持网络连接
            """,
            "oppo": """
【OPPO设置指南】
1. 自启动管理：设置 → 应用管理 → 应用列表 → 币安分析工具 → 自启动 → 允许
2. 后台冻结：设置 → 电池 → 应用耗电管理 → 币安分析工具 → 允许后台运行
3. 后台运行：设置 → 应用管理 → 应用列表 → 币安分析工具 → 后台运行 → 允许
            """,
            "vivo": """
【vivo/iQOO设置指南】
1. 自启动管理：i管家 → 应用管理 → 自启动 → 币安分析工具 → 开启
2. 后台高耗电：设置 → 电池 → 后台高耗电 → 币安分析工具 → 允许
3. 后台运行：i管家 → 应用管理 → 权限管理 → 自启动 → 币安分析工具 → 允许
            """,
            "samsung": """
【三星设置指南】
1. 电池优化：设置 → 应用程序 → 币安分析工具 → 电池 → 优化电池使用 → 关闭
2. 后台运行：设置 → 应用程序 → 币安分析工具 → 电池 → 后台限制 → 不限制
3. 休眠应用：设置 → 电池和设备维护 → 电池 → 后台使用限制 → 从不休眠应用 → 添加币安分析工具
            """,
            "oneplus": """
【一加设置指南】
1. 自启动管理：设置 → 应用管理 → 币安分析工具 → 自启动 → 允许
2. 电池优化：设置 → 电池 → 电池优化 → 币安分析工具 → 不优化
3. 后台运行：设置 → 应用管理 → 币安分析工具 → 高级 → 后台运行 → 允许
            """
        }
        
        guide = guides.get(manufacturer, """
【通用设置指南】
1. 自启动：在系统设置中搜索"自启动"，找到币安分析工具并允许
2. 电池优化：设置 → 电池 → 电池优化 → 币安分析工具 → 不优化
3. 后台运行：设置 → 应用管理 → 币安分析工具 → 允许后台运行
        """)
        
        print(f"\n{'='*50}")
        print(f"设备厂商: {manufacturer.upper()}")
        print(guide)
        print(f"{'='*50}\n")
        
        return guide


# 单例模式
_auto_start_manager_instance = None

def get_auto_start_manager():
    """获取AutoStartManager单例"""
    global _auto_start_manager_instance
    if _auto_start_manager_instance is None:
        _auto_start_manager_instance = AutoStartManager()
    return _auto_start_manager_instance
