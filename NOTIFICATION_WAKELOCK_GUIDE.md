# 通知增强和后台保活功能说明

## 📱 新增功能概览

### 1. 通知时间显示
- **功能**: 每条通知显示精确的发送时间（HH:MM:SS格式）
- **示例**: `[14:30:25] 找到 15 个符合条件的交易对`
- **用途**: 方便用户了解分析的准确时间

### 2. 点击通知跳转
- **功能**: 点击通知自动打开应用并跳转到结果页面
- **实现**: 使用PendingIntent + Intent Extra传递参数
- **体验**: 无需手动导航，直达分析结果

### 3. WakeLock后台保活
- **功能**: 使用PARTIAL_WAKE_LOCK保持CPU运行
- **效果**: 
  - ✅ 应用在后台时继续运行
  - ✅ 锁屏状态下定时任务正常执行
  - ✅ 屏幕关闭不影响分析任务
- **电量**: 仅保持CPU运行，屏幕可关闭，电量消耗较低

### 4. 前台服务通知
- **功能**: 显示持久通知表明后台服务运行中
- **效果**:
  - ✅ 防止系统杀死应用进程
  - ✅ 提高后台服务稳定性
  - ✅ 用户可见应用运行状态
- **通知ID**: 999（与普通通知分离）

### 5. 智能通知逻辑
- **功能**: 避免无意义的0结果通知
- **逻辑**:
  - ❌ 匹配数量为0时 **不发送通知**
  - ✅ 从有结果变为0时 **发送特殊通知**（"匹配结果清零"）
  - ✅ 有结果时正常发送通知
- **示例**:
  - 第1次分析：找到15个币种 → 发送通知 ✅
  - 第2次分析：找到12个币种 → 发送通知 ✅
  - 第3次分析：找到0个币种 → 发送"匹配结果清零"通知 ✅
  - 第4次分析：找到0个币种 → 不发送通知 ❌
  - 第5次分析：找到3个币种 → 发送通知 ✅

---

## 🔧 技术实现细节

### 通知时间显示

**实现位置**: `notification_manager.py` → `_send_android_native()`

```python
from datetime import datetime

# 在消息中添加时间
current_time = datetime.now().strftime("%H:%M:%S")
message_with_time = f"[{current_time}] {message}"

# 设置通知时间戳
builder.setWhen(int(datetime.now().timestamp() * 1000))
builder.setShowWhen(True)
```

**关键API**:
- `setWhen()`: 设置通知时间戳（毫秒）
- `setShowWhen(True)`: 显示时间

---

### 点击通知跳转

**实现位置**: 
- `notification_manager.py` → `_send_android_native()` (创建Intent)
- `main.py` → `handle_notification_intent()` (处理跳转)

#### 步骤1: 创建PendingIntent
```python
Intent = autoclass('android.content.Intent')
PendingIntent = autoclass('android.app.PendingIntent')

# 创建Intent并添加参数
intent = Intent(activity, activity.getClass())
intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP)
intent.putExtra("notification_action", "open_results")

# 创建PendingIntent (Android 12+ 需要FLAG_IMMUTABLE)
pending_intent = PendingIntent.getActivity(
    activity, 0, intent,
    PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE
)

# 设置到通知
builder.setContentIntent(pending_intent)
```

#### 步骤2: 处理Intent参数
```python
def handle_notification_intent(self):
    from jnius import autoclass
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    intent = PythonActivity.mActivity.getIntent()
    
    notification_action = intent.getStringExtra("notification_action")
    
    if notification_action == "open_results":
        # 延迟跳转，确保UI已初始化
        Clock.schedule_once(lambda dt: self._navigate_to_results(), 0.5)

def _navigate_to_results(self):
    self.root.screen_manager.current = "results"
```

**关键点**:
- 使用`FLAG_ACTIVITY_CLEAR_TOP`清除栈顶Activity
- 使用`FLAG_IMMUTABLE`兼容Android 12+
- 延迟跳转确保UI完全加载

---

### WakeLock后台保活

**实现位置**: 
- `main.py` → `acquire_wakelock()` / `release_wakelock()`
- `android_service.py` → `acquire_wakelock()`

#### 主应用WakeLock
```python
def acquire_wakelock(self):
    from jnius import autoclass
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    Context = autoclass('android.content.Context')
    PowerManager = autoclass('android.os.PowerManager')
    
    activity = PythonActivity.mActivity
    power_manager = activity.getSystemService(Context.POWER_SERVICE)
    
    # 创建PARTIAL_WAKE_LOCK
    self.wake_lock = power_manager.newWakeLock(
        PowerManager.PARTIAL_WAKE_LOCK,
        'BinanceAnalyzer::AppWakeLock'
    )
    self.wake_lock.acquire()
```

**WakeLock类型**:
- `PARTIAL_WAKE_LOCK`: CPU保持运行，屏幕可关闭 ✅ 推荐
- `FULL_WAKE_LOCK`: CPU和屏幕都保持运行 ❌ 耗电高
- `SCREEN_DIM_WAKE_LOCK`: 屏幕变暗但不关闭 ❌ 已废弃

**生命周期管理**:
```python
# 应用启动时获取
def on_start(self):
    self.acquire_wakelock()

# 应用退出时释放
def on_stop(self):
    self.release_wakelock()
```

---

### 前台服务通知

**实现位置**: `android_service.py` → `start_foreground_service()`

```python
def start_foreground_service():
    # 1. 创建低优先级通知渠道
    channel_id = "foreground_service_channel"
    importance = NotificationManager.IMPORTANCE_LOW
    channel = NotificationChannel(channel_id, "后台服务", importance)
    
    # 2. 创建持久通知
    builder = NotificationBuilder(activity, channel_id)
    builder.setContentTitle("币安分析工具")
    builder.setContentText("后台服务运行中...")
    builder.setOngoing(True)  # 不可滑动删除
    
    # 3. 显示通知（ID=999）
    notification_service.notify(999, builder.build())
```

**关键配置**:
- `IMPORTANCE_LOW`: 低优先级，不打扰用户
- `setOngoing(True)`: 持久通知，不可删除
- 通知ID=999: 与普通通知（ID=1）分离

---

### 智能通知逻辑

**实现位置**: `service.py` → `_run_analysis()`

#### 核心逻辑
```python
def _run_analysis(self):
    # 获取当前和上次的匹配数量
    results = analyzer.analyze()
    current_count = len(results)
    
    last_analysis = self.db_manager.get_latest_analysis()
    last_count = len(last_analysis["results"]) if last_analysis else 0
    
    # 通知决策逻辑
    should_notify = False
    notify_type = None
    
    if current_count == 0:
        if last_count > 0:
            # 从有变无 -> 发送特殊通知
            should_notify = True
            notify_type = "zero_from_nonzero"
        else:
            # 持续为0 -> 不通知
            should_notify = False
    else:
        # 有结果 -> 正常通知
        should_notify = True
        notify_type = "normal"
    
    # 发送通知
    if should_notify:
        if notify_type == "zero_from_nonzero":
            self.notif_manager.notify_zero_result(last_count)
        else:
            self.notif_manager.notify_analysis_complete(current_count, results)
```

**关键点**:
- 保存结果前先获取上次结果
- 比较当前和上次的数量
- 根据状态转换决定是否通知
- 使用不同的通知方法

#### 通知方法
```python
# notification_manager.py

def notify_zero_result(self, previous_count):
    """从有结果变为0时的特殊通知"""
    title = "匹配结果清零"
    message = f"之前有 {previous_count} 个币种符合条件，现在已全部不符合条件"
    return self.send_notification(title, message, timeout=15)
```

---

## 📋 权限要求

### buildozer.spec配置
```ini
android.permissions = 
    INTERNET,
    WRITE_EXTERNAL_STORAGE,
    READ_EXTERNAL_STORAGE,
    WAKE_LOCK,                    # WakeLock权限
    FOREGROUND_SERVICE,           # 前台服务权限
    POST_NOTIFICATIONS,           # 通知权限（Android 13+）
    SCHEDULE_EXACT_ALARM,         # 精确定时权限
    ACCESS_NETWORK_STATE
```

### 运行时权限请求
```python
def request_android_permissions(self):
    from android.permissions import request_permissions, Permission
    
    required_permissions = [
        Permission.POST_NOTIFICATIONS,  # Android 13+ 必须
        Permission.WAKE_LOCK,
        Permission.FOREGROUND_SERVICE,
        # ...其他权限
    ]
    request_permissions(required_permissions)
```

---

## 🧪 测试方法

### 1. 测试通知时间显示
```bash
# 1. 触发一次分析
# 2. 查看通知内容是否包含 [HH:MM:SS] 格式时间
# 3. 下拉通知栏，检查通知显示的时间戳
```

### 2. 测试点击跳转
```bash
# 1. 触发分析并收到通知
# 2. 点击通知
# 3. 应用应自动打开并跳转到"结果"页面
# 4. 查看日志: adb logcat | grep "通知跳转"
```

### 3. 测试后台保活
```bash
# 1. 启动应用并开启定时任务
# 2. 按Home键将应用切到后台
# 3. 等待定时间隔
# 4. 检查是否收到通知（证明后台任务执行成功）

# 查看WakeLock状态
adb shell dumpsys power | grep BinanceAnalyzer
```

### 4. 测试锁屏保活
```bash
# 1. 启动应用并开启定时任务
# 2. 锁屏（按电源键）
# 3. 等待定时间隔
# 4. 解锁后检查是否收到通知

# 查看日志
adb logcat | grep "定时分析"
```

### 5. 测试前台服务
```bash
# 1. 启动应用
# 2. 下拉通知栏
# 3. 应看到"币安分析工具 - 后台服务运行中..."持久通知
# 4. 尝试滑动删除（应无法删除）
```

---

## ⚠️ 注意事项

### 1. 电量消耗
- **WakeLock**: 使用PARTIAL_WAKE_LOCK，仅保持CPU运行，电量消耗较低
- **建议**: 
  - 定时间隔设置为2-4小时
  - 充电时或WiFi环境下使用
  - 不需要时关闭定时任务

### 2. 系统限制
- **省电模式**: 部分手机的省电模式可能限制后台运行
  - 小米: 需要在"自启动管理"中允许
  - 华为: 需要在"电池优化"中关闭优化
  - OPPO/Vivo: 需要在"后台冻结"中允许后台运行
- **Android 12+**: 需要用户手动授予精确定时权限

### 3. 前台服务通知
- 持久通知无法删除（设计如此）
- 如需隐藏通知，需关闭定时任务并重启应用
- 通知优先级为LOW，不会打扰用户

### 4. 通知跳转
- 仅在应用被完全关闭时跳转到结果页面
- 如果应用已在前台，点击通知会重新启动Activity
- 使用`FLAG_ACTIVITY_CLEAR_TOP`确保不会创建多个实例

---

## 🔍 故障排除

### 问题1: 通知不显示时间
**原因**: Android版本过低或通知渠道设置问题  
**解决**:
```bash
# 检查Android版本
adb shell getprop ro.build.version.sdk

# 重新创建通知渠道
# 卸载应用 → 重新安装
```

### 问题2: 点击通知无反应
**原因**: PendingIntent未正确设置或Intent参数丢失  
**解决**:
```bash
# 查看日志
adb logcat | grep "通知跳转"

# 检查Intent参数
adb logcat | grep "notification_action"
```

### 问题3: 后台任务不执行
**原因**: WakeLock未获取或被系统限制  
**解决**:
```bash
# 检查WakeLock状态
adb shell dumpsys power | grep BinanceAnalyzer

# 检查权限
adb shell dumpsys package com.binance.analyzer | grep WAKE_LOCK

# 关闭电池优化
设置 → 应用管理 → 币安分析工具 → 电池 → 不限制
```

### 问题4: 锁屏后停止运行
**原因**: 手机厂商限制后台运行  
**解决**:
- **小米**: 设置 → 应用设置 → 应用管理 → 币安分析工具 → 省电策略 → 无限制
- **华为**: 设置 → 电池 → 应用启动管理 → 币安分析工具 → 手动管理 → 允许后台活动
- **OPPO/Vivo**: 设置 → 电池 → 高耗电应用 → 币安分析工具 → 允许后台运行

---

## 📊 功能对比

| 功能 | v1.1.0 | v1.2.0 |
|------|--------|--------|
| 通知显示 | ✅ | ✅ |
| 通知时间 | ❌ | ✅ HH:MM:SS |
| 点击跳转 | ❌ | ✅ 跳转到结果页 |
| 后台运行 | ⚠️ 不稳定 | ✅ WakeLock保活 |
| 锁屏运行 | ❌ | ✅ 支持 |
| 前台服务 | ❌ | ✅ 持久通知 |
| 系统杀死保护 | ❌ | ✅ 增强 |

---

## 🚀 未来改进方向

- [ ] 支持自定义通知跳转目标（历史记录/设置等）
- [ ] 添加通知操作按钮（快速停止/重新分析）
- [ ] 优化WakeLock策略（仅在定时任务前获取）
- [ ] 支持JobScheduler替代Thread（更省电）
- [ ] 添加电量监控和智能省电模式

---

**最后更新**: 2025-12-19  
**版本**: v1.2.0
