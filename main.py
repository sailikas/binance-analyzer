"""
币安合约分析工具 - Kivy主程序
"""
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.switch import Switch
from kivy.uix.scrollview import ScrollView
from kivy.uix.progressbar import ProgressBar
from kivy.uix.spinner import Spinner
from kivy.uix.checkbox import CheckBox
from kivy.uix.widget import Widget
from kivy.uix.behaviors import ButtonBehavior
from kivy.animation import Animation
from kivy.clock import Clock, mainthread
from kivy.core.window import Window
from kivy.core.text import LabelBase
from kivy.metrics import dp, sp
from threading import Thread
import traceback
import os
import sys

# 注册中文字体
try:
    if os.name == 'nt':  # Windows
        LabelBase.register(name='Roboto', 
                          fn_regular='C:\\Windows\\Fonts\\msyh.ttc')
        # 注册支持emoji的字体
        LabelBase.register(name='Emoji', 
                          fn_regular='C:\\Windows\\Fonts\\seguiemj.ttf')
    else:  # Android/Linux
        # 尝试多个可能的字体路径
        font_paths = [
            '/system/fonts/DroidSansFallback.ttf',
            '/system/fonts/NotoSansCJK-Regular.ttc',
            '/system/fonts/DroidSans.ttf'
        ]
        for font_path in font_paths:
            if os.path.exists(font_path):
                LabelBase.register(name='Roboto', fn_regular=font_path)
                break
        
        # 尝试注册emoji字体
        emoji_font_paths = [
            '/system/fonts/NotoColorEmoji.ttf',
            '/system/fonts/AndroidEmoji.ttf'
        ]
        for font_path in emoji_font_paths:
            if os.path.exists(font_path):
                LabelBase.register(name='Emoji', fn_regular=font_path)
                break
except Exception as e:
    print(f"字体注册失败: {e}")

# 导入项目模块
try:
    from analysis_core import BinanceAnalyzer
    from database import DatabaseManager
    from notification_manager import NotificationManager
    from config_manager import ConfigManager
    from service import get_service
except Exception as e:
    print(f"模块导入失败: {e}")
    traceback.print_exc()
    sys.exit(1)

Window.clearcolor = (0.95, 0.95, 0.97, 1)  # Element UI浅灰背景

# B站+Element UI统一配色方案
PRIMARY_COLOR = (0.40, 0.71, 0.98, 1)      # B站浅蓝色 #66B5FC
SUCCESS_COLOR = (0.40, 0.74, 0.40, 1)      # Element UI成功色 #67C23A
WARNING_COLOR = (0.90, 0.62, 0.22, 1)      # Element UI警告色 #E6A23C
DANGER_COLOR = (0.96, 0.35, 0.35, 1)       # Element UI危险色 #F56C6C
INFO_COLOR = (0.78, 0.78, 0.78, 1)         # 灰色按钮 #C8C8C8

BILIBILI_PINK = (0.98, 0.45, 0.60, 1)      # B站粉色
BILIBILI_BLUE = (0.40, 0.71, 0.98, 1)      # B站浅蓝色

# 文字颜色
TEXT_PRIMARY = (0.18, 0.20, 0.24, 1)       # 主要文字
TEXT_REGULAR = (0.36, 0.38, 0.42, 1)       # 常规文字
TEXT_SECONDARY = (0.57, 0.63, 0.71, 1)     # 次要文字
TEXT_PLACEHOLDER = (0.76, 0.79, 0.82, 1)   # 占位文字

# 边框和背景
BORDER_BASE = (0.87, 0.88, 0.90, 1)        # 基础边框
BG_WHITE = (1, 1, 1, 1)                     # 白色背景
BG_LIGHT = (0.96, 0.97, 0.98, 1)           # 浅色背景


def create_rounded_button(text, bg_color, **kwargs):
    """创建圆角按钮"""
    from kivy.graphics import Color, RoundedRectangle
    
    btn = Button(
        text=text,
        background_color=(0, 0, 0, 0),  # 透明背景
        background_normal='',
        **kwargs
    )
    
    # 添加圆角矩形背景
    with btn.canvas.before:
        Color(*bg_color)
        btn.bg_rect = RoundedRectangle(pos=btn.pos, size=btn.size, radius=[dp(10)])
    
    btn.bind(pos=lambda obj, val: setattr(obj.bg_rect, "pos", val))
    btn.bind(size=lambda obj, val: setattr(obj.bg_rect, "size", val))
    
    return btn


class HomeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config_manager = ConfigManager()
        self.db_manager = DatabaseManager()
        self.notif_manager = NotificationManager()
        
        layout = BoxLayout(orientation="vertical", padding=[dp(20), dp(15), dp(20), dp(15)], spacing=dp(12))
        
        # 顶部标题
        layout.add_widget(Label(
            text="币安合约分析",
            size_hint_y=0.07,
            font_size="22sp",
            bold=True,
            color=TEXT_PRIMARY
        ))
        
        # 立即分析按钮 - B站浅蓝圆角
        btn_analyze = create_rounded_button(
            text="立即分析",
            bg_color=PRIMARY_COLOR,
            size_hint_y=0.11,
            font_size="18sp",
            bold=True
        )
        btn_analyze.bind(on_press=self.start_analysis)
        layout.add_widget(btn_analyze)
        
        # 分析状态卡片
        self.status_label = Label(
            text="最近分析时间: 暂无",
            size_hint_y=0.06,
            font_size="14sp",
            color=TEXT_REGULAR
        )
        layout.add_widget(self.status_label)
        
        # 日志区域标题和清空按钮
        log_header = BoxLayout(size_hint_y=0.06, spacing=dp(10))
        log_header.add_widget(Label(
            text="运行日志",
            font_size="15sp",
            bold=True,
            color=TEXT_PRIMARY
        ))
        btn_clear = create_rounded_button(
            text="清空",
            bg_color=INFO_COLOR,
            size_hint_x=0.2,
            font_size="14sp"
        )
        btn_clear.bind(on_press=lambda x: self.clear_logs())
        log_header.add_widget(btn_clear)
        layout.add_widget(log_header)
        
        # 滚动日志区域
        scroll = ScrollView(size_hint=(1, 0.65))
        self.log_container = GridLayout(cols=1, spacing=dp(5), size_hint_y=None, padding=[dp(8), dp(5)])
        self.log_container.bind(minimum_height=self.log_container.setter("height"))
        scroll.add_widget(self.log_container)
        layout.add_widget(scroll)
        
        self.add_widget(layout)
        self.update_status()
        self.add_log("系统就绪,等待分析...")
    
    @mainthread
    def add_log(self, message, progress=None, timestamp=None):
        """添加日志到日志区域(线程安全)"""
        import datetime
        
        # 使用传入的时间戳，如果没有则使用当前时间
        if timestamp:
            if isinstance(timestamp, str):
                # 如果是ISO格式字符串，解析为时间对象
                try:
                    dt = datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    time_str = dt.strftime("%H:%M:%S")
                except:
                    time_str = datetime.datetime.now().strftime("%H:%M:%S")
            else:
                time_str = timestamp.strftime("%H:%M:%S")
        else:
            time_str = datetime.datetime.now().strftime("%H:%M:%S")
        
        # 如果有进度信息，添加到消息中
        if progress is not None:
            display_message = f"{message} [{progress}%]"
        else:
            display_message = message
        
        log_label = Label(
            text=f"[{time_str}] {display_message}",
            size_hint_y=None,
            height=dp(48),
            font_size="14sp",
            color=TEXT_REGULAR,
            halign="left",
            valign="top",
            text_size=(None, None)
        )
        self.log_container.add_widget(log_label)
        
        # 限制日志数量
        if len(self.log_container.children) > 50:
            self.log_container.remove_widget(self.log_container.children[-1])
    
    def clear_logs(self):
        """清空日志"""
        self.log_container.clear_widgets()
        self.add_log("日志已清空")
    
    def update_status(self):
        latest = self.db_manager.get_latest_analysis()
        if latest:
            # 使用end_time作为主要显示时间
            timestamp = latest.get("end_time", latest.get("timestamp", ""))[:19].replace("T", " ")
            count = latest["symbol_count"]
            duration = latest.get("duration", 0)
            
            if duration > 0:
                self.status_label.text = f"最近分析: {timestamp} | 找到 {count} 个币种 | 耗时 {duration:.1f}秒"
            else:
                self.status_label.text = f"最近分析: {timestamp} | 找到 {count} 个符合条件的币种"
    
    def start_analysis(self, instance):
        self.add_log("开始分析...")
        Thread(target=self._run_analysis, daemon=True).start()
    
    def _run_analysis(self):
        try:
            config = self.config_manager.get_analyzer_config()
            analyzer = BinanceAnalyzer(config=config, callback=self.analysis_callback)
            analysis_data = analyzer.analyze()
            results = analysis_data.get("results", [])
            
            self.db_manager.save_analysis(analysis_data, config)
            
            Clock.schedule_once(lambda dt: self.show_results(results), 0)
            
            if self.config_manager.get("notify_on_complete", True):
                self.notif_manager.notify_analysis_complete(len(results), results)
        except Exception as e:
            error_msg = str(e)
            Clock.schedule_once(lambda dt: self.show_error(error_msg), 0)
    
    @mainthread
    def analysis_callback(self, message, progress=None):
        if progress is not None:
            self.add_log(f"{message} [{progress}%]")
        else:
            self.add_log(message)
    
    @mainthread
    def show_results(self, results):
        self.add_log(f"✓ 分析完成! 找到 {len(results)} 个符合条件的币种")
        self.update_status()
        
        results_screen = self.manager.get_screen("results")
        results_screen.set_from_screen("home")  # 设置来源页面
        results_screen.display_results(results)
        # 切换到结果页面
        app = App.get_running_app()
        if hasattr(app.root, 'nav_bar'):
            app.root.nav_bar.switch_screen("results")
    
    @mainthread
    def show_error(self, error_msg):
        self.add_log(f"✗ 出错: {error_msg}")


class ResultsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation="vertical", padding=[dp(15), dp(10), dp(15), dp(10)], spacing=dp(10))
        self.from_screen = "home"  # 记录来源页面
        
        # 顶部栏:返回按钮+标题
        top_bar = BoxLayout(size_hint_y=0.08, spacing=dp(10))
        btn_back = create_rounded_button(
            text="← 返回",
            bg_color=INFO_COLOR,
            size_hint_x=0.25,
            font_size="15sp"
        )
        btn_back.bind(on_press=self.go_back)
        top_bar.add_widget(btn_back)
        
        self.results_label = Label(
            text="分析结果",
            font_size="19sp",
            bold=True,
            color=TEXT_PRIMARY
        )
        top_bar.add_widget(self.results_label)
        self.layout.add_widget(top_bar)
        
        self.scroll_view = ScrollView(size_hint=(1, 0.92))
        self.results_container = GridLayout(cols=1, spacing=dp(12), size_hint_y=None, padding=[0, dp(5)])
        self.results_container.bind(minimum_height=self.results_container.setter("height"))
        self.scroll_view.add_widget(self.results_container)
        self.layout.add_widget(self.scroll_view)
        
        self.add_widget(self.layout)
    
    def display_results(self, results):
        self.results_container.clear_widgets()
        self.results_label.text = f"找到 {len(results)} 个符合条件的币种"
        
        if not results:
            self.results_container.add_widget(Label(
                text="未找到符合条件的交易对",
                size_hint_y=None,
                height=dp(96),
                font_size="15sp",
                color=TEXT_SECONDARY
            ))
            return
        
        for i, r in enumerate(results, 1):
            # 外层容器带背景
            card_wrapper = BoxLayout(
                orientation="vertical",
                size_hint_y=None,
                height=dp(220),
                padding=0
            )
            
            # 白色圆角背景
            from kivy.graphics import Color, RoundedRectangle
            with card_wrapper.canvas.before:
                Color(*BG_WHITE)
                card_wrapper.rect = RoundedRectangle(pos=card_wrapper.pos, size=card_wrapper.size, radius=[dp(10)])
            card_wrapper.bind(pos=lambda obj, val: setattr(obj.rect, "pos", val))
            card_wrapper.bind(size=lambda obj, val: setattr(obj.rect, "size", val))
            
            # 内容容器
            card = BoxLayout(
                orientation="vertical",
                padding=[dp(15), dp(12)],
                spacing=dp(6)
            )
            
            # 顶部: 币种名称和排名
            top_row = BoxLayout(size_hint_y=None, height=dp(36))
            top_row.add_widget(Label(
                text=r['symbol'],
                font_size="17sp",
                bold=True,
                color=PRIMARY_COLOR
            ))
            top_row.add_widget(Label(
                text=f"#{i}",
                size_hint_x=0.2,
                font_size="14sp",
                color=TEXT_SECONDARY
            ))
            card.add_widget(top_row)
            
            # 涨幅数据
            for period, gain_key in [("1日", "gain_1d"), ("2日", "gain_2d"), ("3日", "gain_3d")]:
                gain_val = r[gain_key] * 100
                gain_color = SUCCESS_COLOR if gain_val > 0 else DANGER_COLOR
                
                gain_row = BoxLayout(size_hint_y=None, height=dp(38))
                gain_row.add_widget(Label(
                    text=period,
                    size_hint_x=0.25,
                    font_size="15sp",
                    color=TEXT_REGULAR
                ))
                gain_row.add_widget(Label(
                    text=f"{gain_val:+.2f}%",
                    font_size="16sp",
                    bold=True,
                    color=gain_color
                ))
                card.add_widget(gain_row)
            
            card_wrapper.add_widget(card)
            self.results_container.add_widget(card_wrapper)
    
    def go_back(self, instance):
        """返回到来源页面"""
        self.manager.current = self.from_screen
    
    def set_from_screen(self, screen_name):
        """设置来源页面"""
        self.from_screen = screen_name


class ScheduleScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config_manager = ConfigManager()
        
        layout = BoxLayout(orientation="vertical", padding=[dp(20), dp(15), dp(20), dp(15)], spacing=dp(15))
        
        # 提示信息
        layout.add_widget(Label(
            text="定时功能的设置已移动到「设置」页面",
            size_hint_y=0.05,
            font_size="14sp",
            color=TEXT_SECONDARY,
            halign="center"
        ))
        
        # 日志区域标题和清空按钮
        log_header = BoxLayout(size_hint_y=0.06, spacing=dp(10))
        log_header.add_widget(Label(
            text="运行日志",
            font_size="16sp",
            bold=True,
            color=TEXT_PRIMARY
        ))
        btn_clear = create_rounded_button(
            text="清空",
            bg_color=INFO_COLOR,
            size_hint_x=0.2,
            font_size="14sp"
        )
        btn_clear.bind(on_press=lambda x: self.clear_schedule_logs())
        log_header.add_widget(btn_clear)
        layout.add_widget(log_header)
        
        # 滚动日志区域
        scroll = ScrollView(size_hint=(1, 0.84))
        self.schedule_log_container = GridLayout(cols=1, spacing=dp(5), size_hint_y=None, padding=[dp(8), dp(5)])
        self.schedule_log_container.bind(minimum_height=self.schedule_log_container.setter("height"))
        scroll.add_widget(self.schedule_log_container)
        layout.add_widget(scroll)
        
        self.add_widget(layout)
        
        # 初始化日志
        self.add_schedule_log("定时分析日志已初始化")
    
    def _get_next_run_text(self):
        if self.config_manager.get("schedule_enabled", False):
            interval = self.config_manager.get("schedule_interval", 7200)
            minutes = interval // 60
            seconds = interval % 60
            return f"下次运行: 已启用 (间隔 {minutes}分{seconds}秒)"
        return "下次运行: 未启用"
    
    def save_interval(self, instance):
        try:
            minutes = int(self.minutes_input.text or "0")
            seconds = int(self.seconds_input.text or "0")
            total_seconds = minutes * 60 + seconds
            
            if total_seconds < 10:
                self.status_label.text = "错误: 间隔不能少于10秒"
                self.status_label.color = (0.8, 0.2, 0.2, 1)
                return
            
            self.config_manager.set("schedule_interval", total_seconds)
            self.status_label.text = f"已保存: 间隔 {minutes}分{seconds}秒"
            self.status_label.color = (0.2, 0.7, 0.2, 1)
        except ValueError:
            self.status_label.text = "错误: 请输入有效数字"
            self.status_label.color = (0.8, 0.2, 0.2, 1)
    
    def toggle_schedule(self, switch, value):
        self.config_manager.set("schedule_enabled", value)
        
        # 使用线程服务(Android和桌面通用)
        if value:
            self.service.start_service()
            print("[定时服务] 已启动")
        else:
            self.service.stop_service()
            print("[定时服务] 已停止")
    
    @mainthread
    def add_schedule_log(self, message, progress=None, timestamp=None):
        """添加定时分析日志到日志区域(线程安全)"""
        print(f"[调试] add_schedule_log被调用: {message}")  # 添加调试信息
        import datetime
        
        # 使用传入的时间戳，如果没有则使用当前时间
        if timestamp:
            if isinstance(timestamp, str):
                # 如果是ISO格式字符串，解析为时间对象
                try:
                    dt = datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    time_str = dt.strftime("%H:%M:%S")
                except:
                    time_str = datetime.datetime.now().strftime("%H:%M:%S")
            else:
                time_str = timestamp.strftime("%H:%M:%S")
        else:
            time_str = datetime.datetime.now().strftime("%H:%M:%S")
        
        # 如果有进度信息，添加到消息中
        if progress is not None:
            display_message = f"{message} [{progress}%]"
        else:
            display_message = message
        
        log_label = Label(
            text=f"[{time_str}] {display_message}",
            size_hint_y=None,
            height=dp(48),
            font_size="14sp",
            color=TEXT_REGULAR,
            halign="left",
            valign="top",
            text_size=(None, None)
        )
        self.schedule_log_container.add_widget(log_label)
        
        # 限制日志数量
        if len(self.schedule_log_container.children) > 30:
            self.schedule_log_container.remove_widget(self.schedule_log_container.children[-1])
    
    def clear_schedule_logs(self):
        """清空定时分析日志"""
        self.schedule_log_container.clear_widgets()
        self.add_schedule_log("定时分析日志已清空")


class HistoryScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db_manager = DatabaseManager()
        self.current_filter = 0  # 默认当天
        self.show_zero_results = False  # 默认不显示0结果
        self.page_size = 20  # 每页20条
        self.current_page = 1
        self.total_pages = 1
        self.filtered_history = []
        
        layout = BoxLayout(orientation="vertical", padding=[dp(15), dp(10), dp(15), dp(10)], spacing=dp(10))
        
        # 标题
        layout.add_widget(Label(
            text="历史记录",
            size_hint_y=0.05,
            font_size="20sp",
            bold=True,
            color=TEXT_PRIMARY
        ))
        
        # 筛选控制区
        filter_layout = BoxLayout(orientation="vertical", size_hint_y=0.15, spacing=dp(8))
        
        # 时间筛选输入行
        time_filter_box = BoxLayout(size_hint_y=0.5, spacing=dp(8))
        
        # 开始时间标签
        start_label = Label(
            text="开始时间:",
            font_size="13sp",
            color=TEXT_PRIMARY,
            size_hint_x=0.15
        )
        time_filter_box.add_widget(start_label)
        
        # 开始时间输入
        self.start_date_input = TextInput(
            text="",
            hint_text="YYYY-MM-DD",
            multiline=False,
            font_size="13sp",
            size_hint_x=0.25
        )
        time_filter_box.add_widget(self.start_date_input)
        
        # 结束时间标签
        end_label = Label(
            text="结束时间:",
            font_size="13sp",
            color=TEXT_PRIMARY,
            size_hint_x=0.15
        )
        time_filter_box.add_widget(end_label)
        
        # 结束时间输入
        self.end_date_input = TextInput(
            text="",
            hint_text="YYYY-MM-DD",
            multiline=False,
            font_size="13sp",
            size_hint_x=0.25
        )
        time_filter_box.add_widget(self.end_date_input)
        
        # 筛选按钮
        filter_btn = Button(
            text="筛选",
            background_color=PRIMARY_COLOR,
            font_size="13sp",
            size_hint_x=0.2,
            background_normal='',
            background_down=''
        )
        filter_btn.bind(on_press=self.apply_date_filter)
        time_filter_box.add_widget(filter_btn)
        
        filter_layout.add_widget(time_filter_box)
        
        # 选项和分页行
        options_box = BoxLayout(size_hint_y=0.5, spacing=dp(8))
        
        # 显示0结果勾选框 - 放在文字旁边
        self.zero_results_checkbox = CheckBox(
            active=False, 
            size_hint_x=None, 
            width=dp(20),
            height=dp(20),
            size_hint_y=None,
            color=(0.2, 0.6, 0.9, 1)  # 蓝色勾选框
        )
        self.zero_results_checkbox.bind(active=self.on_zero_results_toggle)
        
        # 创建一个水平布局放置勾选框和文字
        checkbox_container = BoxLayout(
            orientation='horizontal', 
            size_hint_x=0.35, 
            spacing=dp(5),
            padding=[dp(5), 0, 0, 0]
        )
        checkbox_container.add_widget(self.zero_results_checkbox)
        
        zero_label = Label(
            text="显示0结果",
            font_size="12sp",
            color=TEXT_PRIMARY,
            size_hint_x=None,
            text_size=(None, None),
            halign='left'
        )
        checkbox_container.add_widget(zero_label)
        
        # 分页控制
        self.page_label = Label(
            text="第 1/1 页",
            font_size="15sp",
            color=PRIMARY_COLOR,
            bold=True
        )
        
        self.prev_btn = create_rounded_button(
            text="上一页",
            bg_color=PRIMARY_COLOR,
            font_size="14sp",
            size_hint_x=0.2,
            bold=True
        )
        self.prev_btn.bind(on_press=self.prev_page)
        
        self.next_btn = create_rounded_button(
            text="下一页", 
            bg_color=PRIMARY_COLOR,
            font_size="14sp",
            size_hint_x=0.2,
            bold=True
        )
        self.next_btn.bind(on_press=self.next_page)
        
        options_box.add_widget(checkbox_container)
        options_box.add_widget(self.prev_btn)
        options_box.add_widget(self.page_label)
        options_box.add_widget(self.next_btn)
        
        filter_layout.add_widget(options_box)
        layout.add_widget(filter_layout)
        
        # 统计信息
        self.stats_label = Label(
            text="",
            size_hint_y=0.04,
            font_size="13sp",
            color=TEXT_SECONDARY
        )
        layout.add_widget(self.stats_label)
        
        # 列表
        self.scroll_view = ScrollView(size_hint=(1, 0.76))
        self.history_container = GridLayout(cols=1, spacing=dp(12), size_hint_y=None, padding=[0, dp(5)])
        self.history_container.bind(minimum_height=self.history_container.setter("height"))
        self.scroll_view.add_widget(self.history_container)
        layout.add_widget(self.scroll_view)
        
        self.add_widget(layout)
    
    def on_enter(self):
        # 确保属性已初始化
        if not hasattr(self, 'show_zero_results'):
            self.show_zero_results = False
        # 默认显示当天数据
        import datetime
        today = datetime.datetime.now().date()
        self.start_date_input.text = today.strftime("%Y-%m-%d")
        self.end_date_input.text = today.strftime("%Y-%m-%d")
        self.load_history()
    
    def on_zero_results_toggle(self, checkbox, value):
        """切换显示0结果"""
        self.show_zero_results = value
        self.current_page = 1  # 重置到第一页
        self.load_history()
    
    def apply_date_filter(self, instance):
        """应用日期范围筛选"""
        self.current_page = 1  # 重置到第一页
        self.load_history()
    
    def parse_date(self, date_str):
        """解析日期字符串"""
        try:
            import datetime
            return datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        except:
            return None
    
    def prev_page(self, instance):
        """上一页"""
        if self.current_page > 1:
            self.current_page -= 1
            self.load_history()
    
    def next_page(self, instance):
        """下一页"""
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.load_history()
    
    def get_result_count_color(self, count):
        """根据结果数量返回颜色"""
        if count == 0:
            return TEXT_SECONDARY  # 灰色
        elif count > 3:
            return DANGER_COLOR  # 红色
        else:
            return SUCCESS_COLOR  # 绿色
    
    def load_history(self):
        self.history_container.clear_widgets()
        
        # 获取所有数据
        all_history = self.db_manager.get_history_list(1000)  # 获取更多数据用于分页
        
        # 日期范围筛选
        start_date = self.parse_date(self.start_date_input.text)
        end_date = self.parse_date(self.end_date_input.text)
        
        history = []
        if start_date and end_date:
            # 确保结束时间不小于开始时间
            if end_date < start_date:
                start_date, end_date = end_date, start_date
            
            # 包含整天的时间范围
            import datetime
            start_datetime = datetime.datetime.combine(start_date, datetime.time.min)
            end_datetime = datetime.datetime.combine(end_date, datetime.time.max)
            
            for h in all_history:
                try:
                    record_date = datetime.datetime.fromisoformat(h["timestamp"])
                    if start_datetime <= record_date <= end_datetime:
                        history.append(h)
                except:
                    continue
        else:
            # 如果日期格式错误，显示当天数据
            import datetime
            today = datetime.datetime.now().date()
            history = [h for h in all_history if datetime.datetime.fromisoformat(h["timestamp"]).date() == today]
        
        # 0结果筛选
        if not self.show_zero_results:
            history = [h for h in history if h["symbol_count"] > 0]
        
        # 按时间倒序排列（最新的在前面）
        history.sort(key=lambda x: x["timestamp"], reverse=True)
        
        # 分页计算
        self.filtered_history = history
        self.total_pages = max(1, (len(history) + self.page_size - 1) // self.page_size)
        self.current_page = min(self.current_page, self.total_pages)
        
        start_idx = (self.current_page - 1) * self.page_size
        end_idx = start_idx + self.page_size
        page_history = history[start_idx:end_idx]
        
        # 更新统计和分页信息
        if start_date and end_date:
            date_range_text = f"{start_date.strftime('%m-%d')} 至 {end_date.strftime('%m-%d')}"
        else:
            date_range_text = "日期格式错误"
        
        zero_text = "含0结果" if self.show_zero_results else "不含0结果"
        self.stats_label.text = f"{date_range_text} {zero_text}: 共 {len(history)} 条"
        self.page_label.text = f"第 {self.current_page}/{self.total_pages} 页"
        
        # 更新分页按钮状态
        self.update_pagination_buttons()
        
        if not page_history:
            self.history_container.add_widget(Label(
                text="暂无历史记录",
                size_hint_y=None,
                height=dp(72),
                color=TEXT_SECONDARY
            ))
            return
        
        for h in page_history:
            # 外层wrapper
            item_wrapper = BoxLayout(
                orientation="horizontal",
                size_hint_y=None,
                height=dp(100),
                padding=0
            )
            
            from kivy.graphics import Color, RoundedRectangle
            with item_wrapper.canvas.before:
                Color(*BG_WHITE)
                item_wrapper.rect = RoundedRectangle(pos=item_wrapper.pos, size=item_wrapper.size, radius=[dp(10)])
            item_wrapper.bind(pos=lambda obj, val: setattr(obj.rect, "pos", val))
            item_wrapper.bind(size=lambda obj, val: setattr(obj.rect, "size", val))
            
            # 内容容器
            item = BoxLayout(padding=[dp(15), dp(10)], spacing=dp(12))
            
            # 时间和数量信息
            timestamp = h["timestamp"][:16].replace("T", " ")
            duration = h.get("duration", 0)
            info_box = BoxLayout(orientation="vertical", spacing=dp(4))
            info_box.add_widget(Label(
                text=timestamp,
                font_size="14sp",
                color=TEXT_PRIMARY,
                size_hint_y=None,
                height=dp(32)
            ))
            
            # 使用颜色控制的结果数量
            count_color = self.get_result_count_color(h["symbol_count"])
            if duration > 0:
                info_box.add_widget(Label(
                    text=f"找到 {h['symbol_count']} 个币种 | 耗时 {duration:.1f}秒",
                    font_size="13sp",
                    color=count_color,
                    size_hint_y=None,
                    height=dp(32)
                ))
            else:
                info_box.add_widget(Label(
                    text=f"找到 {h['symbol_count']} 个币种",
                    font_size="13sp",
                    color=count_color,
                    size_hint_y=None,
                    height=dp(32)
                ))
            item.add_widget(info_box)
            
            btn_view = create_rounded_button(
                text="查看",
                bg_color=PRIMARY_COLOR,
                size_hint_x=0.25,
                font_size="15sp",
                bold=True
            )
            btn_view.bind(on_press=lambda x, record_id=h["id"]: self.view_record(record_id))
            item.add_widget(btn_view)
            
            item_wrapper.add_widget(item)
            self.history_container.add_widget(item_wrapper)
    
    def view_record(self, record_id):
        record = self.db_manager.get_analysis_by_id(record_id)
        if record:
            # 切换到结果页面显示历史记录
            results_screen = self.manager.get_screen("results")
            results_screen.set_from_screen("history")  # 设置来源页面
            results_screen.display_results(record["results"])
            # 通过底部导航栏切换
            app = App.get_running_app()
            if hasattr(app.root, 'nav_bar'):
                app.root.nav_bar.switch_screen("results")
    
    def update_pagination_buttons(self):
        """更新分页按钮的启用/禁用状态"""
        # 获取分页按钮的引用（需要在load_history中保存）
        if hasattr(self, 'prev_btn') and hasattr(self, 'next_btn'):
            # 更新上一页按钮
            if self.current_page <= 1:
                self.prev_btn.disabled = True
                self.prev_btn.background_color = INFO_COLOR  # 灰色
            else:
                self.prev_btn.disabled = False
                self.prev_btn.background_color = PRIMARY_COLOR  # 蓝色
            
            # 更新下一页按钮
            if self.current_page >= self.total_pages:
                self.next_btn.disabled = True
                self.next_btn.background_color = INFO_COLOR  # 灰色
            else:
                self.next_btn.disabled = False
                self.next_btn.background_color = PRIMARY_COLOR  # 蓝色


class SettingsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config_manager = ConfigManager()
        
        layout = BoxLayout(orientation="vertical", padding=dp(25), spacing=dp(15))
        
        layout.add_widget(Label(
            text="设置",
            size_hint_y=0.05,
            font_size="22sp",
            bold=True,
            color=(0, 0.63, 0.84, 1)
        ))
        
        scroll = ScrollView(size_hint=(1, 0.75))
        scroll_layout = GridLayout(cols=1, spacing=dp(10), size_hint_y=None, padding=dp(10))
        scroll_layout.bind(minimum_height=scroll_layout.setter("height"))
        
        # 分析参数分组
        scroll_layout.add_widget(Label(
            text="分析参数",
            size_hint_y=None,
            height=dp(36),
            font_size="16sp",
            bold=True,
            color=(0.1, 0.1, 0.1, 1)
        ))
        
        self.inputs = {}
        
        params = [
            ("MIN_CHANGE_PERCENT", "最小涨幅 (%)", "100"),
            ("LIQUIDITY_THRESHOLD_USDT", "流动性阈值 (USDT)", "1000000"),
            ("MAX_ANALYZE_SYMBOLS", "最大分析数量", "500"),
            ("CACHE_EXPIRY", "缓存过期时间 (秒)", "3600"),
            ("REQUEST_DELAY", "API请求延迟 (秒)", "0.15")
        ]
        
        for key, label, default in params:
            box = BoxLayout(size_hint_y=None, height=dp(70), spacing=dp(10))
            box.add_widget(Label(
                text=label, 
                size_hint_x=0.5, 
                font_size="14sp", 
                color=TEXT_PRIMARY,
                halign="left",
                valign="middle"
            ))
            
            input_field = TextInput(
                text=str(self.config_manager.get(key, default)),
                multiline=False,
                size_hint_x=0.5,
                font_size='18sp'
            )
            self.inputs[key] = input_field
            box.add_widget(input_field)
            scroll_layout.add_widget(box)
        
        # 定时分析设置分组
        scroll_layout.add_widget(Label(
            text="定时分析设置",
            size_hint_y=None,
            height=dp(48),
            font_size="16sp",
            bold=True,
            color=(0.1, 0.1, 0.1, 1)
        ))
        
        # 启用定时分析开关
        schedule_switch_box = BoxLayout(size_hint_y=None, height=dp(60), spacing=dp(10))
        schedule_switch_box.add_widget(Label(
            text="启用定时分析",
            size_hint_x=0.7,
            font_size="14sp",
            color=TEXT_PRIMARY,
            halign="left",
            valign="middle"
        ))
        self.schedule_switch = Switch(active=self.config_manager.get("schedule_enabled", False))
        self.schedule_switch.bind(active=self.toggle_schedule)
        schedule_switch_box.add_widget(self.schedule_switch)
        scroll_layout.add_widget(schedule_switch_box)
        
        # 运行间隔设置
        interval_box = BoxLayout(size_hint_y=None, height=dp(70), spacing=dp(10))
        interval_box.add_widget(Label(
            text="运行间隔(分:秒)",
            size_hint_x=0.35,
            font_size="14sp",
            color=TEXT_PRIMARY,
            halign="left",
            valign="middle"
        ))
        
        current_interval = self.config_manager.get("schedule_interval", 7200)
        minutes = current_interval // 60
        seconds = current_interval % 60
        
        self.minutes_input = TextInput(
            text=str(minutes),
            multiline=False,
            input_filter='int',
            size_hint_x=0.25,
            font_size='16sp'
        )
        interval_box.add_widget(self.minutes_input)
        
        interval_box.add_widget(Label(text=":", size_hint_x=0.1, color=TEXT_PRIMARY, font_size='16sp'))
        
        self.seconds_input = TextInput(
            text=str(seconds),
            multiline=False,
            input_filter='int',
            size_hint_x=0.25,
            font_size='16sp'
        )
        interval_box.add_widget(self.seconds_input)
        scroll_layout.add_widget(interval_box)
        
        # 通知设置
        notify_box1 = BoxLayout(size_hint_y=None, height=dp(60), spacing=dp(10))
        notify_box1.add_widget(Label(
            text="发现变化时通知",
            size_hint_x=0.7,
            font_size="14sp",
            color=TEXT_PRIMARY,
            halign="left",
            valign="middle"
        ))
        self.notify_change_switch = Switch(active=self.config_manager.get("notify_on_change", True))
        self.notify_change_switch.bind(active=lambda sw, val: self.config_manager.set("notify_on_change", val, auto_save=False))
        notify_box1.add_widget(self.notify_change_switch)
        scroll_layout.add_widget(notify_box1)
        
        notify_box2 = BoxLayout(size_hint_y=None, height=dp(60), spacing=dp(10))
        notify_box2.add_widget(Label(
            text="分析完成后通知",
            size_hint_x=0.7,
            font_size="14sp",
            color=TEXT_PRIMARY,
            halign="left",
            valign="middle"
        ))
        self.notify_complete_switch = Switch(active=self.config_manager.get("notify_on_complete", True))
        self.notify_complete_switch.bind(active=lambda sw, val: self.config_manager.set("notify_on_complete", val, auto_save=False))
        notify_box2.add_widget(self.notify_complete_switch)
        scroll_layout.add_widget(notify_box2)
        
        # Server酱设置分组
        scroll_layout.add_widget(Label(
            text="Server酱设置",
            size_hint_y=None,
            height=dp(48),
            font_size="16sp",
            bold=True,
            color=(0.1, 0.1, 0.1, 1)
        ))
        
        # 启用Server酱开关
        serverchan_switch_box = BoxLayout(size_hint_y=None, height=dp(60), spacing=dp(10))
        serverchan_switch_box.add_widget(Label(
            text="启用Server酱通知",
            size_hint_x=0.7,
            font_size="14sp",
            color=TEXT_PRIMARY,
            halign="left",
            valign="middle"
        ))
        serverchan_switch = Switch(active=self.config_manager.get("serverchan_enabled", True))
        serverchan_switch.bind(active=lambda sw, val: self.config_manager.set("serverchan_enabled", val))
        serverchan_switch_box.add_widget(serverchan_switch)
        scroll_layout.add_widget(serverchan_switch_box)
        
        # SendKey
        sendkey_box = BoxLayout(size_hint_y=None, height=dp(70), spacing=dp(10))
        sendkey_box.add_widget(Label(
            text="SendKey", 
            size_hint_x=0.35, 
            font_size="14sp", 
            color=TEXT_PRIMARY,
            halign="left",
            valign="middle"
        ))
        sendkey_input = TextInput(
            text=str(self.config_manager.get("serverchan_key", "")),
            multiline=False,
            size_hint_x=0.65,
            font_size='16sp',
            hint_text="sctp开头的密钥"
        )
        self.inputs["serverchan_key"] = sendkey_input
        sendkey_box.add_widget(sendkey_input)
        scroll_layout.add_widget(sendkey_box)
        
        # 通知标题
        scroll_layout.add_widget(Label(
            text="通知标题模板",
            size_hint_y=None,
            height=dp(36),
            font_size="13sp",
            color=TEXT_SECONDARY,
            halign="left"
        ))
        title_input = TextInput(
            text=str(self.config_manager.get("serverchan_title", "币安分析完成")),
            multiline=False,
            size_hint_y=None,
            height=dp(60),
            font_size='16sp',
            hint_text="通知标题"
        )
        self.inputs["serverchan_title"] = title_input
        scroll_layout.add_widget(title_input)
        
        # 通知正文
        scroll_layout.add_widget(Label(
            text="通知正文模板 (支持{count}变量)",
            size_hint_y=None,
            height=dp(36),
            font_size="13sp",
            color=TEXT_SECONDARY,
            halign="left"
        ))
        content_input = TextInput(
            text=str(self.config_manager.get("serverchan_content", "找到 {count} 个符合条件的交易对")),
            multiline=True,
            size_hint_y=None,
            height=dp(120),
            font_size='16sp',
            hint_text="通知内容,可使用{count}表示币种数量"
        )
        self.inputs["serverchan_content"] = content_input
        scroll_layout.add_widget(content_input)
        
        scroll.add_widget(scroll_layout)
        layout.add_widget(scroll)
        
        btn_box = BoxLayout(size_hint_y=0.10, spacing=dp(15), padding=[dp(10), 0])
        
        btn_save = create_rounded_button(
            text="保存设置",
            bg_color=PRIMARY_COLOR,
            font_size="17sp",
            bold=True
        )
        btn_save.bind(on_press=self.save_settings)
        btn_box.add_widget(btn_save)
        
        btn_reset = create_rounded_button(
            text="恢复默认",
            bg_color=INFO_COLOR,
            font_size="17sp",
            bold=True
        )
        btn_reset.bind(on_press=self.reset_settings)
        btn_box.add_widget(btn_reset)
        
        layout.add_widget(btn_box)
        
        self.status_label = Label(
            text="",
            size_hint_y=0.06,
            font_size="16sp"
        )
        layout.add_widget(self.status_label)
        
        self.add_widget(layout)
    
    def save_settings(self, instance):
        try:
            # 准备所有配置，一次性保存
            config_to_save = {}
            
            # 收集分析参数
            for key, input_field in self.inputs.items():
                value_str = input_field.text.strip()
                if key in ["serverchan_key", "serverchan_title", "serverchan_content"]:
                    value = value_str
                elif key == "REQUEST_DELAY":
                    value = float(value_str)
                elif key == "MIN_CHANGE_PERCENT":
                    value = float(value_str)
                else:
                    value = int(value_str)
                config_to_save[key] = value
                print(f"[调试] 准备保存配置 {key}: {value}")
            
            # 收集定时设置
            try:
                minutes = int(self.minutes_input.text or "0")
                seconds = int(self.seconds_input.text or "0")
                total_seconds = minutes * 60 + seconds
                
                if total_seconds < 10:
                    self.status_label.text = "错误: 间隔不能少于10秒"
                    self.status_label.color = (0.8, 0.2, 0.2, 1)
                    return
                
                config_to_save["schedule_interval"] = total_seconds
            except ValueError:
                self.status_label.text = "错误: 时间间隔格式错误"
                self.status_label.color = (0.8, 0.2, 0.2, 1)
                return
            
            # 添加通知开关状态
            config_to_save["notify_on_change"] = self.notify_change_switch.active
            config_to_save["notify_on_complete"] = self.notify_complete_switch.active
            config_to_save["schedule_enabled"] = self.schedule_switch.active
            
            # 批量保存所有配置
            if self.config_manager.set_batch(config_to_save):
                self.status_label.text = "✓ 所有设置已保存"
                self.status_label.color = (0.2, 0.7, 0.2, 1)
                print(f"[调试] 批量保存成功，共 {len(config_to_save)} 项配置")
                
                # 如果定时服务正在运行，需要重启以应用新的间隔设置
                if config_to_save.get("schedule_enabled", False):
                    try:
                        from service import get_service
                        service = get_service()
                        if service.is_running:
                            print("[设置] 重启定时服务以应用新的间隔设置")
                            service.stop_service()
                            import time
                            time.sleep(1)  # 等待1秒确保完全停止
                            service.start_service()
                            self.status_label.text = "✓ 设置已保存，定时服务已重启"
                    except Exception as e:
                        print(f"[设置] 重启定时服务失败: {e}")
                        self.status_label.text = "✓ 设置已保存，但重启服务失败"
            else:
                self.status_label.text = "✗ 保存失败"
                self.status_label.color = (0.8, 0.2, 0.2, 1)
                
        except ValueError as e:
            self.status_label.text = "输入格式错误"
            self.status_label.color = (0.8, 0.2, 0.2, 1)
            print(f"[调试] 保存出错: {e}")
    
    def reset_settings(self, instance):
        self.config_manager.reset_to_default()
        for key, input_field in self.inputs.items():
            input_field.text = str(self.config_manager.get(key))
        
        # 重置定时设置
        self.schedule_switch.active = self.config_manager.get("schedule_enabled", False)
        current_interval = self.config_manager.get("schedule_interval", 7200)
        minutes = current_interval // 60
        seconds = current_interval % 60
        self.minutes_input.text = str(minutes)
        self.seconds_input.text = str(seconds)
        self.notify_change_switch.active = self.config_manager.get("notify_on_change", True)
        self.notify_complete_switch.active = self.config_manager.get("notify_on_complete", True)
    
    def toggle_schedule(self, switch, value):
        """切换定时分析开关"""
        self.config_manager.set("schedule_enabled", value, auto_save=False)
        
        # 获取服务实例
        from service import get_service
        service = get_service()
        
        if value:
            service.start_service()
            print("[定时服务] 已启动")
        else:
            service.stop_service()
            print("[定时服务] 已停止")
    
    
        self.status_label.text = "✓ 已恢复默认设置"
        self.status_label.color = (0.2, 0.7, 0.2, 1)


class IconWidget(Widget):
    """简单的图形图标组件"""
    def __init__(self, icon_type, color=(0.6, 0.6, 0.6, 1), **kwargs):
        super().__init__(**kwargs)
        self.icon_type = icon_type
        self.color = color
        self.size_hint = (None, None)
        self.size = (dp(30), dp(30))
        self.bind(pos=self.update_graphics)
        self.bind(size=self.update_graphics)
        self.update_graphics()
    
    def update_graphics(self, *args):
        """更新图形"""
        self.canvas.clear()
        from kivy.graphics import Color, Line, Ellipse, Rectangle
        
        with self.canvas:
            Color(*self.color)
            
            if self.icon_type == "history":
                # 历史图标 - 简单的书本形状
                Line(rectangle=(self.x + dp(5), self.y + dp(5), self.width - dp(10), self.height - dp(10)), width=dp(2))
                Line(points=[self.x + dp(5), self.y + self.height/2, 
                           self.x + self.width - dp(5), self.y + self.height/2], width=dp(1))
                
            elif self.icon_type == "schedule":
                # 定时图标 - 时钟形状
                Ellipse(pos=(self.x + dp(3), self.y + dp(3)), 
                       size=(self.width - dp(6), self.height - dp(6)))
                Line(points=[self.center_x, self.center_y,
                           self.center_x, self.y + dp(10)], width=dp(2))
                Line(points=[self.center_x, self.center_y,
                           self.x + self.width - dp(10), self.center_y], width=dp(2))
                
            elif self.icon_type == "home":
                # 主页图标 - 房子形状
                points = [self.center_x, self.y + dp(5),
                         self.x + dp(5), self.y + self.height/2,
                         self.x + dp(5), self.y + self.height - dp(5),
                         self.x + self.width - dp(5), self.y + self.height - dp(5),
                         self.x + self.width - dp(5), self.y + self.height/2]
                Line(points=points, width=dp(2))
                
            elif self.icon_type == "settings":
                # 设置图标 - 齿轮形状
                Ellipse(pos=(self.x + dp(8), self.y + dp(8)), 
                       size=(self.width - dp(16), self.height - dp(16)))
                # 画几个齿
                for i in range(8):
                    angle = i * 45
                    import math
                    x1 = self.center_x + math.cos(math.radians(angle)) * (self.width/2 - dp(2))
                    y1 = self.center_y + math.sin(math.radians(angle)) * (self.height/2 - dp(2))
                    x2 = self.center_x + math.cos(math.radians(angle)) * (self.width/2 - dp(6))
                    y2 = self.center_y + math.sin(math.radians(angle)) * (self.height/2 - dp(6))
                    Line(points=[x1, y1, x2, y2], width=dp(2))


class NavButton(ButtonBehavior, BoxLayout):
    """导航按钮"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def on_press(self):
        # 点击时改变透明度
        anim = Animation(opacity=0.7, duration=0.1)
        anim.start(self)
    
    def on_release(self):
        # 释放时恢复透明度
        anim = Animation(opacity=1.0, duration=0.1)
        anim.start(self)


class BottomNavBar(BoxLayout):
    """B站风格底部导航栏"""
    def __init__(self, screen_manager, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "horizontal"
        self.size_hint_y = 0.11
        self.padding = [0, dp(8), 0, dp(8)]
        self.spacing = 0
        self.screen_manager = screen_manager
        self._initialized = False  # 防止重复初始化的标志
        
        # 设置导航栏背景色和阴影效果
        from kivy.graphics import Color, Rectangle, Line, RoundedRectangle
        with self.canvas.before:
            # 阴影效果
            Color(0, 0, 0, 0.1)
            self.shadow = RoundedRectangle(
                pos=(self.pos[0], self.pos[1] - dp(2)),
                size=(self.size[0], self.size[1]),
                radius=[dp(10), dp(10), 0, 0]
            )
            # 白色背景
            Color(1, 1, 1, 0.95)
            self.rect = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[dp(10), dp(10), 0, 0]
            )
            # 顶部分割线
            Color(0.9, 0.9, 0.9, 1)
            self.border_line = Line(
                points=[self.pos[0], self.pos[1] + self.size[1], 
                       self.pos[0] + self.size[0], self.pos[1] + self.size[1]],
                width=dp(1)
            )
        
        self.bind(pos=self._update_graphics)
        self.bind(size=self._update_graphics)
    
    def _update_graphics(self, *args):
        """更新图形元素位置"""
        if hasattr(self, 'shadow'):
            self.shadow.pos = (self.pos[0], self.pos[1] - dp(2))
            self.shadow.size = self.size
        if hasattr(self, 'rect'):
            self.rect.pos = self.pos
            self.rect.size = self.size
        if hasattr(self, 'border_line'):
            self.border_line.points = [
                self.pos[0], self.pos[1] + self.size[1], 
                self.pos[0] + self.size[0], self.pos[1] + self.size[1]
            ]
        
        # 创建导航按钮（只初始化一次）
        if not self._initialized:
            self.nav_buttons = {}
            nav_items = [
                ("history", "历史", "📚"),
                ("schedule", "定时", "⏰"),
                ("home", "主页", "🏠"),
                ("settings", "设置", "⚙️")
            ]
            
            for screen_name, label, icon in nav_items:
                # 创建垂直布局容器
                container = BoxLayout(orientation="vertical", padding=[dp(8), dp(6)])
                
                # 图标标签 - 使用emoji
                icon_label = Label(
                    text=icon,
                    font_name="Emoji",  # 使用emoji字体
                    font_size="24sp",
                    size_hint_y=0.65,
                    color=(0.6, 0.6, 0.6, 1)
                )
                
                # 文字标签
                text_label = Label(
                    text=label,
                    font_size="10sp",
                    size_hint_y=0.35,
                    color=(0.6, 0.6, 0.6, 1),
                    bold=True
                )
                
                container.add_widget(icon_label)
                container.add_widget(text_label)
                
                # 创建透明按钮
                btn = NavButton(orientation="vertical", size_hint_x=1)  # 每个按钮平均分配宽度
                btn.add_widget(container)
                btn.bind(on_press=lambda x, s=screen_name: self.switch_screen(s))
                
                # 保存引用
                self.nav_buttons[screen_name] = {
                    'button': btn,
                    'icon': icon_label,
                    'text': text_label
                }
                
                self.add_widget(btn)
            
            # 标记为已初始化
            self._initialized = True
        
        # 默认选中主页
        self.set_active("home")
    
    def switch_screen(self, screen_name):
        self.screen_manager.current = screen_name
        self.set_active(screen_name)
    
    def set_active(self, screen_name):
        """设置激活状态"""
        for name, widgets in self.nav_buttons.items():
            if name == screen_name:
                # 激活状态 - 现代蓝色渐变
                widgets['icon'].color = (0.33, 0.73, 0.93, 1)  # Material Blue 400
                widgets['text'].color = (0.33, 0.73, 0.93, 1)
                # 增加图标大小以突出激活状态
                widgets['icon'].font_size = "26sp"
            else:
                # 未激活状态 - 柔和灰色
                widgets['icon'].color = (0.55, 0.55, 0.55, 1)
                widgets['text'].color = (0.55, 0.55, 0.55, 1)
                # 恢复正常大小
                widgets['icon'].font_size = "24sp"


class MainContainer(BoxLayout):
    """主容器,包含Screen Manager和底部导航栏"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        
        # 创建ScreenManager
        self.screen_manager = ScreenManager()
        self.screen_manager.add_widget(HomeScreen(name="home"))
        self.screen_manager.add_widget(ResultsScreen(name="results"))
        self.screen_manager.add_widget(HistoryScreen(name="history"))
        self.screen_manager.add_widget(ScheduleScreen(name="schedule"))
        self.screen_manager.add_widget(SettingsScreen(name="settings"))
        
        # 添加ScreenManager
        self.add_widget(self.screen_manager)
        
        # 创建底部导航栏
        self.nav_bar = BottomNavBar(self.screen_manager)
        self.add_widget(self.nav_bar)


class BinanceAnalyzerApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.wake_lock = None
    
    def build(self):
        return MainContainer()
    
    def on_start(self):
        # Android运行时权限检查和请求
        self.request_android_permissions()
        
        # 设备品牌检测和优化
        try:
            from iqoo_optimizer import apply_brand_specific_optimization
            apply_brand_specific_optimization()
        except Exception as e:
            print(f"[设备优化] 优化器加载失败: {e}")
        
        # 获取主页和定时页面实例并设置定时服务日志回调
        home_screen = self.root.screen_manager.get_screen("home")
        schedule_screen = self.root.screen_manager.get_screen("schedule")
        service = get_service()
        service.log_callback = home_screen.add_log
        service.schedule_log_callback = schedule_screen.add_schedule_log
        
        config_manager = ConfigManager()
        if config_manager.get("schedule_enabled", False):
            service.start_service()
        
        # 处理通知点击跳转
        self.handle_notification_intent()
        
        # 启动前台服务（24小时保活）
        self.start_foreground_service()
        
        # 获取WakeLock保持后台运行
        self.acquire_wakelock()
        
        # 根据配置决定是否自动最小化
        if config_manager.get("auto_minimize", False):
            minimize_delay = config_manager.get("minimize_delay", 0.5)
            Clock.schedule_once(lambda dt: self.minimize_to_background(), minimize_delay)
    
    def handle_notification_intent(self):
        """处理通知点击跳转"""
        try:
            from jnius import autoclass
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            activity = PythonActivity.mActivity
            intent = activity.getIntent()
            
            if intent:
                # 获取Intent中的额外参数
                notification_action = intent.getStringExtra("notification_action")
                
                if notification_action == "open_results":
                    print("[通知跳转] 检测到通知点击，跳转到结果页面")
                    # 延迟跳转，确保UI已完全初始化
                    Clock.schedule_once(lambda dt: self._navigate_to_results(), 0.5)
                else:
                    print(f"[通知跳转] 未知操作: {notification_action}")
        except ImportError:
            print("[通知跳转] 非Android平台，跳过Intent检查")
        except Exception as e:
            print(f"[通知跳转] Intent处理失败: {e}")
    
    def _navigate_to_results(self):
        """导航到结果页面"""
        try:
            screen_manager = self.root.screen_manager
            screen_manager.current = "results"
            print("[通知跳转] 已跳转到结果页面")
        except Exception as e:
            print(f"[通知跳转] 页面跳转失败: {e}")
    
    def acquire_wakelock(self):
        """获取WakeLock，防止系统休眠，确保后台和锁屏保活"""
        try:
            from jnius import autoclass
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            
            # 检测平台
            import platform
            if platform == 'android':
                # Android环境下获取WakeLock
                try:
                    from android_service import acquire_wakelock
                    self.wake_lock = acquire_wakelock()
                    if self.wake_lock:
                        print("[WakeLock] Android环境WakeLock已获取")
                    else:
                        print("[WakeLock] Android环境WakeLock获取失败")
                except Exception as e:
                    print(f"[WakeLock] Android环境WakeLock获取异常: {e}")
                    self.wake_lock = None
                return
            
            # 非Android环境（如Windows测试）才获取WakeLock
            Context = autoclass('android.content.Context')
            PowerManager = autoclass('android.os.PowerManager')
            
            activity = PythonActivity.mActivity
            power_manager = activity.getSystemService(Context.POWER_SERVICE)
            
            # 创建WakeLock (PARTIAL_WAKE_LOCK: CPU保持运行，屏幕可以关闭)
            self.wake_lock = power_manager.newWakeLock(
                PowerManager.PARTIAL_WAKE_LOCK,
                'BinanceAnalyzer::AppWakeLock'
            )
            self.wake_lock.acquire()
            print("[WakeLock] 已获取，应用将在后台和锁屏时保持运行")
        except ImportError:
            print("[WakeLock] 非Android平台，跳过WakeLock获取")
        except Exception as e:
            print(f"[WakeLock] 获取失败: {e}")
            import traceback
            traceback.print_exc()
    
    def release_wakelock(self):
        """释放WakeLock"""
        if self.wake_lock:
            try:
                import platform
                if platform == 'android':
                    # Android环境下释放WakeLock
                    try:
                        self.wake_lock.release()
                        print("[WakeLock] Android环境WakeLock已释放")
                    except Exception as e:
                        print(f"[WakeLock] Android环境WakeLock释放异常: {e}")
                else:
                    # 非Android环境释放WakeLock
                    self.wake_lock.release()
                    print("[WakeLock] 已释放")
            except Exception as e:
                print(f"[WakeLock] 释放失败: {e}")
    
    def minimize_to_background(self):
        """将应用最小化到后台，尽量不显示在最近任务中"""
        try:
            from jnius import autoclass
            
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            Intent = autoclass('android.content.Intent')
            
            activity = PythonActivity.mActivity
            
            # 方法1: 将Activity移到后台
            activity.moveTaskToBack(True)
            print("[后台运行] 应用已最小化到后台")
            
            # 方法2: 设置Activity为不显示在最近任务（需要在启动时设置）
            # 这个方法需要修改AndroidManifest.xml，在Kivy中较难实现
            
            # 方法3: 针对iQOO/vivo手机的特殊优化
            try:
                manufacturer = self._get_manufacturer()
                if manufacturer in ['vivo', 'iqoo']:
                    print("[后台运行] 检测到iQOO/vivo设备，应用优化建议：")
                    print("  1. i管家 → 应用管理 → 权限管理 → 自启动 → 开启")
                    print("  2. i管家 → 省电管理 → 后台高耗电 → 允许")
                    print("  3. 设置 → 电池 → 后台耗电管理 → 允许后台高耗电")
            except:
                pass
            
            return True
            
        except ImportError:
            print("[后台运行] 非Android平台，跳过")
            return False
        except Exception as e:
            print(f"[后台运行] 最小化失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _get_manufacturer(self):
        """获取设备厂商"""
        try:
            from jnius import autoclass
            Build = autoclass('android.os.Build')
            return Build.MANUFACTURER.lower()
        except:
            return "unknown"
    
    def start_foreground_service(self):
        """启动前台服务，实现24小时不间断运行"""
        try:
            from jnius import autoclass
            from datetime import datetime
            
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            NotificationBuilder = autoclass('android.app.Notification$Builder')
            NotificationChannel = autoclass('android.app.NotificationChannel')
            NotificationManager = autoclass('android.app.NotificationManager')
            Context = autoclass('android.content.Context')
            Intent = autoclass('android.content.Intent')
            PendingIntent = autoclass('android.app.PendingIntent')
            Color = autoclass('android.graphics.Color')
            
            activity = PythonActivity.mActivity
            notification_service = activity.getSystemService(Context.NOTIFICATION_SERVICE)
            
            # 创建前台服务通知渠道（高优先级，确保不被系统杀死）
            channel_id = "foreground_service_channel_high"
            channel_name = "24小时后台服务"
            importance = NotificationManager.IMPORTANCE_DEFAULT  # 改为DEFAULT优先级
            
            channel = NotificationChannel(channel_id, channel_name, importance)
            channel.setDescription("保持应用24小时不间断运行")
            channel.enableVibration(False)  # 关闭振动
            channel.enableLights(False)  # 关闭指示灯
            channel.setSound(None, None)  # 关闭声音
            channel.setShowBadge(False)  # 不显示角标
            notification_service.createNotificationChannel(channel)
            
            # 创建点击通知的Intent
            intent = Intent(activity, activity.getClass())
            intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP)
            intent.putExtra("notification_action", "open_home")
            
            try:
                pending_intent = PendingIntent.getActivity(
                    activity, 0, intent,
                    PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE
                )
            except:
                pending_intent = PendingIntent.getActivity(
                    activity, 0, intent,
                    PendingIntent.FLAG_UPDATE_CURRENT
                )
            
            # 创建前台服务通知（更详细的信息）
            current_time = datetime.now().strftime("%H:%M:%S")
            builder = NotificationBuilder(activity, channel_id)
            builder.setContentTitle("🔄 币安分析工具运行中")
            builder.setContentText(f"后台服务已启动 | {current_time}")
            builder.setSmallIcon(activity.getApplicationInfo().icon)
            builder.setContentIntent(pending_intent)
            builder.setOngoing(True)  # 持久通知，不可删除
            builder.setAutoCancel(False)  # 点击后不消失
            builder.setShowWhen(True)  # 显示时间
            builder.setWhen(int(datetime.now().timestamp() * 1000))
            
            # 设置优先级（确保前台服务不被杀死）
            try:
                builder.setPriority(NotificationBuilder.PRIORITY_DEFAULT)
            except:
                pass
            
            # 添加操作按钮（可选）
            try:
                # 停止服务按钮
                stop_intent = Intent(activity, activity.getClass())
                stop_intent.putExtra("action", "stop_service")
                stop_pending = PendingIntent.getActivity(
                    activity, 1, stop_intent,
                    PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE
                )
                # builder.addAction(0, "停止", stop_pending)  # 可选：添加停止按钮
            except:
                pass
            
            notification = builder.build()
            
            # 显示前台服务通知（ID=999，高优先级）
            notification_service.notify(999, notification)
            
            print(f"[前台服务] 已启动 - 24小时保活模式")
            print(f"[前台服务] 通知ID: 999")
            print(f"[前台服务] 优先级: DEFAULT")
            print(f"[前台服务] 启动时间: {current_time}")
            
            return True
            
        except ImportError:
            print("[前台服务] 非Android平台，跳过")
            return False
        except Exception as e:
            print(f"[前台服务] 启动失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def request_android_permissions(self):
        """检查并请求Android权限"""
        try:
            from android.permissions import request_permissions, check_permission, Permission
            
            # 定义所需权限列表
            required_permissions = [
                Permission.POST_NOTIFICATIONS,
                Permission.INTERNET,
                Permission.WRITE_EXTERNAL_STORAGE,
                Permission.READ_EXTERNAL_STORAGE,
                Permission.WAKE_LOCK,
                Permission.FOREGROUND_SERVICE,
                Permission.SCHEDULE_EXACT_ALARM,
                Permission.ACCESS_NETWORK_STATE
            ]
            
            # 检查哪些权限未授予
            permissions_to_request = []
            for perm in required_permissions:
                try:
                    if not check_permission(perm):
                        permissions_to_request.append(perm)
                        print(f"[权限] 需要申请: {perm}")
                except:
                    permissions_to_request.append(perm)
            
            # 请求未授予的权限
            if permissions_to_request:
                print(f"[权限] 正在申请 {len(permissions_to_request)} 个权限...")
                request_permissions(permissions_to_request)
                print("[权限] 权限申请对话框已显示")
            else:
                print("[权限] 所有权限已授予")
                
        except ImportError:
            print("[权限] 非Android平台,跳过权限检查")
        except Exception as e:
            print(f"[权限] 权限检查失败: {e}")
            import traceback
            traceback.print_exc()
    
    def on_stop(self):
        service = get_service()
        service.stop_service()
        
        # 释放WakeLock
        self.release_wakelock()


if __name__ == "__main__":
    BinanceAnalyzerApp().run()
