"""
币安合约三日涨幅分析核心模块
修改自原 three_day_analysis.py，适配移动端使用
"""
import requests
import json
import time
import os
from datetime import datetime


class BinanceAnalyzer:
    """币安分析核心类"""
    
    def __init__(self, config=None, callback=None):
        """
        初始化分析器
        :param config: 配置字典
        :param callback: 进度回调函数 callback(message, progress)
        """
        self.config = config or self._default_config()
        self.callback = callback
        self.cache_file = "exchange_info_cache.json"
        
    def _default_config(self):
        """默认配置"""
        return {
            "MIN_CHANGE_PERCENT": 100.0,
            "LIQUIDITY_THRESHOLD_USDT": 1_000_000,
            "MAX_ANALYZE_SYMBOLS": 500,
            "CACHE_EXPIRY": 3600,
            "REQUEST_DELAY": 0.15
        }
    
    def _log(self, message, progress=None):
        """日志输出"""
        if self.callback:
            self.callback(message, progress)
        else:
            print(message)
    
    def get_active_symbols(self):
        """从文件或 API 获取活跃永续合约列表"""
        now = int(time.time())
        
        # 检查缓存文件是否存在且未过期
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cache = json.load(f)
                if now - cache.get("timestamp", 0) < self.config["CACHE_EXPIRY"]:
                    self._log("从缓存加载exchangeInfo")
                    return set(cache["symbols"])
            except Exception as e:
                self._log(f"?? 缓存文件读取失败: {e}. 重新拉取...")
        
        # 缓存不存在或已过期，重新拉取
        self._log("重新拉取exchangeInfo...")
        try:
            resp = requests.get("https://fapi.binance.com/fapi/v1/exchangeInfo", timeout=10)
            resp.raise_for_status()
            data = resp.json()
            
            active_symbols = []
            for sym in data['symbols']:
                if sym['status'] == 'TRADING' and sym['contractType'] == 'PERPETUAL':
                    active_symbols.append(sym['symbol'])
            
            # 写入缓存文件
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "timestamp": now,
                    "symbols": active_symbols
                }, f, ensure_ascii=False)
            
            self._log(f"? 成功缓存 {len(active_symbols)} 个活跃永续合约")
            return set(active_symbols)
        
        except Exception as e:
            self._log(f"拉取exchangeInfo失败: {e}")
            # 如果有旧缓存文件，即使过期也尝试使用（容错）
            if os.path.exists(self.cache_file):
                try:
                    with open(self.cache_file, 'r', encoding='utf-8') as f:
                        cache = json.load(f)
                    return set(cache.get("symbols", []))
                except:
                    pass
            return set()
    
    def get_klines_data(self, symbol, limit=3):
        """获取指定交易对的K线数据"""
        max_retries = 2
        for attempt in range(max_retries):
            try:
                url = "https://fapi.binance.com/fapi/v1/klines"
                params = {
                    "symbol": symbol,
                    "interval": "1d",
                    "limit": limit
                }
                resp = requests.get(url, params=params, timeout=10)
                resp.raise_for_status()
                raw = resp.json()
                
                # 转换为更易处理的格式
                klines = []
                for k in raw:
                    klines.append({
                        "open_time": k[0],
                        "open": float(k[1]),
                        "high": float(k[2]),
                        "low": float(k[3]),
                        "close": float(k[4]),
                        "volume": float(k[5]),
                        "close_time": k[6],
                        "quote_volume": float(k[7]),
                        "count": int(k[8])
                    })
                
                return klines
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    time.sleep(0.5)
                    continue
                else:
                    return []
            except Exception as e:
                return []
    
    def calculate_gains(self, klines):
        """计算各种涨幅"""
        if len(klines) < 3:
            return None
        
        k_today = klines[-1]
        k_yesterday = klines[-2]
        k_day_before = klines[-3]
        
        # 条件A：最近单日暴涨
        gain_1d = (k_today["close"] / k_today["open"]) - 1
        
        # 条件B：最近两日累计暴涨
        gain_2d = (k_today["close"] / k_yesterday["open"]) - 1
        
        # 条件C：最近三日累计暴涨
        gain_3d = (k_today["close"] / k_day_before["open"]) - 1
        
        return {
            "gain_1d": gain_1d,
            "gain_2d": gain_2d,
            "gain_3d": gain_3d
        }
    
    def check_conditions(self, gains):
        """检查满足的条件"""
        if not gains:
            return []
        
        conditions = []
        min_change = self.config["MIN_CHANGE_PERCENT"] / 100
        
        if gains["gain_1d"] >= min_change:
            conditions.append("A")
        
        if gains["gain_2d"] >= min_change:
            conditions.append("B")
        
        if gains["gain_3d"] >= min_change:
            conditions.append("C")
        
        return conditions
    
    def get_liquid_symbols(self):
        """获取符合流动性条件的活跃永续合约"""
        active_symbols = self.get_active_symbols()
        if not active_symbols:
            self._log("?? 无活跃合约列表，跳过")
            return []
        
        self._log("获取24小时行情数据，过滤低流动性币种...")
        
        max_retries = 3
        tickers = None
        for attempt in range(max_retries):
            try:
                self._log(f"尝试获取24小时行情数据 (第 {attempt + 1}/{max_retries} 次)...")
                resp = requests.get("https://fapi.binance.com/fapi/v1/ticker/24hr", timeout=15)
                resp.raise_for_status()
                tickers = resp.json()
                break
            except requests.exceptions.RequestException as e:
                self._log(f"? 获取 ticker 失败 (第 {attempt + 1} 次): {e}")
                if attempt < max_retries - 1:
                    self._log("等待 5 秒后重试...")
                    time.sleep(5)
                else:
                    self._log("? 所有重试均失败，跳过流动性过滤")
                    return list(active_symbols)[:self.config["MAX_ANALYZE_SYMBOLS"]]
        
        if not tickers:
            self._log("? 未能获取到行情数据")
            return []
        
        liquid_symbols = []
        for t in tickers:
            symbol = t.get('symbol')
            if not symbol or symbol not in active_symbols:
                continue
            
            try:
                quote_vol = float(t['quoteVolume'])
            except (ValueError, KeyError):
                continue
            
            if quote_vol >= self.config["LIQUIDITY_THRESHOLD_USDT"]:
                liquid_symbols.append(symbol)
        
        self._log(f"? 找到 {len(liquid_symbols)} 个符合流动性条件的币种")
        return liquid_symbols
    
    def analyze(self):
        """执行完整分析流程"""
        try:
            # 记录分析开始时间
            start_time = datetime.now()
            start_timestamp = start_time.isoformat()
            
            # 获取活跃合约列表
            active_symbols = self.get_active_symbols()
            if not active_symbols:
                self._log("警告: 无活跃合约列表，跳过")
                return {"results": [], "start_time": start_timestamp, "end_time": start_timestamp, "duration": 0}
            
            # 获取24小时行情数据，过滤低流动性币种
            liquid_symbols = self.get_liquid_symbols()
            if not liquid_symbols:
                self._log("警告: 无符合条件的活跃合约列表")
                return {"results": [], "start_time": start_timestamp, "end_time": start_timestamp, "duration": 0}
            
            # 开始分析
            self._log("=== 开始币安合约三日涨幅分析 ===")
            self._log(f"筛选条件：涨幅 >= {self.config['MIN_CHANGE_PERCENT']}%")
            self._log(f"分析开始时间：{start_time.strftime('%Y-%m-%d %H:%M:%S')}")
                
                # 限制分析数量
            max_symbols = self.config['MAX_ANALYZE_SYMBOLS']
            if len(liquid_symbols) > max_symbols:
                self._log(f"仅分析前 {max_symbols} 个高流动性永续合约")
                liquid_symbols = liquid_symbols[:max_symbols]
            
            self._log(f"开始分析所有 {len(liquid_symbols)} 个高流动性永续合约")
            
            results = []
            total = len(liquid_symbols)
            process_start_time = time.time()
            
            for i, symbol in enumerate(liquid_symbols, 1):
                    # 计算预计剩余时间
                    if i > 1:
                        elapsed = time.time() - process_start_time
                        avg_per_symbol = elapsed / (i - 1)
                        remaining = (total - i) * avg_per_symbol
                        eta = f" (预计剩余 {remaining:.0f} 秒)"
                    else:
                        eta = ""
                    
                    # 计算进度百分比
                    progress = int((i / total) * 100)
                    self._log(f"[{i}/{total}] 正在分析 {symbol}...{eta}", progress)
                    
                    # 获取K线数据
                    klines = self.get_klines_data(symbol, 3)
                    if not klines or len(klines) < 3:
                        continue
                    
                    # 计算涨幅
                    gains = self.calculate_gains(klines)
                    if not gains:
                        continue
                    
                    # 检查条件
                    conditions = self.check_conditions(gains)
                    if not conditions:
                        continue
                    
                    # 添加到结果
                    result = {
                        "symbol": symbol,
                        "gain_1d": gains["gain_1d"],
                        "gain_2d": gains["gain_2d"],
                        "gain_3d": gains["gain_3d"],
                        "changes": gains
                    }
                    results.append(result)
                
                # 记录分析结束时间
            end_time = datetime.now()
            end_timestamp = end_time.isoformat()
            duration = (end_time - start_time).total_seconds()
            
            self._log(f"分析完成！找到 {len(results)} 个符合条件的交易对", 100)
            self._log(f"分析结束时间：{end_time.strftime('%Y-%m-%d %H:%M:%S')}")
            self._log(f"分析耗时：{duration:.1f} 秒")
            
            return {
                "results": results,
                "start_time": start_timestamp,
                "end_time": end_timestamp,
                "duration": duration
            }
            
        except Exception as e:
            end_time = datetime.now()
            end_timestamp = end_time.isoformat()
            duration = (end_time - start_time).total_seconds() if 'start_time' in locals() else 0
            
            self._log(f"分析出错: {str(e)}")
            return {
                "results": [],
                "start_time": start_timestamp if 'start_timestamp' in locals() else end_timestamp,
                "end_time": end_timestamp,
                "duration": duration,
                "error": str(e)
            }
