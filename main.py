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
from kivy.clock import Clock, mainthread
from kivy.core.window import Window
from kivy.core.text import LabelBase
from threading import Thread
import traceback
import os
import sys

# 注册中文字体
try:
    if os.name == 'nt':  # Windows
        LabelBase.register(name='Roboto', 
                          fn_regular='C:\\Windows\\Fonts\\msyh.ttc')
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
        btn.bg_rect = RoundedRectangle(pos=btn.pos, size=btn.size, radius=[10])
    
    btn.bind(pos=lambda obj, val: setattr(obj.bg_rect, "pos", val))
    btn.bind(size=lambda obj, val: setattr(obj.bg_rect, "size", val))
    
    return btn


class HomeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config_manager = ConfigManager()
        self.db_manager = DatabaseManager()
        self.notif_manager = NotificationManager()
        
        layout = BoxLayout(orientation="vertical", padding=[20, 15, 20, 15], spacing=12)
        
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
        log_header = BoxLayout(size_hint_y=0.06, spacing=10)
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
        self.log_container = GridLayout(cols=1, spacing=5, size_hint_y=None, padding=[8, 5])
        self.log_container.bind(minimum_height=self.log_container.setter("height"))
        scroll.add_widget(self.log_container)
        layout.add_widget(scroll)
        
        self.add_widget(layout)
        self.update_status()
        self.add_log("系统就绪,等待分析...")
    
    @mainthread
    def add_log(self, message):
        """添加日志到日志区域(线程安全)"""
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        log_label = Label(
            text=f"[{timestamp}] {message}",
            size_hint_y=None,
            height=40,
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
            timestamp = latest["timestamp"][:19].replace("T", " ")
            count = latest["symbol_count"]
            self.status_label.text = f"最近分析: {timestamp} | 找到 {count} 个符合条件的币种"
    
    def start_analysis(self, instance):
        self.add_log("开始分析...")
        Thread(target=self._run_analysis, daemon=True).start()
    
    def _run_analysis(self):
        try:
            config = self.config_manager.get_analyzer_config()
            analyzer = BinanceAnalyzer(config=config, callback=self.analysis_callback)
            results = analyzer.analyze()
            
            self.db_manager.save_analysis(results, config)
            
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
        self.layout = BoxLayout(orientation="vertical", padding=[15, 10, 15, 10], spacing=10)
        
        # 顶部栏:返回按钮+标题
        top_bar = BoxLayout(size_hint_y=0.08, spacing=10)
        btn_back = create_rounded_button(
            text="← 返回",
            bg_color=INFO_COLOR,
            size_hint_x=0.25,
            font_size="15sp"
        )
        btn_back.bind(on_press=lambda x: setattr(self.manager, "current", "home"))
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
        self.results_container = GridLayout(cols=1, spacing=12, size_hint_y=None, padding=[0, 5])
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
                height=80,
                font_size="15sp",
                color=TEXT_SECONDARY
            ))
            return
        
        for i, r in enumerate(results, 1):
            # 外层容器带背景
            card_wrapper = BoxLayout(
                orientation="vertical",
                size_hint_y=None,
                height=180,
                padding=0
            )
            
            # 白色圆角背景
            from kivy.graphics import Color, RoundedRectangle
            with card_wrapper.canvas.before:
                Color(*BG_WHITE)
                card_wrapper.rect = RoundedRectangle(pos=card_wrapper.pos, size=card_wrapper.size, radius=[10])
            card_wrapper.bind(pos=lambda obj, val: setattr(obj.rect, "pos", val))
            card_wrapper.bind(size=lambda obj, val: setattr(obj.rect, "size", val))
            
            # 内容容器
            card = BoxLayout(
                orientation="vertical",
                padding=[15, 12],
                spacing=6
            )
            
            # 顶部: 币种名称和排名
            top_row = BoxLayout(size_hint_y=None, height=30)
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
                
                gain_row = BoxLayout(size_hint_y=None, height=32)
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


class ScheduleScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config_manager = ConfigManager()
        self.service = get_service()
        
        layout = BoxLayout(orientation="vertical", padding=25, spacing=18)
        
        layout.add_widget(Label(
            text="定时任务设置",
            size_hint_y=0.08,
            font_size="22sp",
            bold=True,
            color=(0, 0.63, 0.84, 1)
        ))
        
        switch_box = BoxLayout(size_hint_y=0.08)
        switch_box.add_widget(Label(text="启用定时分析", font_size="16sp", color=(0.1, 0.1, 0.1, 1)))
        self.schedule_switch = Switch(active=self.config_manager.get("schedule_enabled", False))
        self.schedule_switch.bind(active=self.toggle_schedule)
        switch_box.add_widget(self.schedule_switch)
        layout.add_widget(switch_box)
        
        layout.add_widget(Label(
            text="运行间隔（分钟）",
            size_hint_y=0.06,
            font_size="16sp",
            color=(0.1, 0.1, 0.1, 1)
        ))
        
        interval_box = BoxLayout(size_hint_y=None, height=50, spacing=10)
        current_interval = self.config_manager.get("schedule_interval", 7200)
        minutes = current_interval // 60
        seconds = current_interval % 60
        
        interval_box.add_widget(Label(text="分钟:", size_hint_x=0.25, color=TEXT_PRIMARY, font_size='15sp'))
        self.minutes_input = TextInput(
            text=str(minutes),
            multiline=False,
            input_filter='int',
            size_hint_x=0.25,
            font_size='18sp'
        )
        interval_box.add_widget(self.minutes_input)
        
        interval_box.add_widget(Label(text="秒:", size_hint_x=0.25, color=TEXT_PRIMARY, font_size='15sp'))
        self.seconds_input = TextInput(
            text=str(seconds),
            multiline=False,
            input_filter='int',
            size_hint_x=0.25,
            font_size='18sp'
        )
        interval_box.add_widget(self.seconds_input)
        layout.add_widget(interval_box)
        
        btn_save_interval = create_rounded_button(
            text="保存间隔",
            bg_color=PRIMARY_COLOR,
            size_hint_y=0.10,
            font_size="17sp",
            bold=True
        )
        btn_save_interval.bind(on_press=self.save_interval)
        layout.add_widget(btn_save_interval)
        
        notify_box1 = BoxLayout(size_hint_y=0.08)
        notify_box1.add_widget(Label(text="发现变化时通知", font_size="14sp", color=(0.1, 0.1, 0.1, 1)))
        self.notify_change_switch = Switch(active=self.config_manager.get("notify_on_change", True))
        self.notify_change_switch.bind(active=lambda sw, val: self.config_manager.set("notify_on_change", val))
        notify_box1.add_widget(self.notify_change_switch)
        layout.add_widget(notify_box1)
        
        notify_box2 = BoxLayout(size_hint_y=0.08)
        notify_box2.add_widget(Label(text="分析完成后通知", font_size="14sp", color=(0.1, 0.1, 0.1, 1)))
        self.notify_complete_switch = Switch(active=self.config_manager.get("notify_on_complete", True))
        self.notify_complete_switch.bind(active=lambda sw, val: self.config_manager.set("notify_on_complete", val))
        notify_box2.add_widget(self.notify_complete_switch)
        layout.add_widget(notify_box2)
        
        self.next_run_label = Label(
            text=self._get_next_run_text(),
            size_hint_y=0.08,
            font_size="14sp",
            color=(0.1, 0.1, 0.1, 1)
        )
        layout.add_widget(self.next_run_label)
        
        layout.add_widget(Label(size_hint_y=0.3))
        
        self.add_widget(layout)
    
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
                self.next_run_label.text = "错误: 间隔不能少于10秒"
                self.next_run_label.color = (0.8, 0.2, 0.2, 1)
                return
            
            self.config_manager.set("schedule_interval", total_seconds)
            self.next_run_label.text = f"已保存: 间隔 {minutes}分{seconds}秒"
            self.next_run_label.color = (0.2, 0.7, 0.2, 1)
        except ValueError:
            self.next_run_label.text = "错误: 请输入有效数字"
            self.next_run_label.color = (0.8, 0.2, 0.2, 1)
    
    def toggle_schedule(self, switch, value):
        self.config_manager.set("schedule_enabled", value)
        
        # 使用线程服务(Android和桌面通用)
        if value:
            self.service.start_service()
            print("[定时服务] 已启动")
        else:
            self.service.stop_service()
            print("[定时服务] 已停止")
        
        self.next_run_label.text = self._get_next_run_text()
        self.next_run_label.color = TEXT_PRIMARY


class HistoryScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db_manager = DatabaseManager()
        self.current_filter = 2  # 默认近2天
        
        layout = BoxLayout(orientation="vertical", padding=[15, 10, 15, 10], spacing=10)
        
        # 标题
        layout.add_widget(Label(
            text="历史记录",
            size_hint_y=0.06,
            font_size="20sp",
            bold=True,
            color=TEXT_PRIMARY
        ))
        
        # 筛选按钮行
        filter_box = BoxLayout(size_hint_y=0.08, spacing=8)
        self.filter_buttons = {}
        
        for days, label in [(2, "近2天"), (7, "近7天"), (30, "近30天"), (0, "全部")]:
            btn = Button(
                text=label,
                background_color=PRIMARY_COLOR if days == 2 else BG_LIGHT,
                font_size="14sp",
                background_normal='',
                background_down=''
            )
            btn.bind(on_press=lambda x, d=days: self.apply_filter(d))
            self.filter_buttons[days] = btn
            filter_box.add_widget(btn)
        
        layout.add_widget(filter_box)
        
        # 统计信息
        self.stats_label = Label(
            text="",
            size_hint_y=0.04,
            font_size="13sp",
            color=TEXT_SECONDARY
        )
        layout.add_widget(self.stats_label)
        
        # 列表
        self.scroll_view = ScrollView(size_hint=(1, 0.82))
        self.history_container = GridLayout(cols=1, spacing=12, size_hint_y=None, padding=[0, 5])
        self.history_container.bind(minimum_height=self.history_container.setter("height"))
        self.scroll_view.add_widget(self.history_container)
        layout.add_widget(self.scroll_view)
        
        self.add_widget(layout)
    
    def on_enter(self):
        # 确保属性已初始化
        if not hasattr(self, 'current_filter'):
            self.current_filter = 2
        self.load_history()
    
    def apply_filter(self, days):
        """应用筛选"""
        self.current_filter = days
        
        # 更新按钮颜色
        for d, btn in self.filter_buttons.items():
            btn.background_color = PRIMARY_COLOR if d == days else BG_LIGHT
        
        self.load_history()
    
    def load_history(self):
        self.history_container.clear_widgets()
        
        # 获取并筛选数据
        all_history = self.db_manager.get_history_list(500)
        
        if self.current_filter > 0:
            import datetime
            cutoff = datetime.datetime.now() - datetime.timedelta(days=self.current_filter)
            history = [h for h in all_history if datetime.datetime.fromisoformat(h["timestamp"]) >= cutoff]
        else:
            history = all_history[:50]
        
        # 更新统计
        filter_text = f"近{self.current_filter}天" if self.current_filter > 0 else "全部"
        self.stats_label.text = f"{filter_text}: 共 {len(history)} 条" if history else "暂无记录"
        
        if not history:
            self.history_container.add_widget(Label(
                text="暂无历史记录",
                size_hint_y=None,
                height=60,
                color=TEXT_SECONDARY
            ))
            return
        
        for h in history:
            # 外层wrapper
            item_wrapper = BoxLayout(
                orientation="horizontal",
                size_hint_y=None,
                height=85,
                padding=0
            )
            
            from kivy.graphics import Color, RoundedRectangle
            with item_wrapper.canvas.before:
                Color(*BG_WHITE)
                item_wrapper.rect = RoundedRectangle(pos=item_wrapper.pos, size=item_wrapper.size, radius=[10])
            item_wrapper.bind(pos=lambda obj, val: setattr(obj.rect, "pos", val))
            item_wrapper.bind(size=lambda obj, val: setattr(obj.rect, "size", val))
            
            # 内容容器
            item = BoxLayout(padding=[15, 10], spacing=12)
            
            # 时间和数量信息
            timestamp = h["timestamp"][:16].replace("T", " ")
            info_box = BoxLayout(orientation="vertical", spacing=4)
            info_box.add_widget(Label(
                text=timestamp,
                font_size="14sp",
                color=TEXT_PRIMARY,
                size_hint_y=None,
                height=28
            ))
            info_box.add_widget(Label(
                text=f"找到 {h['symbol_count']} 个币种",
                font_size="13sp",
                color=TEXT_SECONDARY,
                size_hint_y=None,
                height=28
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
            results_screen.display_results(record["results"])
            # 通过底部导航栏切换
            app = App.get_running_app()
            if hasattr(app.root, 'nav_bar'):
                app.root.nav_bar.switch_screen("results")


class SettingsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config_manager = ConfigManager()
        
        layout = BoxLayout(orientation="vertical", padding=25, spacing=15)
        
        layout.add_widget(Label(
            text="设置",
            size_hint_y=0.05,
            font_size="22sp",
            bold=True,
            color=(0, 0.63, 0.84, 1)
        ))
        
        scroll = ScrollView(size_hint=(1, 0.75))
        scroll_layout = GridLayout(cols=1, spacing=10, size_hint_y=None, padding=10)
        scroll_layout.bind(minimum_height=scroll_layout.setter("height"))
        
        # 分析参数分组
        scroll_layout.add_widget(Label(
            text="分析参数",
            size_hint_y=None,
            height=30,
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
            box = BoxLayout(size_hint_y=None, height=60, spacing=10)
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
        
        # Server酱设置分组
        scroll_layout.add_widget(Label(
            text="Server酱设置",
            size_hint_y=None,
            height=40,
            font_size="16sp",
            bold=True,
            color=(0.1, 0.1, 0.1, 1)
        ))
        
        # 启用Server酱开关
        serverchan_switch_box = BoxLayout(size_hint_y=None, height=50, spacing=10)
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
        sendkey_box = BoxLayout(size_hint_y=None, height=60, spacing=10)
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
            height=30,
            font_size="13sp",
            color=TEXT_SECONDARY,
            halign="left"
        ))
        title_input = TextInput(
            text=str(self.config_manager.get("serverchan_title", "币安分析完成")),
            multiline=False,
            size_hint_y=None,
            height=50,
            font_size='16sp',
            hint_text="通知标题"
        )
        self.inputs["serverchan_title"] = title_input
        scroll_layout.add_widget(title_input)
        
        # 通知正文
        scroll_layout.add_widget(Label(
            text="通知正文模板 (支持{count}变量)",
            size_hint_y=None,
            height=30,
            font_size="13sp",
            color=TEXT_SECONDARY,
            halign="left"
        ))
        content_input = TextInput(
            text=str(self.config_manager.get("serverchan_content", "找到 {count} 个符合条件的交易对")),
            multiline=True,
            size_hint_y=None,
            height=100,
            font_size='16sp',
            hint_text="通知内容,可使用{count}表示币种数量"
        )
        self.inputs["serverchan_content"] = content_input
        scroll_layout.add_widget(content_input)
        
        scroll.add_widget(scroll_layout)
        layout.add_widget(scroll)
        
        btn_box = BoxLayout(size_hint_y=0.10, spacing=15, padding=[10, 0])
        
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
                self.config_manager.set(key, value)
            
            self.status_label.text = "✓ 设置已保存"
            self.status_label.color = (0.2, 0.7, 0.2, 1)
        except ValueError as e:
            self.status_label.text = "输入格式错误"
            self.status_label.color = (0.8, 0.2, 0.2, 1)
    
    def reset_settings(self, instance):
        self.config_manager.reset_to_default()
        for key, input_field in self.inputs.items():
            input_field.text = str(self.config_manager.get(key))
        self.status_label.text = "✓ 已恢复默认设置"
        self.status_label.color = (0.2, 0.7, 0.2, 1)


class BottomNavBar(BoxLayout):
    """B站风格底部导航栏"""
    def __init__(self, screen_manager, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "horizontal"
        self.size_hint_y = 0.11
        self.padding = [0, 8, 0, 8]
        self.spacing = 0
        self.screen_manager = screen_manager
        
        # 设置导航栏背景色
        from kivy.graphics import Color, Rectangle
        with self.canvas.before:
            Color(1, 1, 1, 1)
            self.rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=lambda obj, val: setattr(self.rect, "pos", val))
        self.bind(size=lambda obj, val: setattr(self.rect, "size", val))
        
        # 创建导航按钮
        self.nav_buttons = {}
        nav_items = [
            ("history", "历史", "📜"),
            ("schedule", "定时", "⏰"),
            ("home", "主页", "🏠"),
            ("settings", "设置", "⚙")
        ]
        
        for screen_name, label, icon in nav_items:
            # 创建垂直布局容器
            container = BoxLayout(orientation="vertical", padding=[5, 5])
            
            # 图标标签
            icon_label = Label(
                text=icon,
                font_size="24sp",
                size_hint_y=0.6,
                color=(0.6, 0.6, 0.6, 1)
            )
            
            # 文字标签
            text_label = Label(
                text=label,
                font_size="11sp",
                size_hint_y=0.4,
                color=(0.6, 0.6, 0.6, 1)
            )
            
            container.add_widget(icon_label)
            container.add_widget(text_label)
            
            # 创建透明按钮
            from kivy.uix.behaviors import ButtonBehavior
            class NavButton(ButtonBehavior, BoxLayout):
                pass
            
            btn = NavButton(orientation="vertical")
            btn.add_widget(container)
            btn.bind(on_press=lambda x, s=screen_name: self.switch_screen(s))
            
            # 保存引用
            self.nav_buttons[screen_name] = {
                'button': btn,
                'icon': icon_label,
                'text': text_label
            }
            
            self.add_widget(btn)
        
        # 默认选中主页
        self.set_active("home")
    
    def switch_screen(self, screen_name):
        self.screen_manager.current = screen_name
        self.set_active(screen_name)
    
    def set_active(self, screen_name):
        """设置激活状态"""
        for name, widgets in self.nav_buttons.items():
            if name == screen_name:
                # 激活状态 - B站粉色
                widgets['icon'].color = (0.98, 0.45, 0.60, 1)
                widgets['text'].color = (0.98, 0.45, 0.60, 1)
            else:
                # 未激活状态 - 灰色
                widgets['icon'].color = (0.6, 0.6, 0.6, 1)
                widgets['text'].color = (0.6, 0.6, 0.6, 1)


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
    def build(self):
        return MainContainer()
    
    def on_start(self):
        # Android运行时权限检查和请求
        self.request_android_permissions()
        
        # 获取主页实例并设置定时服务日志回调
        home_screen = self.root.screen_manager.get_screen("home")
        service = get_service()
        service.log_callback = home_screen.add_log
        
        config_manager = ConfigManager()
        if config_manager.get("schedule_enabled", False):
            service.start_service()
    
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


if __name__ == "__main__":
    BinanceAnalyzerApp().run()
