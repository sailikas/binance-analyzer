import requests
import json
import time
import os
from datetime import datetime


# ====== 配置 ======
CACHE_FILE = "exchange_info_cache.json"
CACHE_EXPIRY = 3600  # 1小时，单位：秒
#做空的话如果想赚50个点，他必须得涨100个点，比如没涨前原价1块，涨价后是两块100个点，跌的空间才有50个点，因为跌50%是1块等于跌回涨之前
MIN_CHANGE_PERCENT = 100.0  # 最小涨幅 
LIQUIDITY_THRESHOLD_USDT = 1_000_000  # 流动性阈值：100万USDT
REQUEST_DELAY = 0.15  # API请求间隔，避免限频
MAX_ANALYZE_SYMBOLS = 500  # 最大分析数量，避免运行时间过长


def get_active_symbols():
    """从文件或 API 获取活跃永续合约列表"""
    now = int(time.time())

    # 检查缓存文件是否存在且未过期
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                cache = json.load(f)
            if now - cache.get("timestamp", 0) < CACHE_EXPIRY:
                print("从缓存加载exchangeInfo")
                return set(cache["symbols"])
        except Exception as e:
            print(f"⚠️ 缓存文件读取失败: {e}. 重新拉取...")

    # 缓存不存在或已过期，重新拉取
    print("重新拉取exchangeInfo...")
    try:
        resp = requests.get("https://fapi.binance.com/fapi/v1/exchangeInfo", timeout=10)
        resp.raise_for_status()
        data = resp.json()

        active_symbols = []
        for sym in data['symbols']:
            if sym['status'] == 'TRADING' and sym['contractType'] == 'PERPETUAL':
                active_symbols.append(sym['symbol'])

        # 写入缓存文件
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump({
                "timestamp": now,
                "symbols": active_symbols
            }, f, ensure_ascii=False)

        print(f"✅ 成功缓存 {len(active_symbols)} 个活跃永续合约")
        return set(active_symbols)

    except Exception as e:
        print(f"拉取exchangeInfo失败: {e}")
        # 如果有旧缓存文件，即使过期也尝试使用（容错）
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                    cache = json.load(f)
                return set(cache.get("symbols", []))
            except:
                pass
        return set()


def get_klines_data(symbol, limit=3):
    """获取指定交易对的K线数据"""
    max_retries = 2
    for attempt in range(max_retries):
        try:
            url = "https://fapi.binance.com/fapi/v1/klines"
            params = {
                "symbol": symbol,
                "interval": "1d",  # 日K线
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
                time.sleep(0.5)  # 短暂等待后重试
                continue
            else:
                # 只在最后一次重试失败时打印错误，避免刷屏
                print(f"\n⚠️ 获取 {symbol} K线数据失败: {e}")
                return []
        except Exception as e:
            print(f"\n⚠️ 获取 {symbol} K线数据失败: {e}")
            return []


def calculate_gains(klines):
    """计算各种涨幅"""
    if len(klines) < 3:
        return None
    
    # 根据需求文档：
    # K线[0]：最近一个已结束的交易日（"今日"）
    # K线[-1]：前一交易日（"昨日"）
    # K线[-2]：前两个交易日（"前日"）
    
    # 币安API返回的K线按时间顺序排列，最新的K线在数组末尾
    # 但需求文档使用的是不同的索引约定
    # 我们需要确保正确理解时间顺序
    
    # 根据需求文档的反向索引约定：
    # 需求文档：K线[0]=今日, K线[-1]=昨日, K线[-2]=前日
    # API返回：[3天前, 2天前, 昨天] 
    # 映射关系：
    # 需求文档的K线[0] 对应 API的 klines[-1]（最新数据）
    # 需求文档的K线[-1] 对应 API的 klines[-2]（前一日数据）
    # 需求文档的K线[-2] 对应 API的 klines[-3]（前两日数据）
    
    k_today = klines[-1]      # 需求文档的K线[0] - 今日（最新数据）
    k_yesterday = klines[-2]  # 需求文档的K线[-1] - 昨日（前一日数据）
    k_day_before = klines[-3] # 需求文档的K线[-2] - 前日（前两日数据）
    
    # 条件A：最近单日暴涨 (K线[0].收盘价 / K线[0].开盘价) - 1 >= 50%
    gain_1d = (k_today["close"] / k_today["open"]) - 1
    
    # 条件B：最近两日累计暴涨 (K线[0].收盘价 / K线[-1].开盘价) - 1 >= 50%
    gain_2d = (k_today["close"] / k_yesterday["open"]) - 1
    
    # 条件C：最近三日累计暴涨 (K线[0].收盘价 / K线[-2].开盘价) - 1 >= 50%
    gain_3d = (k_today["close"] / k_day_before["open"]) - 1
    
    return {
        "gain_1d": gain_1d,
        "gain_2d": gain_2d,
        "gain_3d": gain_3d
    }


def check_conditions(gains):
    """检查满足的条件"""
    if not gains:
        return []
    
    conditions = []
    
    # 条件A：最近单日暴涨 >= 50%
    if gains["gain_1d"] >= MIN_CHANGE_PERCENT / 100:
        conditions.append("A")
    
    # 条件B：最近两日累计暴涨 >= 50%
    if gains["gain_2d"] >= MIN_CHANGE_PERCENT / 100:
        conditions.append("B")
    
    # 条件C：最近三日累计暴涨 >= 50%
    if gains["gain_3d"] >= MIN_CHANGE_PERCENT / 100:
        conditions.append("C")
    
    return conditions


def get_liquid_symbols():
    """获取符合流动性条件的活跃永续合约"""
    # 获取活跃合约
    active_symbols = get_active_symbols()
    if not active_symbols:
        print("⚠️ 无活跃合约列表，跳过")
        return []
    
    print(f"获取24小时行情数据，过滤低流动性币种...")
    
    # 获取24h行情，添加重试机制
    max_retries = 3
    tickers = None
    for attempt in range(max_retries):
        try:
            print(f"尝试获取24小时行情数据 (第 {attempt + 1}/{max_retries} 次)...")
            resp = requests.get("https://fapi.binance.com/fapi/v1/ticker/24hr", timeout=15)
            resp.raise_for_status()
            tickers = resp.json()
            break
        except requests.exceptions.RequestException as e:
            print(f"❌ 获取 ticker 失败 (第 {attempt + 1} 次): {e}")
            if attempt < max_retries - 1:
                print(f"等待 5 秒后重试...")
                time.sleep(5)
            else:
                print("❌ 所有重试均失败，跳过流动性过滤")
                return list(active_symbols)[:MAX_ANALYZE_SYMBOLS]  # 返回前N个活跃合约作为备选
        except KeyboardInterrupt:
            print("\n⚠️ 用户中断操作")
            return []
    
    if not tickers:
        print("❌ 未能获取到行情数据")
        return []

    liquid_symbols = []
    for t in tickers:
        symbol = t.get('symbol')
        if not symbol or symbol not in active_symbols:
            continue

        try:
            quote_vol = float(t['quoteVolume'])  # 24小时成交额
        except (ValueError, KeyError):
            continue

        if quote_vol >= LIQUIDITY_THRESHOLD_USDT:
            liquid_symbols.append(symbol)

    print(f"✅ 找到 {len(liquid_symbols)} 个符合流动性条件的币种（24小时成交额 >= {LIQUIDITY_THRESHOLD_USDT:,} USDT）")
    return liquid_symbols


def analyze_symbols():
    """分析所有交易对的三日涨幅"""
    # 获取符合流动性条件的合约
    liquid_symbols = get_liquid_symbols()
    if not liquid_symbols:
        print("⚠️ 无符合条件的活跃合约列表，跳过")
        return []
    
    # 限制分析数量
    if len(liquid_symbols) > MAX_ANALYZE_SYMBOLS:
        liquid_symbols = liquid_symbols[:MAX_ANALYZE_SYMBOLS]
        print(f"为避免运行时间过长，仅分析前 {MAX_ANALYZE_SYMBOLS} 个高流动性永续合约...")
    else:
        print(f"开始分析所有 {len(liquid_symbols)} 个高流动性永续合约...")
    
    # 显示将要分析的币种列表
    print(f"将要分析的币种列表（前20个）:")
    for i, symbol in enumerate(liquid_symbols[:20], 1):
        print(f"{i:2d}. {symbol}")
    if len(liquid_symbols) > 20:
        print(f"... 以及其他 {len(liquid_symbols) - 20} 个币种")
    print()
    
    results = []
    total = len(liquid_symbols)
    start_time = time.time()
    
    for i, symbol in enumerate(liquid_symbols, 1):
        # 计算预估剩余时间
        if i > 1:
            elapsed = time.time() - start_time
            avg_per_symbol = elapsed / (i - 1)
            remaining = (total - i) * avg_per_symbol
            eta = f" (预计剩余 {remaining:.0f} 秒)"
        else:
            eta = ""
        
        print(f"[{i}/{total}] 正在分析 {symbol}...{eta}", end="\r")
        
        # 获取K线数据
        klines = get_klines_data(symbol, 3)
        if not klines or len(klines) < 3:
            continue
        
        # 计算涨幅
        gains = calculate_gains(klines)
        if not gains:
            continue
        
        # 检查条件
        conditions = check_conditions(gains)
        if not conditions:
            continue
        
        # 添加到结果
        result = {
            "symbol": symbol,
            "gain_1d": gains["gain_1d"],
            "gain_2d": gains["gain_2d"],
            "gain_3d": gains["gain_3d"],
            "conditions": conditions,
            "conditions_count": len(conditions)
        }
        results.append(result)
        
        # API限频
        time.sleep(REQUEST_DELAY)
    
    print()  # 换行
    
    # 排序结果
    # 第一优先级：按满足条件数量降序
    # 第二优先级：按三日累计涨幅降序
    results.sort(key=lambda x: (x["conditions_count"], x["gain_3d"]), reverse=True)
    
    return results


def format_results(results):
    """格式化输出结果"""
    if not results:
        print("未找到符合条件的交易对")
        return
    
    print(f"\n找到 {len(results)} 个符合条件的交易对:")
    print("-" * 100)
    print(f"{'交易对':<12} | {'单日涨幅':<10} | {'两日涨幅':<10} | {'三日涨幅':<10} | {'触发条件':<10} | {'排名'}")
    print("-" * 100)
    
    for i, result in enumerate(results, 1):
        symbol = result["symbol"]
        gain_1d = result["gain_1d"] * 100
        gain_2d = result["gain_2d"] * 100
        gain_3d = result["gain_3d"] * 100
        conditions = ", ".join(result["conditions"])
        
        print(f"{symbol:<12} | {gain_1d:>+7.1f}%   | {gain_2d:>+7.1f}%   | {gain_3d:>+7.1f}%   | {conditions:<10} | {i}")


def main():
    """主函数"""
    print("=== 币安合约三日涨幅筛选分析工具 ===")
    print(f"筛选条件：涨幅 >= {MIN_CHANGE_PERCENT}%")
    print(f"分析时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 分析交易对
    results = analyze_symbols()
    
    # 输出结果
    format_results(results)
    
    # 保存结果到文件
    if results:
        output_file = f"three_day_gainers_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\n结果已保存到: {output_file}")


if __name__ == "__main__":
    main()