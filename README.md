# 币安合约分析工具 - Android应用

## 项目简介
这是一个基于Kivy框架开发的Android应用，用于分析币安期货市场的三日涨幅数据。应用支持定时自动分析、结果变化通知、历史记录查看等功能。

## 主要功能
用于拉取币安上架的币中，最近1天，2天，3天涨幅超过设定阈值的币并触发通知，支持定时运行

## 项目结构
```
binance_android_app/
├── main.py                    # Kivy主程序（UI界面）
├── analysis_core.py           # 分析核心逻辑
├── service.py                 # 后台定时服务
├── database.py                # 历史记录数据库管理
├── config_manager.py          # 配置管理
├── notification_manager.py    # 通知管理
├── buildozer.spec            # Android打包配置
├── requirements.txt          # Python依赖
└── README.md                 # 使用说明
```

## 环境要求
- Python 3.8+
- Kivy 2.2.1
- Buildozer (用于打包APK)
- Linux系统 (推荐Ubuntu 20.04+) 或 WSL2

## 安装依赖

### 1. 安装Python依赖
```bash
pip install -r requirements.txt
```

### 2. 安装Buildozer（Linux/WSL）
```bash
# 安装系统依赖
sudo apt update
sudo apt install -y git zip unzip openjdk-17-jdk python3-pip autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev

# 安装Buildozer
pip3 install --user buildozer

# 安装Cython
pip3 install --user Cython==0.29.33
```

## 本地测试运行

在电脑上测试应用（不打包APK）：
```bash
python main.py
```

## 打包APK

### 方法一：使用Buildozer（推荐）
```bash
# 首次打包（会下载Android SDK/NDK，需要较长时间）
buildozer android debug

# 打包完成后，APK位于：
# bin/binanceanalyzer-1.0.0-arm64-v8a-debug.apk
```

### 方法二：指定架构打包
```bash
# 仅打包ARM64架构（适用于大多数现代Android设备）
buildozer android debug

# 同时打包多个架构
buildozer -v android debug
```

### 打包发布版本
```bash
# 生成签名的发布版APK
buildozer android release

# 需要配置签名密钥，参考：
# https://buildozer.readthedocs.io/en/latest/quickstart.html#create-a-package-for-android
```

## 安装到手机

### 方法一：通过ADB安装
```bash
# 连接手机并启用USB调试
adb devices

# 安装APK
adb install -r bin/binanceanalyzer-1.0.0-arm64-v8a-debug.apk
```

### 方法二：直接传输安装
1. 将APK文件传输到手机
2. 在手机上打开文件管理器
3. 点击APK文件进行安装
4. 允许"未知来源"安装权限

## 使用说明

### 首次使用
1. **授予权限**: 首次启动时，应用会请求以下权限：
   - 网络访问权限（必需）
   - 存储权限（保存分析结果）
   - 通知权限（推送提醒）
   - 后台运行权限（定时任务）

2. **配置参数**: 进入"设置"页面，根据需要调整：
   - 最小涨幅：默认100%
   - 流动性阈值：默认1,000,000 USDT
   - 最大分析数量：默认500个

3. **立即分析**: 点击"立即分析"按钮，首次运行会缓存交易所信息

### iQOO/vivo设备专项配置（重要！）
**如果你使用iQOO或vivo手机，请务必完成以下设置，否则应用可能被系统杀死：**

1. **自启动管理**: i管家 → 应用管理 → 权限管理 → 自启动 → 开启
2. **后台高耗电**: i管家 → 省电管理 → 后台高耗电 → 允许
3. **后台耗电管理**: 设置 → 电池 → 后台耗电管理 → 允许后台高耗电
4. **后台冻结**: i管家 → 应用管理 → 后台冻结 → 关闭
5. **锁定后台**: 最近任务 → 下拉应用卡片 → 点击锁定🔒
6. **通知权限**: 设置 → 通知与状态栏 → 应用通知 → 允许通知

**详细配置指南**: 请查看 `IQOO_SETUP_GUIDE.md` 文件

### 定时任务设置
1. 进入"定时设置"页面
2. 开启"启用定时分析"开关
3. 选择运行间隔（建议每2-4小时）
4. 配置通知选项：
   - ☑ 发现变化时通知（推荐开启）
   - ☑ 分析完成后通知

### 通知逻辑说明
应用采用智能通知策略，避免无意义的通知：
- **有结果时**: 正常发送通知，显示匹配数量和前3名币种
- **持续无结果**: 不发送通知（避免骚扰）
- **从有变无**: 发送特殊通知"匹配结果清零"，提醒用户市场变化
- **通知时间**: 每条通知显示精确时间（HH:MM:SS格式）
- **点击跳转**: 点击通知自动打开应用并跳转到结果页面

### Server酱通知配置（推荐）
应用支持多种通知方式同时发送，包括Android原生通知、plyer通知和Server酱（ServerChan）。Server酱可以将通知推送到微信，特别适合需要远程接收通知的场景。

#### 1. 获取Server酱SendKey
1. 访问 [Server酱官网](https://sct.ftqq.com/)
2. 使用微信扫码登录
3. 进入"SendKey"页面，复制你的SendKey（格式：`sctp开头的字符串`）

#### 2. 配置Server酱
1. 打开应用，进入"设置"页面
2. 滚动到"Server酱设置"分组
3. 开启"启用Server酱通知"开关
4. 填写你的SendKey
5. （可选）自定义通知标题和正文模板：
   - **通知标题模板**: 例如 `币安分析完成`
   - **通知正文模板**: 支持 `{count}` 变量，例如 `找到 {count} 个符合条件的交易对`
6. 点击"保存设置"

#### 3. 通知内容说明
- 通知会自动显示前3名币种的详细信息
- 包含币种名称和1日/2日/3日涨幅数据
- 示例：
  ```
  币安分析完成
  
  找到 15 个符合条件的交易对
  
  【前3名币种】
  1. BTCUSDT
     1日: +5.23% | 2日: +8.45% | 3日: +12.67%
  2. ETHUSDT
     1日: +3.12% | 2日: +6.34% | 3日: +9.56%
  3. BNBUSDT
     1日: +2.45% | 2日: +4.89% | 3日: +7.33%
  ```

#### 4. 多通知方式说明
- **Android环境**: 同时尝试Android原生通知 + plyer + Server酱
- **Windows测试环境**: 同时尝试plyer + Server酱
- 只要有一种方式成功即视为通知发送成功
- 可在设置中单独关闭Server酱通知

### 查看历史记录
1. 进入"历史记录"页面
2. 使用筛选功能：近2天（默认）、近7天、近30天、全部
3. 点击任意记录查看详情
4. 支持查看最近500次分析结果

## Android权限说明

应用申请的权限及用途：
- `INTERNET`: 访问币安API获取行情数据
- `WRITE_EXTERNAL_STORAGE`: 保存分析结果和缓存文件
- `READ_EXTERNAL_STORAGE`: 读取配置文件
- `WAKE_LOCK`: 保持后台运行不被系统杀死
- `RECEIVE_BOOT_COMPLETED`: 开机自启动（可选）
- `FOREGROUND_SERVICE`: 前台服务保证定时任务稳定运行
- `POST_NOTIFICATIONS`: 发送通知提醒
- `SCHEDULE_EXACT_ALARM`: 精确定时任务
- `ACCESS_NETWORK_STATE`: 检测网络连接状态

## 常见问题

### Q1: 打包时提示"Command failed"
**A**: 检查是否安装了所有系统依赖，特别是Java JDK 17和Android SDK。

### Q2: 应用安装后闪退
**A**: 检查手机Android版本（需要Android 5.0+），并确保授予了必要权限。

### Q3: 定时任务不运行
**A**: 检查以下设置：
- 应用是否被系统省电模式限制
- 是否授予了后台运行权限
- 网络连接是否正常

### Q4: 通知不显示
**A**: 进入手机设置 → 应用管理 → Binance Analyzer → 通知，确保通知权限已开启。

### Q5: 分析速度慢
**A**: 可以在设置中减少"最大分析数量"，或增加"API请求延迟"避免被限频。

## 技术栈
- **UI框架**: Kivy 2.2.1
- **网络请求**: requests
- **通知**: plyer
- **数据库**: SQLite3
- **打包工具**: Buildozer
- **目标平台**: Android 5.0+ (API 21+)

## 开发调试

### 查看日志
```bash
# 实时查看应用日志
adb logcat | grep python
```

### 调试技巧
1. 使用`print()`输出调试信息，可通过adb logcat查看
2. 在代码中添加try-except捕获异常
3. 使用Kivy的Inspector工具检查UI布局

## 更新日志

### v1.2.0 (2025-12-19)
- ✨ 通知显示精确时间戳（HH:MM:SS格式）
- ✨ 点击通知自动跳转到结果页面
- ✨ WakeLock后台保活（CPU保持运行）
- ✨ 锁屏状态下保持应用运行
- ✨ 前台服务持久通知（防止系统杀死进程）
- ✨ 智能通知逻辑：匹配数量为0时不通知，但从有结果变为0时发送特殊通知
- ✨ 自动最小化到后台（启动后2秒自动隐藏）
- ✨ iQOO/vivo设备专项优化和配置指南
- ✨ 电池优化豁免请求（REQUEST_IGNORE_BATTERY_OPTIMIZATIONS）
- ⚡ 优化后台服务稳定性

### v1.1.0 (2025-12-18)
- ✨ 集成Server酱(ServerChan)通知，支持微信推送
- ✨ 多通知方式同时发送（Android原生+plyer+Server酱）
- ✨ 通知内容显示前3名币种详细涨幅信息
- ✨ 适配Android 13+通知渠道(NotificationChannel)
- ✨ 设置页面新增Server酱配置分组
- ✨ 支持自定义通知标题和正文模板（{count}变量）
- ✨ 历史记录页面新增时间筛选功能（2天/7天/30天/全部）
- 🎨 UI改版为Bilibili风格底部导航栏设计
- 🎨 应用Element UI配色方案，统一按钮圆角和颜色
- 🎨 添加应用图标和开屏动画
- 🐛 修复卡片布局内容溢出问题（使用wrapper模式）
- 🐛 修复TextInput在Android设备上显示不全的问题
- 🐛 修复定时任务开关导致应用崩溃的问题
- ⚡ 添加运行时权限请求功能
- ⚡ 主页新增日志显示和清空功能

### v1.0.0 (2025-12-17)
- ✨ 首次发布
- ✅ 实现核心分析功能
- ✅ 支持定时任务和通知
- ✅ 历史记录查看
- ✅ 参数配置界面

## 注意事项
⚠️ **免责声明**: 本应用仅供学习和研究使用，不构成任何投资建议。使用本应用进行交易决策的风险由用户自行承担。

⚠️ **API限频**: 币安API有调用频率限制，请合理设置定时间隔和请求延迟，避免被封禁IP。

⚠️ **电池消耗**: 后台定时任务会增加电池消耗，建议在充电时或WiFi环境下使用。

## 许可证
MIT License

## 联系方式
如有问题或建议，欢迎提Issue或Pull Request。

---

**祝使用愉快！** 🚀
