"""
iQOO/OriginOS系统优化器
针对iQOO设备的特殊后台限制进行适配
"""

def optimize_for_iqoo():
    """iQOO系统优化"""
    try:
        from jnius import autoclass
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        activity = PythonActivity.mActivity
        
        print("[iQOO优化] 开始iQOO系统优化...")
        
        # 1. 请求忽略电池优化
        try:
            Intent = autoclass('android.content.Intent')
            Settings = autoclass('android.provider.Settings')
            Uri = autoclass('android.net.Uri')
            
            intent = Intent(Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS)
            intent.setData(Uri.parse("package:" + activity.getPackageName()))
            activity.startActivity(intent)
            print("[iQOO优化] 已请求忽略电池优化")
        except Exception as e:
            print(f"[iQOO优化] 请求忽略电池优化失败: {e}")
        
        # 2. 显示iQOO设置指导
        print("\n[iQOO优化] 为了确保息屏后正常运行，请手动设置：")
        print("=================================================")
        print("1. 电池优化设置：")
        print("   设置 → 电池 → 电池优化 → 选择'所有应用'")
        print("   找到'币安分析工具' → 选择'不限制'")
        print("")
        print("2. 自启动管理：")
        print("   i管家 → 应用管理 → 自启动")
        print("   找到'币安分析工具' → 开启自启动")
        print("")
        print("3. 后台高耗电：")
        print("   设置 → 电池 → 后台高耗电")
        print("   找到'币安分析工具' → 允许后台高耗电")
        print("")
        print("4. 后台冻结：")
        print("   i管家 → 应用管理 → 后台冻结")
        print("   找到'币安分析工具' → 关闭冻结")
        print("=================================================\n")
        
        return True
    except Exception as e:
        print(f"[iQOO优化] 失败: {e}")
        return False

def check_iqoo_restrictions():
    """检查iQOO限制状态"""
    try:
        from jnius import autoclass
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        Context = autoclass('android.content.Context')
        PowerManager = autoclass('android.os.PowerManager')
        
        activity = PythonActivity.mActivity
        power_manager = activity.getSystemService(Context.POWER_SERVICE)
        
        # 检查是否在电池优化白名单
        try:
            ignoring_optimizations = power_manager.isIgnoringBatteryOptimizations(
                activity.getPackageName()
            )
            print(f"[iQOO检查] 电池优化状态: {'已忽略' if ignoring_optimizations else '受限制'}")
            return ignoring_optimizations
        except:
            print(f"[iQOO检查] 无法检查电池优化状态")
            return False
    except Exception as e:
        print(f"[iQOO检查] 检查失败: {e}")
        return False

def show_iqoo_setup_guide():
    """显示iQOO设置指南（用于UI显示）"""
    guide_text = """
[b]iQOO/OriginOS 息屏运行设置指南[/b]

[color=333333]为了确保应用在息屏后正常运行，请按以下步骤设置：[/color]

[b][color=0066cc]第1步：电池优化设置[/color][/b]
[color=000000]设置 → 电池 → 电池优化 → 选择'所有应用'[/color]
[color=000000]找到'币安分析工具' → 选择'不限制'[/color]

[b][color=0066cc]第2步：自启动管理[/color][/b]  
[color=000000]i管家 → 应用管理 → 自启动[/color]
[color=000000]找到'币安分析工具' → 开启自启动[/color]

[b][color=0066cc]第3步：后台高耗电[/color][/b]
[color=000000]设置 → 电池 → 后台高耗电[/color]
[color=000000]找到'币安分析工具' → 允许后台高耗电[/color]

[b][color=0066cc]第4步：后台冻结[/color][/b]
[color=000000]i管家 → 应用管理 → 后台冻结[/color]
[color=000000]找到'币安分析工具' → 关闭冻结[/color]

[b][color=00aa00]完成以上设置后，应用将能在息屏状态下稳定运行[/color][/b]
"""
    return guide_text

def detect_device_brand():
    """检测设备品牌"""
    try:
        from jnius import autoclass
        Build = autoclass('android.os.Build')
        
        brand = Build.BRAND.lower()
        manufacturer = Build.MANUFACTURER.lower()
        
        print(f"[设备检测] 品牌: {brand}, 制造商: {manufacturer}")
        
        # 检测是否为iQOO/vivo
        if 'iqoo' in brand or 'vivo' in manufacturer:
            print("[设备检测] 检测到iQOO/Vivo设备")
            return 'iqoo'
        elif 'xiaomi' in brand or 'redmi' in brand:
            print("[设备检测] 检测到小米设备")
            return 'xiaomi'
        elif 'huawei' in brand or 'honor' in brand:
            print("[设备检测] 检测到华为/荣耀设备")
            return 'huawei'
        elif 'oppo' in brand:
            print("[设备检测] 检测到OPPO设备")
            return 'oppo'
        else:
            print(f"[设备检测] 其他品牌设备: {brand}")
            return 'other'
    except Exception as e:
        print(f"[设备检测] 检测失败: {e}")
        return 'unknown'

def apply_brand_specific_optimization():
    """根据设备品牌应用特定优化"""
    brand = detect_device_brand()
    
    if brand == 'iqoo':
        return optimize_for_iqoo()
    elif brand == 'xiaomi':
        print("[小米优化] 请在设置中允许自启动和后台运行")
        return True
    elif brand == 'huawei':
        print("[华为优化] 请在电池优化中选择'允许后台活动'")
        return True
    else:
        print("[通用优化] 请在系统设置中允许应用后台运行")
        return True
