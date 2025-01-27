import ccxt
import pandas as pd
import numpy as np
from datetime import datetime
import time
import logging
import json
import os
from market_analyzer import EnhancedMarketAnalyzer
import asyncio
import requests
import hmac
import hashlib
from urllib.parse import urlencode


class PionexTradingBot:
    def __init__(self, api_key, api_secret):
        try:
            self.api_key = api_key
            self.api_secret = api_secret
            self.base_url = "https://api.pionex.com"

            # 初始化請求頭
            self.headers = {
                'PIONEX-KEY': self.api_key,
                'Content-Type': 'application/json'
            }

            # 測試連接
            self.test_connection()

            # 初始化其他設置
            self.setup_logging()
            self.load_config()
            self.market_analyzer = EnhancedMarketAnalyzer()

            # 記錄成功初始化
            logging.info("交易系統初始化成功")

        except Exception as e:
            logging.error(f"初始化失敗: {str(e)}")
            raise Exception(f"交易所連接失敗: {str(e)}")

    def generate_signature(self, params, method, endpoint):
        """生成 API 簽名
        根據 Pionex API 文檔要求生成簽名：
        1. 將所有參數按字母順序排序
        2. 將參數轉換為 key=value 格式並用 & 連接
        3. 添加請求方法和路徑
        4. 使用 HMAC-SHA256 生成簽名
        """
        try:
            # 生成時間戳
            timestamp = str(int(time.time() * 1000))

            # 準備參數字典
            sign_params = params.copy() if params else {}
            sign_params['timestamp'] = timestamp

            # 按字母順序排序並生成參數字符串
            sorted_params = sorted(sign_params.items(), key=lambda x: x[0])
            param_str = '&'.join(
                [f"{key}={value}" for key, value in sorted_params])

            # 構建完整的簽名字符串：METHOD + PATH + QUERY
            sign_str = f"{method.upper()}{endpoint}"
            if param_str:
                sign_str = f"{sign_str}?{param_str}"

            # 使用 HMAC-SHA256 生成簽名
            signature = hmac.new(
                self.api_secret.encode('utf-8'),
                sign_str.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()

            logging.debug(f"Signature string: {sign_str}")
            logging.debug(f"Generated signature: {signature}")

            return signature, timestamp

        except Exception as e:
            logging.error(f"生成簽名失敗: {str(e)}")
            raise

    def make_request(self, method, endpoint, params=None):
        """發送API請求"""
        try:
            url = f"{self.base_url}{endpoint}"

            # 如果沒有提供參數，初始化空字典
            if params is None:
                params = {}

            # 生成簽名
            signature, timestamp = self.generate_signature(
                params, method, endpoint)

            # 添加時間戳到參數中
            params['timestamp'] = timestamp

            # 更新請求頭
            headers = self.headers.copy()
            headers['PIONEX-SIGNATURE'] = signature
            headers['PIONEX-TIMESTAMP'] = timestamp

            # 發送請求
            response = requests.request(
                method,
                url,
                params=params,
                headers=headers,
                timeout=10
            )

            # 打印請求信息用於調試
            logging.debug(f"Request URL: {response.url}")
            logging.debug(f"Request Headers: {headers}")
            logging.debug(f"Response: {response.text}")

            # 檢查響應狀態
            response.raise_for_status()

            # 解析響應
            data = response.json()

            # 檢查API響應結果
            if not data.get('result', False):
                error_msg = data.get('message', '未知錯誤')
                raise ValueError(f"API響應錯誤: {error_msg}")

            return data

        except requests.exceptions.RequestException as e:
            logging.error(f"API 請求失敗: {str(e)}")
            raise
        except ValueError as e:
            logging.error(str(e))
            raise
        except Exception as e:
            logging.error(f"未預期的錯誤: {str(e)}")
            raise

    def test_connection(self):
        """測試 API 連接"""
        try:
            # 使用正確的帳戶餘額接口
            response = self.make_request('GET', '/api/v1/account/balances')

            # 修改檢查邏輯：使用 result 字段
            if response.get('result', False):
                logging.info("API 連接成功")
                logging.info(f"帳戶餘額: {response.get(
                    'data', {}).get('balances', [])}")
                return True
            else:
                raise Exception(response.get('message', '未知錯誤'))

        except Exception as e:
            logging.error(f"API 連接測試失敗: {str(e)}")
            raise Exception(f"API 驗證失敗: {str(e)}")

    def get_market_data(self, symbol, timeframe='1M', limit=100):
        """獲取市場數據"""
        try:
            # 確保交易對格式正確 (例如：BTC_USDT)
            formatted_symbol = symbol.replace('-', '_').upper()
            if '/' in formatted_symbol:
                formatted_symbol = formatted_symbol.replace('/', '_')

            # 轉換時間間隔格式
            interval_mapping = {
                '1m': '1M',
                '5m': '5M',
                '15m': '15M',
                '30m': '30M',
                '1h': '60M',
                '4h': '4H',
                '8h': '8H',
                '12h': '12H',
                '1d': '1D'
            }

            # 獲取正確的時間間隔格式
            formatted_interval = interval_mapping.get(timeframe, timeframe)

            # 構建請求參數
            params = {
                "symbol": formatted_symbol,
                "interval": formatted_interval,
                "limit": str(limit),
                "timestamp": str(int(time.time() * 1000))
            }

            logging.info(f"正在獲取市場數據: {formatted_symbol}, 時間間隔: {
                         formatted_interval}")
            response = self.make_request(
                'GET', '/api/v1/market/klines', params)

            if response.get('result', False):
                data = response.get('data', [])
                if not data:
                    logging.warning(f"未獲取到 {formatted_symbol} 的市場數據")
                    return None

                df = pd.DataFrame(data, columns=[
                    'timestamp', 'open', 'high', 'low',
                    'close', 'volume', 'close_time', 'quote_volume',
                    'trades', 'taker_base', 'taker_quote'
                ])
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                return df
            else:
                raise Exception(response.get('message', '獲取市場數據失敗'))

        except Exception as e:
            logging.error(f"獲取市場數據失敗: {str(e)}")
            return None

    def setup_logging(self):
        logging.basicConfig(
            filename=f'trading_log_{datetime.now().strftime("%Y%m%d")}.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def load_config(self):
        with open('config.json', 'r') as f:
            self.config = json.load(f)

    def calculate_indicators(self, df):
        # RSI 計算
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))

        # MACD 計算
        exp1 = df['close'].ewm(span=12, adjust=False).mean()
        exp2 = df['close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = exp1 - exp2
        df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()

        # 添加布林帶
        df['SMA20'] = df['close'].rolling(window=20).mean()
        df['stddev'] = df['close'].rolling(window=20).std()
        df['BB_upper'] = df['SMA20'] + (df['stddev'] * 2)
        df['BB_lower'] = df['SMA20'] - (df['stddev'] * 2)

        # 添加 KDJ
        low_min = df['low'].rolling(window=9).min()
        high_max = df['high'].rolling(window=9).max()
        df['RSV'] = (df['close'] - low_min) / (high_max - low_min) * 100
        df['K'] = df['RSV'].ewm(com=2).mean()
        df['D'] = df['K'].ewm(com=2).mean()
        df['J'] = 3 * df['K'] - 2 * df['D']

        # 添加趨勢強度指標
        df['EMA50'] = df['close'].ewm(span=50).mean()
        df['EMA200'] = df['close'].ewm(span=200).mean()

        # 添加 ATR (Average True Range) 波動指標
        df['TR'] = np.maximum(
            df['high'] - df['low'],
            np.maximum(
                abs(df['high'] - df['close'].shift(1)),
                abs(df['low'] - df['close'].shift(1))
            )
        )
        df['ATR'] = df['TR'].rolling(window=14).mean()

        # 添加 OBV (On Balance Volume) 成交量指標
        df['OBV'] = (np.sign(df['close'].diff()) *
                     df['volume']).fillna(0).cumsum()

        # 添加 Stochastic RSI
        df['StochRSI'] = (df['RSI'] - df['RSI'].rolling(window=14).min()) / \
            (df['RSI'].rolling(window=14).max() -
             df['RSI'].rolling(window=14).min())

        # 添加價格趨勢強度
        df['Price_ROC'] = df['close'].pct_change(periods=14) * 100

        return df

    def check_signals(self, df):
        signals = {
            'rsi_oversold': df['RSI'].iloc[-1] < 30,
            'rsi_overbought': df['RSI'].iloc[-1] > 70,
            'macd_crossover': (df['MACD'].iloc[-2] < df['Signal'].iloc[-2]) and
            (df['MACD'].iloc[-1] > df['Signal'].iloc[-1]),
            'macd_crossunder': (df['MACD'].iloc[-2] > df['Signal'].iloc[-2]) and
            (df['MACD'].iloc[-1] < df['Signal'].iloc[-1]),
            'bb_lower_break': df['close'].iloc[-1] < df['BB_lower'].iloc[-1],
            'bb_upper_break': df['close'].iloc[-1] > df['BB_upper'].iloc[-1],
            'kdj_oversold': df['J'].iloc[-1] < 20,
            'kdj_overbought': df['J'].iloc[-1] > 80,
            'trend_strong_up': (df['EMA50'].iloc[-1] > df['EMA200'].iloc[-1]) and
            (df['close'].iloc[-1] > df['EMA50'].iloc[-1]),
            'trend_strong_down': (df['EMA50'].iloc[-1] < df['EMA200'].iloc[-1]) and
            (df['close'].iloc[-1] < df['EMA50'].iloc[-1]),
            'should_trade': True
        }
        return signals

    def initialize_trading(self):
        """初始化交易設置"""
        print("\n=== Pionex 智能交易系統 ===")

        # 獲取投資金額
        while True:
            try:
                investment_twd = float(input("\n請輸入您要投資的台幣金額: "))
                if investment_twd <= 0:
                    print("請輸入大於0的金額")
                    continue
                break
            except ValueError:
                print("請輸入有效的數字")

        # 轉換為USDT (假設匯率 1 USD = 31 TWD)
        investment_usdt = round(investment_twd / 31, 2)

        # 資金分配建議
        print(f"\n您的投資金額相當於 {investment_usdt} USDT")
        print("\n建議資金分配:")
        print(f"BTC/USDT: {round(investment_usdt * 0.6, 2)} USDT (60%)")
        print(f"ETH/USDT: {round(investment_usdt * 0.4, 2)} USDT (40%)")

        # 確認分配
        while True:
            confirm = input("\n是否接受此分配方案？(y/n): ").lower()
            if confirm == 'y':
                self.update_investment_amounts(investment_usdt)
                break
            elif confirm == 'n':
                print("\n請手動設置分配比例")
                btc_percentage = float(input("BTC 分配比例 (0-100): ")) / 100
                self.update_investment_amounts(investment_usdt, btc_percentage)
                break

    def update_investment_amounts(self, total_usdt, btc_percentage=0.6):
        """更新配置文件中的投資金額"""
        self.config['grid_settings']['BTC/USDT']['investment_amount'] = round(
            total_usdt * btc_percentage, 2)
        self.config['grid_settings']['ETH/USDT']['investment_amount'] = round(
            total_usdt * (1 - btc_percentage), 2)
        self.save_config()

    def save_config(self):
        """保存配置到文件"""
        with open('config.json', 'w') as f:
            json.dump(self.config, f, indent=4)

    def analyze_market_condition(self, df):
        signals = self.check_signals(df)
        market_state = {
            'trend': self.analyze_trend(df),
            'volatility': self.analyze_volatility(df),
            'volume': self.analyze_volume(df),
            'momentum': self.analyze_momentum(df)
        }

        # 綜合評分系統
        score = self.calculate_market_score(market_state, signals)

        return {
            'score': score,
            'state': market_state,
            'recommendation': self.get_trading_recommendation(score)
        }

    def analyze_trend(self, df):
        """分析趨勢強度"""
        trend_score = 0

        # EMA趨勢
        if df['EMA50'].iloc[-1] > df['EMA200'].iloc[-1]:
            trend_score += 2

        # 價格位置
        if df['close'].iloc[-1] > df['EMA50'].iloc[-1]:
            trend_score += 1

        # 趨勢持續性
        price_trend = df['close'].diff().rolling(window=20).mean()
        if price_trend.iloc[-1] > 0:
            trend_score += 1

        return trend_score

    def execute_trading_strategy(self):
        """執行交易策略"""
        try:
            # 使用當前熱門交易對
            for pair in self.trading_pairs:
                # 獲取市場數據
                market_data = self.get_market_data(pair)
                if market_data is None:
                    continue

                # 計算技術指標
                analysis = self.calculate_indicators(market_data)

                # 獲取市場情緒
                sentiment = self.market_analyzer.analyze_market_sentiment(pair)

                # 獲取交易信號
                signals = self.check_signals(analysis)

                # 根據信號執行交易
                if signals.get('should_trade', False):
                    # 計算倉位大小
                    position_size = self.optimize_position_management(
                        pair, sentiment)

                    # 獲取動態止盈止損點
                    targets = self.risk_manager.calculate_dynamic_targets(
                        pair, sentiment)

                    # 執行交易
                    if signals.get('direction') == 'buy':
                        self.place_order(
                            pair, 'buy', position_size,
                            take_profit=targets['take_profit'],
                            stop_loss=targets['stop_loss']
                        )
                    else:
                        self.place_order(
                            pair, 'sell', position_size,
                            take_profit=targets['take_profit'],
                            stop_loss=targets['stop_loss']
                        )

        except Exception as e:
            logging.error(f"執行交易策略失敗: {str(e)}")

    def execute_long_strategy(self, symbol, grid_levels, investment_amount, signal_strength):
        """執行做多策略"""
        try:
            current_price = self.exchange.fetch_ticker(symbol)['last']

            # 根據信號強度調整網格參數
            grid_count = int(grid_levels['grid_count']
                             * (1 + signal_strength * 0.1))
            price_range = grid_levels['price_range_percentage'] * \
                (1 + signal_strength * 0.05)

            lower_price = current_price * (1 - price_range / 100)
            upper_price = current_price * (1 + price_range / 100)
            grid_interval = (upper_price - lower_price) / grid_count

            # 設置網格訂單
            for i in range(grid_count):
                grid_price = lower_price + (i * grid_interval)
                order_amount = self.calculate_position_size(
                    investment_amount, grid_count, signal_strength)

                if grid_price < current_price:
                    self.place_buy_order(
                        symbol, order_amount * 1.2, grid_price)
                else:
                    self.place_sell_order(symbol, order_amount, grid_price)

        except Exception as e:
            logging.error(f"Long strategy error: {str(e)}")

    def execute_short_strategy(self, symbol, grid_levels, investment_amount, signal_strength):
        """執行做空策略"""
        try:
            current_price = self.exchange.fetch_ticker(symbol)['last']

            # 根據信號強度調整網格參數
            grid_count = int(grid_levels['grid_count']
                             * (1 + signal_strength * 0.1))
            price_range = grid_levels['price_range_percentage'] * \
                (1 + signal_strength * 0.05)

            lower_price = current_price * (1 - price_range / 100)
            upper_price = current_price * (1 + price_range / 100)
            grid_interval = (upper_price - lower_price) / grid_count

            # 設置網格訂單
            for i in range(grid_count):
                grid_price = lower_price + (i * grid_interval)
                order_amount = self.calculate_position_size(
                    investment_amount, grid_count, signal_strength)

                if grid_price > current_price:
                    self.place_sell_order(
                        symbol, order_amount * 1.2, grid_price)
                else:
                    self.place_buy_order(symbol, order_amount, grid_price)

        except Exception as e:
            logging.error(f"Short strategy error: {str(e)}")

    def calculate_position_size(self, investment_amount, grid_count, signals):
        base_amount = investment_amount / grid_count

        # 根據信號強度調整倉位
        signal_strength = 0
        if signals['trend_strong_up']:
            signal_strength += 0.2
        if signals['trend_strong_down']:
            signal_strength -= 0.2
        if signals['rsi_oversold'] and signals['kdj_oversold']:
            signal_strength += 0.15
        if signals['rsi_overbought'] and signals['kdj_overbought']:
            signal_strength -= 0.15

        adjusted_amount = base_amount * (1 + signal_strength)
        return max(adjusted_amount, base_amount * 0.5)  # 確保最小倉位

    def update_profit_stats(self, trade):
        self.profit_tracker['total_trades'] += 1
        if trade['profit'] > 0:
            self.profit_tracker['win_trades'] += 1
        self.profit_tracker['daily_profit'] += trade['profit']
        self.profit_tracker['total_profit'] += trade['profit']

    def run(self):
        """運行交易機器人"""
        # 定期更新交易對列表
        self.update_trading_pairs()

        # 設置定時更新
        self.schedule_update()

    def print_trading_stats(self):
        """打印交易統計信息"""
        print("\n=== 交易統計 ===")
        print(f"總交易次數: {self.profit_tracker['total_trades']}")
        win_rate = (self.profit_tracker['win_trades'] / self.profit_tracker['total_trades']
                    * 100) if self.profit_tracker['total_trades'] > 0 else 0
        print(f"總勝率: {win_rate:.2f}%")
        print(f"當日盈利: {self.profit_tracker['daily_profit']:.2f} USDT")
        print(f"總盈利: {self.profit_tracker['total_profit']:.2f} USDT")
        print("==================")

    def manage_position(self, symbol, current_price, signal_strength):
        """管理倉位加減"""
        position = self.position_manager[symbol]
        max_position = position['max_position_size']
        current_position = position['current_position']

        # 計算目標倉位
        target_position = self.calculate_target_position(
            symbol,
            current_price,
            signal_strength
        )

        if target_position > current_position:
            # 需要加倉
            if current_position < max_position:
                add_amount = min(
                    target_position - current_position,
                    max_position - current_position
                )
                self.add_position(symbol, add_amount, current_price)
        else:
            # 需要減倉
            if target_position < current_position:
                reduce_amount = current_position - target_position
                self.reduce_position(symbol, reduce_amount, current_price)

    def calculate_target_position(self, symbol, current_price, signal_strength):
        """計算目標倉位大小"""
        position = self.position_manager[symbol]
        base_position = position['max_position_size'] * 0.5  # 基礎倉位為最大倉位的50%

        # 根據信號強度調整目標倉位
        if signal_strength > 8:  # 強烈信號
            return base_position * 1.5  # 最大加倉150%
        elif signal_strength > 5:  # 中等信號
            return base_position * 1.2  # 加倉120%
        elif signal_strength < -8:  # 強烈反轉信號
            return base_position * 0.3  # 減倉到30%
        elif signal_strength < -5:  # 中等反轉信號
            return base_position * 0.5  # 減倉到50%
        else:
            return base_position  # 保持基礎倉位

    def add_position(self, symbol, amount, current_price):
        """加倉操作"""
        try:
            # 檢查加倉條件
            if self.check_add_position_conditions(symbol, current_price):
                # 計算加倉金額
                investment = amount * current_price

                # 執行買入訂單
                order = self.place_buy_order(symbol, amount, current_price)

                if order['status'] == 'filled':
                    # 更新倉位信息
                    position = self.position_manager[symbol]
                    position['current_position'] += amount
                    position['total_investment'] += investment
                    position['average_price'] = (
                        position['total_investment'] /
                        position['current_position']
                    )

                    # 記錄加倉操作
                    logging.info(
                        f"加倉成功 - {symbol}: 數量={amount}, 價格={current_price}")

        except Exception as e:
            logging.error(f"加倉失敗: {str(e)}")

    def reduce_position(self, symbol, amount, current_price):
        """減倉操作"""
        try:
            # 檢查減倉條件
            if self.check_reduce_position_conditions(symbol, current_price):
                # 執行賣出訂單
                order = self.place_sell_order(symbol, amount, current_price)

                if order['status'] == 'filled':
                    # 更新倉位信息
                    position = self.position_manager[symbol]
                    position['current_position'] -= amount
                    position['total_investment'] -= (amount *
                                                     position['average_price'])

                    if position['current_position'] > 0:
                        position['average_price'] = (
                            position['total_investment'] /
                            position['current_position']
                        )
                    else:
                        position['average_price'] = 0

                    # 記錄減倉操作
                    logging.info(
                        f"減倉成功 - {symbol}: 數量={amount}, 價格={current_price}")

        except Exception as e:
            logging.error(f"減倉失敗: {str(e)}")

    def check_add_position_conditions(self, symbol, current_price):
        """檢查加倉條件"""
        position = self.position_manager[symbol]

        # 檢查是否達到最大倉位
        if position['current_position'] >= position['max_position_size']:
            return False

        # 檢查當前價格是否適合加倉
        if position['average_price'] > 0:
            price_change = (
                current_price - position['average_price']) / position['average_price']

            # 如果虧損超過2%，不加倉
            if price_change < -0.02:
                return False

            # 如果盈利超過3%，可以加倉
            if price_change > 0.03:
                return True

        return True

    def check_reduce_position_conditions(self, symbol, current_price):
        """檢查減倉條件"""
        position = self.position_manager[symbol]

        if position['current_position'] <= 0:
            return False

        # 計算當前盈虧
        price_change = (
            current_price - position['average_price']) / position['average_price']

        # 虧損達到止損線，強制減倉
        if price_change < -0.02:  # -2%止損
            return True

        # 盈利回撤超過30%，保護利潤
        if price_change > 0.05 and self.calculate_drawdown(symbol) > 0.3:
            return True

        return False

    def calculate_drawdown(self, symbol):
        """計算回撤幅度"""
        df = self.get_market_data(symbol)
        if df is None:
            return 0

        recent_high = df['high'].rolling(window=20).max().iloc[-1]
        current_price = df['close'].iloc[-1]

        return (recent_high - current_price) / recent_high

    def optimize_position_management(self, symbol, sentiment):
        """智能倉位管理"""
        try:
            # 基礎倉位大小
            base_position = self.calculate_base_position(symbol)

            # 根據市場情緒調整倉位
            sentiment_factor = self.calculate_sentiment_factor(sentiment)

            # 根據波動率調整倉位
            volatility_factor = self.calculate_volatility_factor(symbol)

            # 根據趨勢強度調整倉位
            trend_factor = self.calculate_trend_factor(symbol)

            # 綜合計算最終倉位
            final_position = base_position * sentiment_factor * \
                volatility_factor * trend_factor

            # 應用風險限制
            max_position = self.get_max_position_size(symbol)
            return min(final_position, max_position)

        except Exception as e:
            logging.error(f"倉位優化失敗: {str(e)}")
            return base_position

    def calculate_sentiment_factor(self, sentiment):
        """計算情緒因子"""
        try:
            # 恐懼貪婪指數影響
            fear_greed_impact = 1 + (sentiment['fear_greed_index'] - 50) / 100

            # 趨勢強度影響
            trend_impact = 1 + sentiment['trend_strength'] * 0.5

            # 成交量趨勢影響
            volume_impact = 1 + sentiment['volume_trend'] * 0.3

            # 綜合計算
            factor = (fear_greed_impact + trend_impact + volume_impact) / 3

            # 限制調整範圍
            return max(0.5, min(1.5, factor))

        except Exception as e:
            logging.error(f"情緒因子計算失敗: {str(e)}")
            return 1.0

    def update_trading_pairs(self):
        """更新交易對列表"""
        try:
            # 獲取前五大交易量幣種
            pairs_data = self.market_analyzer.get_top_volume_pairs(self)

            if not pairs_data:
                logging.warning("未獲取到任何交易對數據")
                return

            # 更新UI顯示
            if hasattr(self, 'ui'):
                self.ui.update_popular_pairs(pairs_data)
                logging.info("已更新UI顯示")

            # 更新交易對列表
            self.trading_pairs = [pair['symbol'] for pair in pairs_data]
            logging.info(f"成功更新交易對列表: {self.trading_pairs}")

        except Exception as e:
            logging.error(f"更新交易對失敗: {str(e)}")
            raise

    def schedule_update(self):
        # 實現定時更新邏輯
        pass

    def optimize_investment_allocation(self, total_investment):
        """優化資金配置"""
        try:
            # 獲取前五大交易量幣種
            top_pairs = self.market_analyzer.get_top_volume_pairs(
                self.exchange)

            # 分析每個交易對的歷史表現
            performance_data = {}
            for pair, volume in top_pairs:
                # 獲取歷史數據
                historical_data = self.get_market_data(
                    pair, timeframe='1d', limit=30)

                if historical_data is not None:
                    # 計算關鍵指標
                    volatility = historical_data['close'].pct_change().std()
                    trend_strength = self.calculate_trend_strength(
                        historical_data)
                    win_rate = self.analyze_historical_win_rate(pair)

                    # 綜合評分
                    score = self.calculate_investment_score(
                        volatility,
                        trend_strength,
                        win_rate,
                        volume
                    )

                    performance_data[pair] = {
                        'score': score,
                        'volume': volume,
                        'volatility': volatility,
                        'win_rate': win_rate
                    }

            # 根據評分分配資金
            total_score = sum(data['score']
                              for data in performance_data.values())
            allocations = {}

            for pair, data in performance_data.items():
                allocation_ratio = data['score'] / total_score
                allocations[pair] = {
                    'amount': total_investment * allocation_ratio,
                    'ratio': allocation_ratio * 100
                }

            return allocations

        except Exception as e:
            logging.error(f"資金配置優化失敗: {str(e)}")
            return None

    def calculate_investment_score(self, volatility, trend_strength, win_rate, volume):
        """計算投資評分"""
        # 波動率分數 (較低波動率得分較高)
        volatility_score = 1 / (1 + volatility)

        # 趨勢強度分數
        trend_score = trend_strength

        # 勝率分數
        win_rate_score = win_rate

        # 交易量分數 (取對數以平衡大小差異)
        volume_score = np.log(volume) / 10

        # 綜合評分 (可調整權重)
        score = (
            volatility_score * 0.3 +
            trend_score * 0.2 +
            win_rate_score * 0.3 +
            volume_score * 0.2
        )

        return score

    def start_market_data_update(self):
        """開始更新市場數據"""
        try:
            def update_market_data():
                try:
                    # 使用正確的交易對格式和時間間隔
                    data = self.get_market_data(
                        'BTC_USDT', '1M')  # 使用 1M 的時間間隔
                    if data is not None:
                        self.market_data = data
                        logging.info("市場數據更新成功")
                except Exception as e:
                    logging.error(f"市場數據更新失敗: {str(e)}")

            # 設置下一次更新
            if hasattr(self, 'window'):
                self.window.after(60000, update_market_data)

            # 開始第一次更新
            update_market_data()

        except Exception as e:
            logging.error(f"啟動市場數據更新失敗: {str(e)}")
            raise

    def get_account_status(self):
        """獲取帳戶狀態"""
        try:
            # 只使用餘額接口
            balance_response = self.make_request(
                'GET', '/api/v1/account/balances')

            if not balance_response.get('result', False):
                raise Exception('獲取帳戶信息失敗')

            balances = balance_response.get('data', {}).get('balances', [])

            # 計算總資產和可用餘額
            total_balance = sum(float(b['free']) + float(b['frozen'])
                                for b in balances if b['coin'] == 'USDT')
            available_balance = sum(float(b['free'])
                                    for b in balances if b['coin'] == 'USDT')

            return {
                'total_balance': total_balance,
                'available_balance': available_balance,
                'capital_usage': 0,  # 添加資金使用率
                'total_pnl': 0,      # 添加總收益
                'daily_pnl': 0,      # 添加日收益
                'win_rate': 0,       # 添加勝率
                'position_details': {},  # 添加空持倉詳情
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

        except Exception as e:
            logging.error(f"獲取帳戶狀態失敗: {str(e)}")
            return None

    def validate_investment_amount(self, investment_amount):
        """驗證投資金額"""
        try:
            # 獲取帳戶餘額
            balance = self.exchange.fetch_balance()
            available_usdt = float(balance['free']['USDT'])

            # 檢查可用餘額是否足夠
            if investment_amount > available_usdt:
                return {
                    'valid': False,
                    'message': f"餘額不足！可用 USDT: {available_usdt:.2f}，需要: {investment_amount:.2f}",
                    'available': available_usdt
                }

            # 檢查是否超過最大投資限額
            max_investment = available_usdt * 0.95  # 保留 5% 作為緩衝
            if investment_amount > max_investment:
                return {
                    'valid': False,
                    'message': f"投資金額過大！建議最大投資額: {max_investment:.2f} USDT",
                    'available': available_usdt,
                    'suggested': max_investment
                }

            return {
                'valid': True,
                'available': available_usdt
            }

        except Exception as e:
            logging.error(f"驗證投資金額失敗: {str(e)}")
            return {
                'valid': False,
                'message': f"驗證失敗: {str(e)}"
            }

    def get_current_price(self, symbol):
        """獲取當前價格"""
        try:
            # 使用 market/tickers API 獲取價格
            params = {'type': 'PERP'}
            response = self.make_request(
                'GET', '/api/v1/market/tickers', params=params)

            tickers = response.get('data', {}).get('tickers', [])
            for ticker in tickers:
                if ticker.get('symbol') == symbol:
                    return float(ticker.get('close', 0))

            raise ValueError(f"未找到{symbol}的價格數據")

        except Exception as e:
            logging.error(f"獲取{symbol}價格失敗: {str(e)}")
            raise

    def calculate_position_size(self, symbol, risk_amount):
        """計算倉位大小"""
        try:
            current_price = self.get_current_price(symbol)

            # 獲取市場情緒
            sentiment = self.market_analyzer.analyze_market_sentiment(symbol)

            # 計算情緒調整因子
            sentiment_factor = self.calculate_sentiment_factor(sentiment)

            # 計算基礎倉位大小
            base_position = risk_amount / current_price

            # 應用情緒調整
            adjusted_position = base_position * sentiment_factor

            return adjusted_position, current_price

        except Exception as e:
            logging.error(f"計算倉位大小失敗: {str(e)}")
            raise

    def place_order(self, symbol, side, amount):
        """下單"""
        try:
            current_price = self.get_current_price(symbol)

            # 構建訂單參數
            params = {
                'symbol': symbol,
                'side': side.upper(),
                'type': 'MARKET',
                'quantity': str(amount)
            }

            # 發送訂單請求
            response = self.make_request(
                'POST', '/api/v1/order', params=params)

            if response.get('result', False):
                order_id = response.get('data', {}).get('orderId')
                logging.info(f"下單成功: {symbol} {side} {
                             amount} @ {current_price}")
                return order_id
            else:
                raise ValueError(response.get('message', '下單失敗'))

        except Exception as e:
            logging.error(f"下單失敗: {str(e)}")
            raise

    def optimize_strategy_parameters(self, symbol):
        """優化交易策略參數"""
        try:
            market_data = self.get_market_data(
                symbol, timeframe='1h', limit=100)
            if market_data is None:
                return None

            trend_strength = self.calculate_trend_strength(market_data)
            volatility = market_data['close'].pct_change().std()
            sentiment = self.market_analyzer.analyze_market_sentiment(symbol)

            # 動態調整止盈止損
            tp_ratio = 2.0  # 基礎止盈比例
            sl_ratio = 1.0  # 基礎止損比例

            # 根據趨勢強度調整
            if trend_strength > 0.7:
                tp_ratio *= 1.5
                sl_ratio *= 0.8
            elif trend_strength < 0.3:
                tp_ratio *= 0.8
                sl_ratio *= 1.2

            # 根據波動率調整
            volatility_factor = 1 + (volatility * 10)
            tp_ratio *= volatility_factor
            sl_ratio *= volatility_factor

            # 計算倉位大小
            base_position = self.config['position_management']['position_size_limit']
            position_size = base_position * \
                (1 + trend_strength - 0.5) * (1 / (1 + volatility * 5))

            return {
                'take_profit_ratio': tp_ratio,
                'stop_loss_ratio': sl_ratio,
                'position_size': min(position_size, self.config['risk_management']['position_size_limit']),
                'trend_strength': trend_strength,
                'volatility': volatility
            }

        except Exception as e:
            logging.error(f"策略參數優化失敗: {str(e)}")
            return None

    def update_trailing_stop(self, symbol, current_price, position):
        """更新追蹤止損"""
        try:
            if not position or 'stop_loss' not in position:
                return None

            trailing_percentage = self.config['risk_management']['trailing_stop_percentage'] / 100
            original_stop = position['stop_loss']

            if position['side'] == 'buy':
                new_stop = current_price * (1 - trailing_percentage)
                return new_stop if new_stop > original_stop else original_stop
            else:
                new_stop = current_price * (1 + trailing_percentage)
                return new_stop if new_stop < original_stop else original_stop

        except Exception as e:
            logging.error(f"更新追蹤止損失敗: {str(e)}")
            return None

    def check_trend_signals(self, symbol):
        """檢查趨勢信號"""
        try:
            data = self.get_market_data(symbol, timeframe='1h', limit=50)
            if data is None:
                return None

            # 計算技術指標
            ema_short = data['close'].ewm(span=10).mean()
            ema_long = data['close'].ewm(span=30).mean()

            # MACD
            macd = data['close'].ewm(span=12).mean(
            ) - data['close'].ewm(span=26).mean()
            signal = macd.ewm(span=9).mean()

            # 趨勢信號
            signals = {
                'trend_direction': 'up' if ema_short.iloc[-1] > ema_long.iloc[-1] else 'down',
                'trend_strength': abs(ema_short.iloc[-1] - ema_long.iloc[-1]) / ema_long.iloc[-1],
                'macd_signal': 'buy' if macd.iloc[-1] > signal.iloc[-1] else 'sell',
                'momentum': (data['close'].iloc[-1] / data['close'].iloc[-10] - 1) * 100
            }

            return signals

        except Exception as e:
            logging.error(f"趨勢信號檢查失敗: {str(e)}")
            return None
