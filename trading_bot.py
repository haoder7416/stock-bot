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

            # 初始化交易對列表
            self.trading_pairs = []

            # 測試連接
            self.test_connection()

            # 初始化其他設置
            self.setup_logging()
            self.load_config()

            # 初始化市場分析器
            self.market_analyzer = EnhancedMarketAnalyzer()
            self.market_analyzer.set_trading_bot(self)  # 設置交易機器人實例

            # 更新交易對列表
            self.update_trading_pairs()

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
        """
        基於24小時行情數據計算技術指標
        """
        try:
            if df.empty:
                return None

            # 複製數據以避免修改原始數據
            df = df.copy()

            # 使用已計算的指標
            for index, row in df.iterrows():
                # 計算市場強度指標
                price_change = row['price_change']
                volume_intensity = row['volume_intensity']

                market_strength = 0
                if price_change > 0 and volume_intensity > 1000:
                    market_strength = 1
                elif price_change < 0 and volume_intensity > 1000:
                    market_strength = -1

                df.at[index, 'market_strength'] = market_strength

                # 計算價格位置
                price_position = (float(row['close']) - float(row['low'])) / \
                    (float(row['high']) - float(row['low'])) * \
                    100 if float(row['high']) != float(row['low']) else 50

                df.at[index, 'price_position'] = price_position

            return df

        except Exception as e:
            logging.error(f"計算技術指標失敗: {str(e)}")
            return None

    def check_signals(self, df):
        """檢查交易信號"""
        try:
            if df.empty:
                return None

            latest_data = df.iloc[-1]

            signals = {
                'price_change': latest_data['price_change'],
                'volume_intensity': latest_data['volume_intensity'],
                'market_strength': latest_data['market_strength'],
                'price_position': latest_data['price_position'],
                'should_trade': False,
                'direction': None,
                'trend_strong_up': False,
                'trend_strong_down': False,
                'rsi_oversold': False,
                'rsi_overbought': False,
                'kdj_oversold': False,
                'kdj_overbought': False
            }

            # 計算額外的技術指標
            rsi = self.calculate_rsi(df['close'])
            k, d, j = self.calculate_kdj(df)

            # RSI 超買超賣
            signals['rsi_oversold'] = rsi < 30
            signals['rsi_overbought'] = rsi > 70

            # KDJ 超買超賣
            signals['kdj_oversold'] = k < 20 and d < 20
            signals['kdj_overbought'] = k > 80 and d > 80

            # 趨勢強度判斷
            if signals['market_strength'] > 0 and signals['volume_intensity'] > 1000:
                signals['trend_strong_up'] = True
            elif signals['market_strength'] < 0 and signals['volume_intensity'] > 1000:
                signals['trend_strong_down'] = True

            # 多空信號綜合判斷
            # 做多條件：趨勢向上 + (RSI超賣 或 KDJ超賣) + 價格位置低於30%
            if signals['trend_strong_up'] and \
               (signals['rsi_oversold'] or signals['kdj_oversold']) and \
               signals['price_position'] < 30:
                signals['should_trade'] = True
                signals['direction'] = 'buy'

            # 做空條件：趨勢向下 + (RSI超買 或 KDJ超買) + 價格位置高於70%
            elif signals['trend_strong_down'] and \
                (signals['rsi_overbought'] or signals['kdj_overbought']) and \
                    signals['price_position'] > 70:
                signals['should_trade'] = True
                signals['direction'] = 'sell'

            return signals

        except Exception as e:
            logging.error(f"檢查交易信號失敗: {str(e)}")
            return None

    def calculate_rsi(self, prices, period=14):
        """計算 RSI 指標"""
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi.iloc[-1]
        except Exception as e:
            logging.error(f"RSI 計算失敗: {str(e)}")
            return 50

    def calculate_kdj(self, df, n=9, m1=3, m2=3):
        """計算 KDJ 指標"""
        try:
            low_list = df['low'].rolling(window=n).min()
            high_list = df['high'].rolling(window=n).max()
            rsv = (df['close'] - low_list) / (high_list - low_list) * 100
            k = rsv.ewm(com=m1-1, adjust=True, min_periods=0).mean()
            d = k.ewm(com=m2-1, adjust=True, min_periods=0).mean()
            j = 3 * k - 2 * d
            return k.iloc[-1], d.iloc[-1], j.iloc[-1]
        except Exception as e:
            logging.error(f"KDJ 計算失敗: {str(e)}")
            return 50, 50, 50

    def initialize_trading(self):
        """初始化交易設置"""
        try:
            # 檢查配置文件中是否已有投資金額設置
            if not self.config.get('grid_settings'):
                logging.error("配置文件中缺少網格設置")
                return False

            # 檢查每個交易對的設置
            for pair, settings in self.config['grid_settings'].items():
                if 'investment_amount' not in settings or settings['investment_amount'] <= 0:
                    logging.error(f"{pair} 缺少有效的投資金額設置")
                    return False

            logging.info("交易設置初始化成功")
            return True

        except Exception as e:
            logging.error(f"初始化交易設置失敗: {str(e)}")
            return False

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
        """分析市場狀況"""
        try:
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
        except Exception as e:
            logging.error(f"市場分析失敗: {str(e)}")
            return None

    def analyze_trend(self, df):
        """分析趨勢強度"""
        try:
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
        except Exception as e:
            logging.error(f"趨勢分析失敗: {str(e)}")
            return 0

    def analyze_volatility(self, df):
        """分析波動率"""
        try:
            # 計算波動率
            returns = df['close'].pct_change()
            volatility = returns.std()

            # 根據波動率範圍評分
            if volatility < 0.01:  # 低波動
                return 1
            elif volatility < 0.03:  # 中等波動
                return 2
            else:  # 高波動
                return 3
        except Exception as e:
            logging.error(f"波動率分析失敗: {str(e)}")
            return 0

    def analyze_volume(self, df):
        """分析成交量"""
        try:
            # 計算成交量變化
            volume_ma = df['volume'].rolling(window=20).mean()
            current_volume = df['volume'].iloc[-1]

            # 根據成交量相對於均線的位置評分
            if current_volume > volume_ma.iloc[-1] * 1.5:
                return 3  # 成交量顯著放大
            elif current_volume > volume_ma.iloc[-1]:
                return 2  # 成交量高於均線
            else:
                return 1  # 成交量低於均線
        except Exception as e:
            logging.error(f"成交量分析失敗: {str(e)}")
            return 0

    def analyze_momentum(self, df):
        """分析動量"""
        try:
            # 計算RSI
            rsi = self.calculate_rsi(df['close'])

            # 根據RSI評分
            if rsi > 70:
                return 3  # 強勢
            elif rsi < 30:
                return 1  # 弱勢
            else:
                return 2  # 中性
        except Exception as e:
            logging.error(f"動量分析失敗: {str(e)}")
            return 0

    def execute_trading_strategy(self):
        """執行交易策略"""
        try:
            # 使用 tickers API 一次性獲取所有交易對數據
            market_data = self.market_analyzer.get_market_data()
            if market_data is None or market_data.empty:
                logging.error("無法獲取市場數據")
                return

            logging.info(f"成功獲取 {len(market_data)} 個交易對的市場數據")

            # 遍歷活躍的交易對
            for pair in self.trading_pairs:
                try:
                    # 過濾特定交易對的數據
                    pair_data = market_data[market_data['symbol'] == pair]
                    if pair_data.empty:
                        logging.error(f"未找到 {pair} 的市場數據")
                        continue

                    # 計算技術指標
                    analysis = self.calculate_indicators(pair_data)
                    if analysis is None:
                        continue

                    # 獲取市場情緒（使用已計算指標的數據）
                    sentiment = self.market_analyzer.analyze_market_sentiment(
                        pair, analysis)
                    if sentiment is None:
                        continue

                    # 獲取交易信號
                    signals = self.check_signals(analysis)
                    if signals is None:
                        continue

                    # 記錄市場數據
                    latest_data = analysis.iloc[-1]
                    logging.info(f"{pair} 市場數據: 價格={latest_data['close']:.2f}, "
                                 f"24h漲跌={latest_data['price_change']:.2f}%, "
                                 f"成交量={latest_data['volume']:.2f}, "
                                 f"市場強度={latest_data['market_strength']}")

                    # 根據信號執行交易
                    if signals.get('should_trade', False):
                        try:
                            # 計算倉位大小
                            position_size = self.optimize_position_management(
                                pair, sentiment)
                            if position_size is None or position_size <= 0:
                                continue

                            # 獲取動態止盈止損點
                            targets = self.calculate_dynamic_targets(
                                pair, sentiment)
                            if targets is None:
                                continue

                            # 執行交易
                            direction = signals.get('direction')
                            if direction:
                                self.place_order(
                                    pair,
                                    direction,
                                    position_size,
                                    take_profit=targets['take_profit'],
                                    stop_loss=targets['stop_loss']
                                )
                                logging.info(f"下單成功: {pair} {direction} "
                                             f"數量={position_size:.4f} "
                                             f"止盈={
                                                 targets['take_profit']:.2f} "
                                             f"止損={targets['stop_loss']:.2f}")

                        except Exception as e:
                            logging.error(f"執行 {pair} 交易失敗: {str(e)}")
                            continue

                except Exception as e:
                    logging.error(f"處理交易對 {pair} 時發生錯誤: {str(e)}")
                    continue

        except Exception as e:
            logging.error(f"執行交易策略失敗: {str(e)}")
            raise

    def update_trading_pairs(self):
        """更新交易對列表"""
        try:
            # 獲取前五大交易量幣種
            pairs_data = self.market_analyzer.get_top_volume_pairs(self)

            if not pairs_data:
                logging.warning("未獲取到任何交易對數據")
                return

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
            response = self.make_request('GET', '/api/v1/account/balances')

            if not response.get('result', False):
                raise Exception('獲取帳戶餘額失敗')

            balances = response.get('data', {}).get('balances', [])
            available_usdt = sum(float(b['free'])
                                 for b in balances if b['coin'] == 'USDT')

            # 檢查可用餘額是否足夠
            if investment_amount > available_usdt:
                return {
                    'valid': False,
                    'message': f"餘額不足！可用 USDT: {available_usdt:.2f}，需要: {investment_amount:.2f}",
                    'available': available_usdt
                }

            # 檢查是否超過最大投資限額
            max_investment = available_usdt * 0.95  # 保留 5% 作為緩衝
            return {
                'valid': True,
                'message': '投資金額有效',
                'available': available_usdt,
                'max_investment': max_investment
            }

        except Exception as e:
            logging.error(f"驗證投資金額失敗: {str(e)}")
            return None

    def get_current_price(self, symbol):
        """獲取當前價格"""
        try:
            # 獲取最新市場數據
            ticker = self.make_request('GET', f'/api/v1/ticker/{symbol}')

            if not ticker.get('result', False):
                raise Exception('獲取價格失敗')

            return float(ticker['data']['last'])

        except Exception as e:
            logging.error(f"獲取 {symbol} 價格失敗: {str(e)}")
            return None

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

    def start_trading(self, settings):
        """開始交易"""
        try:
            logging.info("開始初始化交易設置...")

            # 驗證交易對是否存在
            if not self.trading_pairs:
                logging.error("未找到可用的交易對")
                return False

            # 記錄交易設置
            logging.info(f"當前交易設置: {settings}")
            logging.info(f"可用交易對: {self.trading_pairs}")

            # 更新配置中的投資金額
            for pair in self.trading_pairs:
                formatted_pair = pair.replace('_PERP', '').replace('_', '/')
                if formatted_pair in self.config['grid_settings']:
                    self.config['grid_settings'][formatted_pair]['investment_amount'] = settings.get(
                        'investment_amount', 0)
                    logging.info(f"已更新 {formatted_pair} 的投資金額")

            # 初始化交易設置
            if not self.initialize_trading():
                logging.error("交易初始化失敗")
                return False

            # 開始執行交易策略
            logging.info("開始執行交易策略...")
            self.execute_trading_strategy()

            logging.info("交易系統啟動成功")
            return True

        except Exception as e:
            logging.error(f"啟動交易系統失敗: {str(e)}")
            return False

    def optimize_position_management(self, pair, sentiment):
        """優化倉位管理"""
        try:
            # 獲取帳戶餘額
            account_info = self.get_account_status()
            if account_info is None:
                return None

            # 根據市場情緒調整倉位大小
            base_position = account_info['available_balance'] * 0.1
            position_size = base_position * (1 + sentiment['confidence'])

            # 確保不超過最大倉位限制
            max_position = account_info['available_balance'] * 0.3
            position_size = min(position_size, max_position)

            return position_size

        except Exception as e:
            logging.error(f"倉位優化失敗: {str(e)}")
            return None

    def calculate_dynamic_targets(self, pair, sentiment):
        """計算動態止盈止損點"""
        try:
            current_price = self.get_current_price(pair)
            if current_price is None:
                return None

            # 根據市場情緒調整止盈止損比例
            base_tp_ratio = 0.02  # 基礎止盈比例
            base_sl_ratio = 0.01  # 基礎止損比例

            # 調整止盈止損比例
            tp_ratio = base_tp_ratio * (1 + sentiment['confidence'])
            sl_ratio = base_sl_ratio * (1 - sentiment['confidence'] * 0.5)

            return {
                'take_profit': current_price * (1 + tp_ratio),
                'stop_loss': current_price * (1 - sl_ratio)
            }

        except Exception as e:
            logging.error(f"計算止盈止損點失敗: {str(e)}")
            return None
