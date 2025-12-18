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

# 注册中文字体
if os.name == 'nt':  # Windows
    LabelBase.register(name='Roboto', 
                      fn_regular='C:\\Windows\\Fonts\\msyh.ttc')  # 微软雅黑
else:  # Android
    LabelBase.register(name='Roboto',
                      fn_regular='/system/fonts/DroidSansFallback.ttf')

from analysis_core import BinanceAnalyzer
from database import DatabaseManager
from notification_manager import NotificationManager
from config_manager import ConfigManager
from service import get_service

Window.clearcolor = (0.95, 0.95, 0.95, 1)


class HomeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config_manager = ConfigManager()
        self.db_manager = DatabaseManager()
        self.notif_manager = NotificationManager()
        
        layout = BoxLayout(orientation="vertical", padding=20, spacing=15)
        
        layout.add_widget(Label(
            text="币安合约分析工具",
            size_hint_y=0.1,
            font_size="24sp",
            bold=True,
            color=(0.1, 0.4, 0.8, 1)
        ))
        
        self.status_label = Label(
            text="最近分析时间: 暂无",
            size_hint_y=0.08,
            font_size="14sp",
            color=(0.3, 0.3, 0.3, 1)
        )
        layout.add_widget(self.status_label)
        
        btn_analyze = Button(
            text="立即分析",
            size_hint_y=0.12,
            background_color=(0.1, 0.6, 0.3, 1),
            font_size="18sp"
        )
        btn_analyze.bind(on_press=self.start_analysis)
        layout.add_widget(btn_analyze)
        
        btn_schedule = Button(
            text="定时设置",
            size_hint_y=0.12,
            background_color=(0.2, 0.5, 0.8, 1),
            font_size="18sp"
        )
        btn_schedule.bind(on_press=lambda x: setattr(self.manager, "current", "schedule"))
        layout.add_widget(btn_schedule)
        
        btn_history = Button(
            text="历史记录",
            size_hint_y=0.12,
            background_color=(0.6, 0.4, 0.2, 1),
            font_size="18sp"
        )
        btn_history.bind(on_press=lambda x: setattr(self.manager, "current", "history"))
        layout.add_widget(btn_history)
        
        btn_settings = Button(
            text="设置",
            size_hint_y=0.12,
            background_color=(0.5, 0.5, 0.5, 1),
            font_size="18sp"
        )
        btn_settings.bind(on_press=lambda x: setattr(self.manager, "current", "settings"))
        layout.add_widget(btn_settings)
        
        self.bottom_status = Label(
            text="状态: 待机中",
            size_hint_y=0.08,
            font_size="14sp",
            color=(0.2, 0.7, 0.2, 1)
        )
        layout.add_widget(self.bottom_status)
        
        self.add_widget(layout)
        self.update_status()
    
    def update_status(self):
        latest = self.db_manager.get_latest_analysis()
        if latest:
            timestamp = latest["timestamp"][:19].replace("T", " ")
            count = latest["symbol_count"]
            self.status_label.text = f"最近分析: {timestamp}\n找到 {count} 个符合条件的币种"
    
    def start_analysis(self, instance):
        self.bottom_status.text = "状态: 分析中..."
        self.bottom_status.color = (0.8, 0.5, 0, 1)
        Thread(target=self._run_analysis, daemon=True).start()
    
    def _run_analysis(self):
        try:
            config = self.config_manager.get_analyzer_config()
            analyzer = BinanceAnalyzer(config=config, callback=self.analysis_callback)
            results = analyzer.analyze()
            
            self.db_manager.save_analysis(results, config)
            
            Clock.schedule_once(lambda dt: self.show_results(results), 0)
            
            if self.config_manager.get("notify_on_complete", True):
                self.notif_manager.notify_analysis_complete(len(results))
        except Exception as e:
            error_msg = str(e)
            Clock.schedule_once(lambda dt: self.show_error(error_msg), 0)
    
    @mainthread
    def analysis_callback(self, message, progress=None):
        if progress is not None:
            self.bottom_status.text = f"状态: {message} [{progress}%]"
        else:
            self.bottom_status.text = f"状态: {message}"
    
    @mainthread
    def show_results(self, results):
        self.bottom_status.text = "状态: 分析完成"
        self.bottom_status.color = (0.2, 0.7, 0.2, 1)
        self.update_status()
        
        results_screen = self.manager.get_screen("results")
        results_screen.display_results(results)
        self.manager.current = "results"
    
    @mainthread
    def show_error(self, error_msg):
        self.bottom_status.text = f"状态: 出错 - {error_msg[:30]}"
        self.bottom_status.color = (0.8, 0.2, 0.2, 1)


class ResultsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation="vertical", padding=10, spacing=10)
        
        top_bar = BoxLayout(size_hint_y=0.08, spacing=10)
        btn_back = Button(text="返回", background_color=(0.5, 0.5, 0.5, 1))
        btn_back.bind(on_press=lambda x: setattr(self.manager, "current", "home"))
        top_bar.add_widget(btn_back)
        self.layout.add_widget(top_bar)
        
        self.results_label = Label(
            text="分析结果",
            size_hint_y=0.06,
            font_size="18sp",
            bold=True
        )
        self.layout.add_widget(self.results_label)
        
        self.scroll_view = ScrollView(size_hint=(1, 0.86))
        self.results_container = GridLayout(cols=1, spacing=10, size_hint_y=None)
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
                height=50
            ))
            return
        
        for i, r in enumerate(results, 1):
            item = BoxLayout(
                orientation="vertical",
                size_hint_y=None,
                height=120,
                padding=10
            )
            item.canvas.before.clear()
            
            from kivy.graphics import Color, Rectangle
            with item.canvas.before:
                Color(1, 1, 1, 1)
                item.rect = Rectangle(pos=item.pos, size=item.size)
            item.bind(pos=lambda obj, val: setattr(obj.rect, "pos", val))
            item.bind(size=lambda obj, val: setattr(obj.rect, "size", val))
            
            symbol_label = Label(
                text=f"#{r['symbol']}",
                size_hint_y=0.3,
                font_size="16sp",
                bold=True,
                color=(0.1, 0.4, 0.8, 1)
            )
            item.add_widget(symbol_label)
            
            gains_text = (
                f"单日: {r['gain_1d']*100:+.1f}%  "
                f"两日: {r['gain_2d']*100:+.1f}%  "
                f"三日: {r['gain_3d']*100:+.1f}%"
            )
            gains_label = Label(
                text=gains_text,
                size_hint_y=0.35,
                font_size="14sp",
                color=(0.3, 0.3, 0.3, 1)
            )
            item.add_widget(gains_label)
            
            conditions_label = Label(
                text=f"触发条件: {', '.join(r['conditions'])}  |  排名: #{i}",
                size_hint_y=0.35,
                font_size="12sp",
                color=(0.6, 0.6, 0.6, 1)
            )
            item.add_widget(conditions_label)
            
            self.results_container.add_widget(item)


class ScheduleScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config_manager = ConfigManager()
        self.service = get_service()
        
        layout = BoxLayout(orientation="vertical", padding=20, spacing=15)
        
        top_bar = BoxLayout(size_hint_y=0.08, spacing=10)
        btn_back = Button(text="返回", background_color=(0.5, 0.5, 0.5, 1))
        btn_back.bind(on_press=lambda x: setattr(self.manager, "current", "home"))
        top_bar.add_widget(btn_back)
        layout.add_widget(top_bar)
        
        layout.add_widget(Label(
            text="定时任务设置",
            size_hint_y=0.08,
            font_size="20sp",
            bold=True,
            color=(0.1, 0.1, 0.1, 1)
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
        
        interval_box = BoxLayout(size_hint_y=0.08, spacing=10)
        current_interval = self.config_manager.get("schedule_interval", 7200)
        minutes = current_interval // 60
        seconds = current_interval % 60
        
        interval_box.add_widget(Label(text="分钟:", size_hint_x=0.2, color=(0.1, 0.1, 0.1, 1)))
        self.minutes_input = TextInput(
            text=str(minutes),
            multiline=False,
            input_filter='int',
            size_hint_x=0.3
        )
        interval_box.add_widget(self.minutes_input)
        
        interval_box.add_widget(Label(text="秒:", size_hint_x=0.2, color=(0.1, 0.1, 0.1, 1)))
        self.seconds_input = TextInput(
            text=str(seconds),
            multiline=False,
            input_filter='int',
            size_hint_x=0.3
        )
        interval_box.add_widget(self.seconds_input)
        layout.add_widget(interval_box)
        
        btn_save_interval = Button(
            text="保存间隔",
            size_hint_y=0.08,
            background_color=(0.2, 0.6, 0.8, 1)
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
        if value:
            self.service.start_service()
        else:
            self.service.stop_service()
        self.next_run_label.text = self._get_next_run_text()
        self.next_run_label.color = (0.1, 0.1, 0.1, 1)


class HistoryScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db_manager = DatabaseManager()
        
        layout = BoxLayout(orientation="vertical", padding=10, spacing=10)
        
        top_bar = BoxLayout(size_hint_y=0.08, spacing=10)
        btn_back = Button(text="返回", background_color=(0.5, 0.5, 0.5, 1))
        btn_back.bind(on_press=lambda x: setattr(self.manager, "current", "home"))
        top_bar.add_widget(btn_back)
        
        btn_refresh = Button(text="刷新", background_color=(0.2, 0.6, 0.8, 1))
        btn_refresh.bind(on_press=lambda x: self.load_history())
        top_bar.add_widget(btn_refresh)
        layout.add_widget(top_bar)
        
        layout.add_widget(Label(
            text="历史记录",
            size_hint_y=0.06,
            font_size="18sp",
            bold=True
        ))
        
        self.scroll_view = ScrollView(size_hint=(1, 0.86))
        self.history_container = GridLayout(cols=1, spacing=10, size_hint_y=None)
        self.history_container.bind(minimum_height=self.history_container.setter("height"))
        self.scroll_view.add_widget(self.history_container)
        layout.add_widget(self.scroll_view)
        
        self.add_widget(layout)
    
    def on_enter(self):
        self.load_history()
    
    def load_history(self):
        self.history_container.clear_widgets()
        history = self.db_manager.get_history_list(50)
        
        if not history:
            self.history_container.add_widget(Label(
                text="暂无历史记录",
                size_hint_y=None,
                height=50
            ))
            return
        
        for h in history:
            item = BoxLayout(
                orientation="horizontal",
                size_hint_y=None,
                height=60,
                padding=10,
                spacing=10
            )
            
            from kivy.graphics import Color, Rectangle
            with item.canvas.before:
                Color(1, 1, 1, 1)
                item.rect = Rectangle(pos=item.pos, size=item.size)
            item.bind(pos=lambda obj, val: setattr(obj.rect, "pos", val))
            item.bind(size=lambda obj, val: setattr(obj.rect, "size", val))
            
            timestamp = h["timestamp"][:19].replace("T", " ")
            info_label = Label(
                text=f"{timestamp}\n找到 {h['symbol_count']} 个币种",
                font_size="13sp"
            )
            item.add_widget(info_label)
            
            btn_view = Button(
                text="查看",
                size_hint_x=0.25,
                background_color=(0.2, 0.6, 0.8, 1)
            )
            btn_view.bind(on_press=lambda x, record_id=h["id"]: self.view_record(record_id))
            item.add_widget(btn_view)
            
            self.history_container.add_widget(item)
    
    def view_record(self, record_id):
        record = self.db_manager.get_analysis_by_id(record_id)
        if record:
            results_screen = self.manager.get_screen("results")
            results_screen.display_results(record["results"])
            self.manager.current = "results"


class SettingsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config_manager = ConfigManager()
        
        layout = BoxLayout(orientation="vertical", padding=20, spacing=10)
        
        top_bar = BoxLayout(size_hint_y=0.06, spacing=10)
        btn_back = Button(text="返回", background_color=(0.5, 0.5, 0.5, 1))
        btn_back.bind(on_press=lambda x: setattr(self.manager, "current", "home"))
        top_bar.add_widget(btn_back)
        layout.add_widget(top_bar)
        
        layout.add_widget(Label(
            text="设置",
            size_hint_y=0.05,
            font_size="20sp",
            bold=True
        ))
        
        scroll = ScrollView(size_hint=(1, 0.75))
        scroll_layout = GridLayout(cols=1, spacing=10, size_hint_y=None, padding=10)
        scroll_layout.bind(minimum_height=scroll_layout.setter("height"))
        
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
            box.add_widget(Label(text=label, size_hint_x=0.5, font_size="14sp", color=(0.1, 0.1, 0.1, 1)))
            
            input_field = TextInput(
                text=str(self.config_manager.get(key, default)),
                multiline=False,
                size_hint_x=0.5
            )
            self.inputs[key] = input_field
            box.add_widget(input_field)
            scroll_layout.add_widget(box)
        
        scroll.add_widget(scroll_layout)
        layout.add_widget(scroll)
        
        btn_box = BoxLayout(size_hint_y=0.08, spacing=10)
        
        btn_save = Button(
            text="保存设置",
            background_color=(0.2, 0.7, 0.3, 1)
        )
        btn_save.bind(on_press=self.save_settings)
        btn_box.add_widget(btn_save)
        
        btn_reset = Button(
            text="恢复默认",
            background_color=(0.8, 0.4, 0.2, 1)
        )
        btn_reset.bind(on_press=self.reset_settings)
        btn_box.add_widget(btn_reset)
        
        layout.add_widget(btn_box)
        
        self.status_label = Label(
            text="",
            size_hint_y=0.06,
            font_size="14sp"
        )
        layout.add_widget(self.status_label)
        
        self.add_widget(layout)
    
    def save_settings(self, instance):
        try:
            for key, input_field in self.inputs.items():
                value_str = input_field.text.strip()
                if key == "REQUEST_DELAY":
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


class BinanceAnalyzerApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(HomeScreen(name="home"))
        sm.add_widget(ResultsScreen(name="results"))
        sm.add_widget(ScheduleScreen(name="schedule"))
        sm.add_widget(HistoryScreen(name="history"))
        sm.add_widget(SettingsScreen(name="settings"))
        return sm
    
    def on_start(self):
        config_manager = ConfigManager()
        if config_manager.get("schedule_enabled", False):
            service = get_service()
            service.start_service()
    
    def on_stop(self):
        service = get_service()
        service.stop_service()


if __name__ == "__main__":
    BinanceAnalyzerApp().run()
