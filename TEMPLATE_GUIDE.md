# Android应用开发模板使用指南

## 项目概述

本项目是一个基于Kivy框架开发的Android应用模板，经过实战验证，具备完整的通用功能模块和稳定的跨平台架构。可快速改造为各类Android应用。

**原型项目**: 币安合约分析工具  
**技术栈**: Python + Kivy 2.2.1 + SQLite  
**支持平台**: Android 5.0+ / Windows (开发测试)

---

## 模板特点

### 1. 完整的UI框架
- ✅ **Bilibili风格底部导航栏** - 4个可配置Tab，支持图标和文字
- ✅ **Material Design配色** - Element UI + Bilibili配色方案
- ✅ **DPI完美适配** - 所有组件使用dp()，支持各种屏幕密度
- ✅ **圆角卡片布局** - Wrapper模式防止内容溢出
- ✅ **响应式设计** - 自适应不同屏幕尺寸

### 2. 强大的通用功能
- ✅ **历史记录系统** - SQLite存储，支持时间筛选（2天/7天/30天/全部）
- ✅ **定时任务服务** - 线程后台运行，可自定义间隔（分钟+秒）
- ✅ **多通知方式** - Android原生 + plyer + Server酱（微信推送）
- ✅ **配置管理** - JSON持久化，支持参数自定义
- ✅ **权限管理** - 运行时自动请求，跨平台兼容
- ✅ **日志系统** - 实时显示，支持清空，限制数量

### 3. 稳定的技术架构
- ✅ **跨平台兼容** - Windows开发测试，Android部署运行
- ✅ **线程服务** - 避免Android Service崩溃问题
- ✅ **防御性编程** - 属性检查，异常捕获，@mainthread装饰
- ✅ **模块化设计** - 业务逻辑与UI分离，易于维护

---

## 项目结构

```
项目根目录/
├── main.py                    # UI界面（需要修改）
├── analysis_core.py           # 业务逻辑（需要完全替换）
├── service.py                 # 定时任务服务（通用，保留）
├── database.py                # 历史记录数据库（通用，保留）
├── notification_manager.py    # 通知管理（通用，保留）
├── config_manager.py          # 配置管理（需要修改参数）
├── buildozer.spec            # Android打包配置（需要修改）
├── requirements.txt          # Python依赖（根据需要添加）
├── icon.png                  # 应用图标（需要替换）
├── presplash.png             # 开屏动画（需要替换）
├── README.md                 # 项目说明（需要重写）
└── TROUBLESHOOTING_GUIDE.md  # 故障排除（通用参考）
```

---

## 快速改造指南

### 第一步：替换业务逻辑

**文件**: `analysis_core.py`

```python
# 原代码: BinanceAnalyzer
class BinanceAnalyzer:
    def analyze(self):
        # 币安API分析逻辑
        return results

# 改为: 你的业务逻辑类
class YourBusinessLogic:
    def __init__(self, config=None, callback=None):
        self.config = config or {}
        self.callback = callback
    
    def execute(self):
        """执行你的核心业务逻辑"""
        # 1. 数据获取
        data = self.fetch_data()
        
        # 2. 数据处理
        results = self.process_data(data)
        
        # 3. 回调通知UI
        if self.callback:
            self.callback("处理完成", 100)
        
        return results
    
    def fetch_data(self):
        """获取数据 - 替换为你的数据源"""
        pass
    
    def process_data(self, data):
        """处理数据 - 替换为你的处理逻辑"""
        pass
```

---

### 第二步：修改主页UI

**文件**: `main.py` -> `HomeScreen`类

需要修改的关键部分：
1. 按钮文字和功能
2. 业务逻辑调用
3. 结果展示方式

---

### 第三步：修改配置参数

**文件**: `config_manager.py`

替换`default_config`中的业务参数，保留通用配置。

---

### 第四步：修改结果显示

**文件**: `main.py` -> `ResultsScreen`类

根据你的数据结构修改卡片内容展示。

---

### 第五步：修改数据库结构

**文件**: `database.py`

根据你的数据结构调整表结构和字段。

---

### 第六步：修改定时任务

**文件**: `service.py`

将定时任务改为调用你的业务逻辑。

---

### 第七步：修改打包配置

**文件**: `buildozer.spec`

修改应用名称、包名、版本、依赖、权限等。

---

### 第八步：替换图标和开屏动画

**文件**: `icon.png` 和 `presplash.png`

- **icon.png**: 512x512像素
- **presplash.png**: 800x1280像素

---

## 保留的通用模块（无需修改）

### 1. 底部导航栏 (`BottomNavBar`)
只需修改导航项配置即可。

### 2. 通知管理器 (`notification_manager.py`)
完全通用，支持三种通知方式。

### 3. 权限管理 (`request_android_permissions`)
完全通用，自动请求所需权限。

### 4. 历史记录页面 (`HistoryScreen`)
基本通用，可能需要调整显示内容。

### 5. 定时任务页面 (`ScheduleScreen`)
完全通用，无需修改。

---

## 配色方案

### Element UI + Bilibili配色（可选修改）

```python
# main.py 顶部配色常量
PRIMARY_COLOR = (0.40, 0.71, 0.98, 1)      # B站浅蓝色 #66B5FC
SUCCESS_COLOR = (0.40, 0.74, 0.40, 1)      # Element UI成功色 #67C23A
WARNING_COLOR = (0.90, 0.62, 0.22, 1)      # Element UI警告色 #E6A23C
DANGER_COLOR = (0.96, 0.35, 0.35, 1)       # Element UI危险色 #F56C6C
INFO_COLOR = (0.78, 0.78, 0.78, 1)         # 灰色按钮 #C8C8C8

BILIBILI_PINK = (0.98, 0.45, 0.60, 1)      # B站粉色 #FB7299
BILIBILI_BLUE = (0.40, 0.71, 0.98, 1)      # B站浅蓝色 #66B5FC

TEXT_PRIMARY = (0.18, 0.20, 0.24, 1)       # 主要文字
TEXT_REGULAR = (0.36, 0.38, 0.42, 1)       # 常规文字
TEXT_SECONDARY = (0.57, 0.63, 0.71, 1)     # 次要文字

BG_WHITE = (1, 1, 1, 1)                     # 白色背景
BG_LIGHT = (0.96, 0.97, 0.98, 1)           # 浅色背景
```

---

## 开发流程

### 1. 本地开发测试
```bash
# Windows环境测试
python main.py

# 检查语法
python -m py_compile main.py
```

### 2. Android打包
```bash
# 首次打包（下载SDK/NDK需要时间）
buildozer android debug

# 后续打包
buildozer android debug

# 发布版本
buildozer android release
```

### 3. 安装测试
```bash
# 通过ADB安装
adb install -r bin/yourapp-1.0.0-arm64-v8a-debug.apk

# 查看日志
adb logcat | grep python
```

---

## 关键技术要点

### 1. DPI适配（必须遵守）
```python
# 所有固定像素值必须使用dp()
from kivy.metrics import dp, sp

# 错误
height=180
padding=[15, 12]

# 正确
height=dp(180)
padding=[dp(15), dp(12)]
```

### 2. 线程安全UI更新
```python
from kivy.clock import mainthread

@mainthread
def update_ui(self, data):
    """必须在主线程更新UI"""
    self.label.text = data
```

### 3. Wrapper模式防止溢出
```python
# 外层负责背景
card_wrapper = BoxLayout(padding=0)
with card_wrapper.canvas.before:
    Color(*BG_WHITE)
    RoundedRectangle(...)

# 内层负责内容
card = BoxLayout(padding=[dp(15), dp(12)])
card_wrapper.add_widget(card)
```

### 4. 防御性编程
```python
def on_enter(self):
    # 检查属性是否存在
    if not hasattr(self, 'data'):
        self.data = []
    
    self.load_data()
```

---

## 常见问题参考

详见项目中的 `TROUBLESHOOTING_GUIDE.md`，包含：
- UI布局问题（DPI适配）
- 通知问题（多种方案）
- 权限问题（运行时请求）
- 定时任务问题（线程服务）
- AttributeError修复
- 调试技巧

---

## 模板优势总结

### ✅ 快速开发
- 完整UI框架，无需从零搭建
- 通用功能模块开箱即用
- 只需专注业务逻辑开发

### ✅ 稳定可靠
- 经过实战验证
- 解决了常见坑点
- 跨平台兼容性好

### ✅ 易于维护
- 模块化清晰
- 代码注释完整
- 故障排除文档齐全

### ✅ 功能丰富
- 历史记录
- 定时任务
- 多通知方式
- 配置管理
- 权限管理

### ✅ 用户体验好
- Material Design风格
- DPI完美适配
- 响应式设计
- 流畅动画

---

## 适用场景

本模板特别适合以下类型的Android应用：

1. **数据采集类** - 定期获取数据并通知
2. **监控类** - 定时检查状态并告警
3. **工具类** - 执行特定任务并记录历史
4. **信息查询类** - 查询数据并展示结果
5. **自动化类** - 定时执行脚本并通知结果

---

## 核心改造点总结

只需替换以下内容，即可快速开发新应用：

### 必须替换
1. **业务逻辑** (`analysis_core.py`) - 完全重写
2. **主页UI** (`HomeScreen`) - 修改按钮和功能
3. **结果展示** (`ResultsScreen`) - 根据数据结构调整
4. **配置参数** (`config_manager.py`) - 替换业务参数
5. **应用信息** (`buildozer.spec`) - 名称、包名、版本
6. **图标动画** (`icon.png`, `presplash.png`) - 替换素材

### 可选修改
1. **数据库结构** (`database.py`) - 根据需要调整
2. **配色方案** (`main.py`顶部常量) - 自定义颜色
3. **导航栏** (`BottomNavBar`) - 调整tab项
4. **通知内容** (`notification_manager.py`) - 自定义模板

### 完全保留
1. **通知管理** - 三种方式通用
2. **权限管理** - 自动请求通用
3. **定时服务** - 线程架构通用
4. **DPI适配** - dp()机制通用
5. **历史筛选** - 时间过滤通用

---

## 技术支持

- **项目地址**: https://github.com/sailikas/binance-analyzer
- **故障排除**: 参考 `TROUBLESHOOTING_GUIDE.md`
- **Kivy文档**: https://kivy.org/doc/stable/
- **Buildozer文档**: https://buildozer.readthedocs.io/

---

## 许可证

MIT License - 可自由修改和商用

---

**最后更新**: 2025-12-18  
**模板版本**: v1.0  
**基于项目**: 币安合约分析工具 v1.1.0
