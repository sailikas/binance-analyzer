# 币安合约分析工具 - 故障排除指南

## 目录
- [UI布局问题](#ui布局问题)
- [通知问题](#通知问题)
- [权限问题](#权限问题)
- [定时任务问题](#定时任务问题)
- [开发调试问题](#开发调试问题)

---

## UI布局问题

### 问题1: Android设备上布局挤在一起,Windows正常

**症状**:
- 在Windows桌面测试时UI显示正常
- 在Android手机上运行时,所有内容挤在一起
- 卡片、列表项、输入框等组件显示不完整
- 文字被截断或重叠

**原因分析**:
- 代码中使用固定像素值(如`height=180`, `padding=[15, 12]`)
- 没有使用Kivy的`dp()`函数进行DPI适配
- 字体使用`sp`单位会在高DPI设备上自动放大
- 但容器使用固定像素不会缩放,导致内容溢出

**解决方案**:
```python
# 1. 导入dp函数
from kivy.metrics import dp, sp

# 2. 将所有固定像素值转换为dp()
# 错误写法:
height=180
padding=[15, 12]
spacing=10

# 正确写法:
height=dp(180)
padding=[dp(15), dp(12)]
spacing=dp(10)

# 3. 增加容器高度以容纳更大字体(建议增加20-30%)
height=dp(220)  # 原180增加到220
```

**技术原理**:
- `dp()`函数根据设备DPI自动缩放
- 96 DPI设备: `dp(180)` ≈ 180像素
- 240 DPI设备: `dp(180)` ≈ 450像素
- 确保在不同设备上视觉大小一致

**修改位置**:
- `main.py` 所有BoxLayout的height、padding、spacing参数
- 特别注意: ResultsScreen卡片、HistoryScreen列表项、SettingsScreen输入框

---

## 通知问题

### 问题2: 通知在Android设备上不显示

**症状**:
- 应用显示"通知发送成功"但实际没收到通知
- Windows上plyer显示成功但Android上无效
- 没有权限请求弹窗

**原因分析**:
1. Android 13+需要运行时请求通知权限
2. plyer在某些设备上不可靠
3. 需要创建NotificationChannel(Android 8.0+)
4. 可能被系统省电模式限制

**解决方案**:

#### 方案A: 运行时权限请求
```python
def request_android_permissions(self):
    """检查并请求Android权限"""
    try:
        from android.permissions import request_permissions, check_permission, Permission
        
        required_permissions = [
            Permission.POST_NOTIFICATIONS,
            Permission.INTERNET,
            Permission.WAKE_LOCK,
            Permission.FOREGROUND_SERVICE
        ]
        
        permissions_to_request = []
        for perm in required_permissions:
            if not check_permission(perm):
                permissions_to_request.append(perm)
        
        if permissions_to_request:
            request_permissions(permissions_to_request)
    except Exception as e:
        print(f"权限请求失败: {e}")
```

#### 方案B: Android原生通知(支持Android 13+)
```python
def _send_android_native(self, title, message):
    from jnius import autoclass
    
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    NotificationChannel = autoclass('android.app.NotificationChannel')
    NotificationManager = autoclass('android.app.NotificationManager')
    
    # 创建通知渠道(Android 8.0+必需)
    channel_id = "app_channel"
    channel = NotificationChannel(channel_id, "通知", 
                                  NotificationManager.IMPORTANCE_HIGH)
    
    # 发送通知
    builder = NotificationBuilder(activity, channel_id)
    builder.setContentTitle(title)
    builder.setContentText(message)
    notification_service.notify(1, builder.build())
```

#### 方案C: Server酱备用方案
```python
# 使用Server酱作为备用通知方式
def _send_serverchan(self, title, message):
    sendkey = self.config_manager.get("serverchan_key", "")
    if not sendkey:
        return False
    
    import requests
    url = f"https://sctapi.ftqq.com/{sendkey}.send"
    data = {"title": title, "desp": message}
    response = requests.post(url, data=data, timeout=10)
    return response.status_code == 200
```

**推荐策略**: 同时使用多种通知方式
```python
def send_notification(self, title, message):
    success_count = 0
    
    # 1. 尝试Android原生
    if self._send_android_native(title, message):
        success_count += 1
    
    # 2. 尝试plyer
    if self._send_plyer(title, message):
        success_count += 1
    
    # 3. 尝试Server酱
    if self._send_serverchan(title, message):
        success_count += 1
    
    return success_count > 0
```

**配置要求**:
- `buildozer.spec`中添加权限:
  ```ini
  android.permissions = POST_NOTIFICATIONS,INTERNET,WAKE_LOCK,FOREGROUND_SERVICE
  ```
- Server酱需要在设置中配置SendKey

---

## 权限问题

### 问题3: 应用启动时没有权限请求弹窗

**症状**:
- 首次安装应用后没有权限请求
- 功能无法正常使用(通知、后台运行等)

**原因**:
- Android 6.0+需要运行时请求危险权限
- 仅在`buildozer.spec`声明权限不够

**解决方案**:
在`App.on_start()`中添加权限请求:
```python
def on_start(self):
    # 检测Android平台
    import platform
    if platform.system() == 'Linux':
        try:
            import sys
            if hasattr(sys, 'getandroidapilevel'):
                self.request_android_permissions()
        except:
            pass
```

**需要请求的权限**:
- `POST_NOTIFICATIONS` - 发送通知(Android 13+)
- `INTERNET` - 网络访问
- `WAKE_LOCK` - 保持唤醒
- `FOREGROUND_SERVICE` - 前台服务
- `SCHEDULE_EXACT_ALARM` - 精确定时

---

## 定时任务问题

### 问题4: 定时任务开关导致应用崩溃

**症状**:
- 点击"启用定时分析"开关后应用闪退
- 日志显示ImportError或AttributeError

**原因**:
尝试使用Android PythonService但环境不支持:
```python
# 错误代码:
from android import mActivity
from jnius import autoclass
service = autoclass('org.kivy.android.PythonService')
service.start(mActivity, 'Service')  # 崩溃
```

**解决方案**:
使用Python线程代替Android Service:
```python
def toggle_schedule(self, switch, value):
    self.config_manager.set("schedule_enabled", value)
    
    # 使用线程服务(跨平台兼容)
    if value:
        self.service.start_service()
    else:
        self.service.stop_service()
```

**service.py实现**:
```python
class AnalysisService:
    def start_service(self):
        if self.is_running:
            return False
        
        self.is_running = True
        self.thread = Thread(target=self._service_loop, daemon=True)
        self.thread.start()
        return True
    
    def _service_loop(self):
        while self.is_running:
            if schedule_enabled:
                self._run_analysis()
            
            interval = self.config_manager.get("schedule_interval", 7200)
            for i in range(interval):
                if not self.is_running:
                    break
                time.sleep(1)
```

---

## 开发调试问题

### 问题5: 属性未初始化导致AttributeError

**症状**:
```python
AttributeError: 'HomeScreen' object has no attribute 'add_log'
AttributeError: 'HistoryScreen' object has no attribute 'current_filter'
```

**原因**:
- 方法在定义前被调用
- `__init__`中的初始化顺序错误
- 异步回调访问未初始化的属性

**解决方案**:

#### 方法1: 调整初始化顺序
```python
def __init__(self, **kwargs):
    super().__init__(**kwargs)
    
    # 1. 先初始化所有属性
    self.current_filter = 2
    self.filter_buttons = {}
    
    # 2. 再创建UI组件
    self.create_ui()
    
    # 3. 最后调用方法
    self.load_history()
```

#### 方法2: 防御性检查
```python
def on_enter(self):
    # 防御性检查
    if not hasattr(self, 'current_filter'):
        self.current_filter = 2
    
    self.load_history()
```

#### 方法3: 使用@mainthread装饰器
```python
from kivy.clock import mainthread

@mainthread
def add_log(self, message):
    """确保在主线程中更新UI"""
    # 安全地添加日志
    self.log_container.add_widget(log_label)
```

---

### 问题6: 卡片内容溢出白色背景

**症状**:
- 币种名称显示在白色卡片外面
- 内容和背景不对齐

**原因**:
单个BoxLayout同时设置padding和背景,在Android上渲染顺序问题

**解决方案 - Wrapper模式**:
```python
# 外层wrapper: 负责背景
card_wrapper = BoxLayout(
    orientation="vertical",
    size_hint_y=None,
    height=dp(220),
    padding=0  # 外层不设padding
)

# 添加圆角背景
with card_wrapper.canvas.before:
    Color(*BG_WHITE)
    card_wrapper.rect = RoundedRectangle(
        pos=card_wrapper.pos, 
        size=card_wrapper.size, 
        radius=[dp(10)]
    )

# 内层card: 负责内容和padding
card = BoxLayout(
    orientation="vertical",
    padding=[dp(15), dp(12)],  # 内层设padding
    spacing=dp(6)
)

# 组装
card_wrapper.add_widget(card)
# 所有内容添加到card,不是card_wrapper
card.add_widget(content)
```

---

### 问题7: TextInput在Android上只显示一半

**症状**:
- 输入框在Windows上正常
- 在Android上只能看到一半数字
- 输入框高度过大(2行高)

**原因**:
- Android渲染padding的方式不同
- 固定高度没有使用dp()
- multiline默认行为差异

**解决方案**:
```python
# 1. 使用dp()设置高度
interval_box = BoxLayout(size_hint_y=None, height=dp(60))

# 2. 不设置padding,增大字体
self.minutes_input = TextInput(
    text=str(minutes),
    multiline=False,
    input_filter='int',
    size_hint_x=0.25,
    font_size='18sp'  # 增大字体,不用padding
)

# 3. 确保容器高度足够
# 原: height=50 (太小)
# 改: height=dp(60) (增加20%)
```

---

## 调试技巧

### 查看Android日志
```bash
# 实时查看应用日志
adb logcat | grep python

# 查看所有日志
adb logcat

# 清空日志后查看
adb logcat -c && adb logcat
```

### 在代码中添加调试日志
```python
print(f"[调试] 变量值: {value}")
print(f"[调试] 类型: {type(obj)}")
print(f"[调试] 属性: {dir(obj)}")

# 使用try-except捕获详细错误
try:
    # 可能出错的代码
    pass
except Exception as e:
    print(f"[错误] {e}")
    import traceback
    traceback.print_exc()
```

### Windows本地测试
```bash
# 快速测试UI
python main.py

# 检查语法错误
python -m py_compile main.py
```

---

## 常见问题速查表

| 问题 | 症状 | 快速解决 |
|------|------|----------|
| 布局挤压 | Android上内容重叠 | 所有像素值用`dp()`包裹 |
| 通知不显示 | 无通知弹出 | 1.请求权限 2.使用Server酱 |
| 应用崩溃 | 点击功能闪退 | 检查`AttributeError`,添加防御性检查 |
| 输入框异常 | 只显示一半 | 使用`dp()`,去掉padding |
| 卡片溢出 | 内容在背景外 | 使用wrapper模式 |
| 定时任务失败 | 开关崩溃 | 用线程代替Android Service |

---

## 预防措施

### 开发规范
1. **始终使用dp()**: 所有固定像素值必须用`dp()`包裹
2. **运行时权限**: Android 6.0+必须请求危险权限
3. **防御性编程**: 访问属性前检查是否存在
4. **多设备测试**: Windows + Android真机测试
5. **日志记录**: 关键操作添加日志便于调试

### 代码检查清单
- [ ] 所有height、width使用dp()
- [ ] 所有padding、spacing使用dp()
- [ ] 所有radius使用dp()
- [ ] 字体大小使用sp单位
- [ ] 添加运行时权限请求
- [ ] UI更新使用@mainthread
- [ ] 异常处理try-except
- [ ] 属性初始化顺序正确

---

## 获取帮助

如遇到文档未覆盖的问题:
1. 查看应用日志: `adb logcat | grep python`
2. 检查Python语法: `python -m py_compile main.py`
3. 在GitHub提Issue并附上完整错误信息
4. 提供设备信息(Android版本、设备型号、屏幕DPI)

---

**最后更新**: 2025-12-18  
**版本**: v1.1.0