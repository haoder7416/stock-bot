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
from ai_trade_advisor import AITradeAdvisor


class PionexTradingBot:
    def __init__(self, api_key, api_secret, openai_api_key=None):
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
            self.market_analyzer.set_trading_bot(self)

            # 初始化AI交易顧問（只使用傳入的API key，不從配置文件讀取）
            self.ai_advisor = None
            if openai_api_key:
                self.ai_advisor = AITradeAdvisor(openai_api_key)
                logging.info("AI交易顧問初始化成功")

            # 更新交易對列表
            self.update_trading_pairs()

            # 記錄成功初始化
            logging.info("交易系統初始化成功")

        except Exception as e:
            logging.error(f"初始化失敗: {str(e)}")
            raise Exception(f"交易所連接失敗: {str(e)}")

    def generate_signature(self, params, method, endpoint):
        """生成 API 簽名"""
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

            # 構建簽名字符串：METHOD + ENDPOINT + QUERY
            sign_str = f"{method.upper()}{endpoint}"
            if param_str:
                sign_str = f"{sign_str}?{param_str}"

            # 使用 HMAC-SHA256 生成簽名
            signature = hmac.new(
                self.api_secret.encode('utf-8'),
                sign_str.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()

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

    def get_market_data(self, symbol=None, timeframe='1m', limit=100):
        """獲取市場數據"""
        try:
            # 構建請求參數
            params = {'type': 'PERP'}  # 預設獲取永續合約數據

            if symbol:
                # 格式化交易對符號
                formatted_symbol = symbol.replace('/', '_').upper()
                if not formatted_symbol.endswith('_PERP'):
                    formatted_symbol = f"{formatted_symbol}_PERP"
                params['symbol'] = formatted_symbol

            # 使用 tickers API 獲取24小時行情數據
            response = self.make_request(
                'GET', '/api/v1/market/tickers', params)

            if not response.get('result', False):
                error_msg = response.get('message', '未知錯誤')
                logging.error(f"獲取市場數據失敗: {error_msg}")
                return None

            tickers = response.get('data', {}).get('tickers', [])
            if not tickers:
                logging.error("未獲取到任何市場數據")
                return None

            # 轉換為 DataFrame
            df = pd.DataFrame(tickers)

            # 過濾出永續合約數據
            df = df[df['symbol'].str.endswith('_PERP')]

            if df.empty:
                logging.error("未找到任何永續合約數據")
                return None

            # 重命名列以匹配現有代碼
            df = df.rename(columns={
                'time': 'timestamp',
                'amount': 'quote_volume',
                'count': 'trades'
            })

            # 轉換數據類型
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            numeric_columns = ['open', 'high', 'low',
                               'close', 'volume', 'quote_volume']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')

            # 如果指定了特定交易對，過濾數據
            if symbol:
                df = df[df['symbol'] == params['symbol']]
                if df.empty:
                    logging.error(f"未找到 {symbol} 的市場數據")
                    return None

            # 添加基本的技術指標
            df['price_change'] = (
                (df['close'] - df['open']) / df['open'] * 100)
            df['true_range'] = df.apply(lambda x: max(
                x['high'] - x['low'],
                abs(x['high'] - x['close']),
                abs(x['low'] - x['close'])
            ), axis=1)
            df['volume_intensity'] = df['volume'] * df['close']
            df['market_strength'] = df['price_change']

            logging.info(f"成功獲取市場數據: {len(df)} 筆")
            return df

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

            # 獲取基本信號
            signals = self._get_basic_signals(df)

            # 如果有AI顧問，獲取AI分析和建議
            if self.ai_advisor:
                # 準備市場數據
                market_data = self._prepare_market_data(df)
                # 準備技術指標
                technical_indicators = self._prepare_technical_indicators(df)

                # 獲取AI市場分析
                ai_analysis = self.ai_advisor.analyze_market_conditions(
                    market_data,
                    technical_indicators
                )

                if ai_analysis:
                    # 獲取AI交易建議
                    risk_profile = self._get_risk_profile()
                    ai_recommendation = self.ai_advisor.get_trading_recommendation(
                        ai_analysis,
                        risk_profile
                    )

                    # 整合AI建議到信號中
                    if ai_recommendation:
                        signals.update({
                            'ai_analysis': ai_analysis,
                            'ai_recommendation': ai_recommendation,
                            'should_trade': signals['should_trade'] or ai_recommendation['action'] != 'hold',
                            'direction': ai_recommendation['action'] if ai_recommendation['action'] != 'hold' else signals['direction']
                        })

            return signals

        except Exception as e:
            logging.error(f"檢查交易信號失敗: {str(e)}")
            return None

    def _get_basic_signals(self, df):
        """獲取基本交易信號"""
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

        # 計算技術指標
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
        if signals['trend_strong_up'] and \
           (signals['rsi_oversold'] or signals['kdj_oversold']) and \
           signals['price_position'] < 30:
            signals['should_trade'] = True
            signals['direction'] = 'buy'
        elif signals['trend_strong_down'] and \
            (signals['rsi_overbought'] or signals['kdj_overbought']) and \
                signals['price_position'] > 70:
            signals['should_trade'] = True
            signals['direction'] = 'sell'

        return signals

    def _prepare_market_data(self, df):
        """準備市場數據供AI分析"""
        latest_data = df.iloc[-1]
        return {
            'symbol': self.current_symbol,
            'timestamp': latest_data.name.isoformat(),
            'price': {
                'open': float(latest_data['open']),
                'high': float(latest_data['high']),
                'low': float(latest_data['low']),
                'close': float(latest_data['close'])
            },
            'volume': float(latest_data['volume']),
            'price_change': float(latest_data['price_change']),
            'volume_intensity': float(latest_data['volume_intensity'])
        }

    def _prepare_technical_indicators(self, df):
        """準備技術指標供AI分析"""
        return {
            'rsi': self.calculate_rsi(df['close']),
            'kdj': self.calculate_kdj(df),
            'macd': self.calculate_macd(df['close']),
            'bollinger_bands': self.calculate_bollinger_bands(df['close']),
            'moving_averages': self.calculate_moving_averages(df['close'])
        }

    def _get_risk_profile(self):
        """獲取風險配置"""
        return {
            'risk_level': self.config.get('risk_level', 'moderate'),
            'max_position_size': self.config.get('max_position_size', 0.1),
            'max_leverage': self.config.get('max_leverage', 3),
            'stop_loss_percentage': self.config.get('stop_loss_percentage', 2),
            'take_profit_percentage': self.config.get('take_profit_percentage', 6)
        }

    def optimize_strategy_parameters(self, market_conditions):
        """優化策略參數"""
        try:
            # 獲取歷史表現數據
            historical_performance = self._get_historical_performance()

            # 如果有AI顧問，使用AI優化參數
            if self.ai_advisor:
                optimized_params = self.ai_advisor.optimize_trade_parameters(
                    market_conditions,
                    historical_performance
                )

                if optimized_params:
                    # 更新配置
                    self._update_strategy_parameters(optimized_params)
                    return True

            return False

        except Exception as e:
            logging.error(f"優化策略參數失敗: {str(e)}")
            return False

    def _get_historical_performance(self):
        """獲取歷史表現數據"""
        return {
            'win_rate': self.calculate_win_rate(),
            'profit_loss_ratio': self.calculate_profit_loss_ratio(),
            'max_drawdown': self.calculate_max_drawdown(),
            'sharpe_ratio': self.calculate_sharpe_ratio(),
            'average_holding_time': self.calculate_average_holding_time()
        }

    def _update_strategy_parameters(self, params):
        """更新策略參數"""
        try:
            if params.get('stop_loss_ratio'):
                self.config['stop_loss_percentage'] = params['stop_loss_ratio']

            if params.get('take_profit_ratio'):
                self.config['take_profit_percentage'] = params['take_profit_ratio']

            if params.get('position_size'):
                self.config['position_size'] = params['position_size']

            if params.get('leverage'):
                self.config['leverage'] = params['leverage']

            if params.get('trailing_stop'):
                self.config['trailing_stop'] = params['trailing_stop']

            # 保存更新後的配置
            self.save_config()

        except Exception as e:
            logging.error(f"更新策略參數失敗: {str(e)}")

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
            if df is None or df.empty:
                logging.error("市場數據為空")
                return None

            signals = self.check_signals(df)
            if signals is None:
                logging.error("無法獲取交易信號")
                return None

            market_state = {
                'trend': self.analyze_trend(df),
                'volatility': self.analyze_volatility(df),
                'volume': self.analyze_volume(df),
                'momentum': self.analyze_momentum(df)
            }

            # 檢查是否有任何指標為 None
            if any(v is None for v in market_state.values()):
                logging.error("部分市場指標計算失敗")
                return None

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
            if 'EMA50' not in df.columns or 'EMA200' not in df.columns:
                # 計算需要的 EMA
                df['EMA50'] = df['close'].ewm(span=50, adjust=False).mean()
                df['EMA200'] = df['close'].ewm(span=200, adjust=False).mean()

            trend_score = 0
            last_row = df.iloc[-1]

            # EMA趨勢
            if last_row['EMA50'] > last_row['EMA200']:
                trend_score += 2

            # 價格位置
            if last_row['close'] > last_row['EMA50']:
                trend_score += 1

            # 趨勢持續性
            price_trend = df['close'].diff().rolling(window=20).mean().iloc[-1]
            if price_trend > 0:
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

    def execute_trading_strategy(self, pair, analysis):
        """執行交易策略"""
        try:
            if not analysis or not isinstance(analysis, dict):
                logging.error("分析結果無效")
                return

            # 根據分析結果執行交易
            if analysis.get('should_trade', False):
                trade_direction = analysis.get('trade_direction')

                if trade_direction == 'buy':
                    # 執行買入邏輯
                    self.place_buy_order(pair, analysis)
                elif trade_direction == 'sell':
                    # 執行賣出邏輯
                    self.place_sell_order(pair, analysis)
                else:
                    logging.warning(f"無效的交易方向: {trade_direction}")

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
            # 確保交易對格式正確
            formatted_symbol = symbol.replace('/', '_').upper()
            if not formatted_symbol.endswith('_PERP'):
                formatted_symbol = f"{formatted_symbol}_PERP"

            # 獲取最新市場數據
            params = {'symbol': formatted_symbol}
            ticker = self.make_request('GET', '/api/v1/ticker/price', params)

            if not ticker.get('result', False):
                raise Exception('獲取價格失敗')

            return float(ticker['data']['price'])

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

    def start_trading(self, settings):
        """開始交易"""
        try:
            # 驗證設置
            if not settings:
                raise ValueError("未提供交易設置")

            # 更新交易設置
            self.settings = settings

            # 初始化交易狀態
            self.is_trading = True
            self.last_check_time = time.time()

            # 開始交易循環
            self.trading_loop()

            return True

        except Exception as e:
            logging.error(f"啟動交易失敗: {str(e)}")
            return False

    def trading_loop(self):
        """交易主循環"""
        try:
            while self.is_trading:
                # 獲取市場數據
                for pair in self.trading_pairs:
                    try:
                        # 使用標準化的時間間隔
                        market_data = self.get_market_data(
                            pair, timeframe='1m')
                        if market_data is None or market_data.empty:
                            logging.warning(f"無法獲取 {pair} 的市場數據")
                            continue

                        # 分析市場狀況
                        analysis = self.market_analyzer.analyze_market(
                            market_data)
                        if analysis is None:
                            logging.warning(f"無法分析 {pair} 的市場狀況")
                            continue

                        # 如果啟用了AI顧問，獲取AI建議
                        if self.ai_advisor:
                            try:
                                ai_analysis = self.ai_advisor.analyze_market_conditions(
                                    market_data,
                                    analysis.get('indicators', {})
                                )
                                if ai_analysis:
                                    analysis['ai_analysis'] = ai_analysis
                            except Exception as e:
                                logging.error(f"AI分析失敗: {str(e)}")
                                continue

                        # 執行交易策略
                        if analysis.get('should_trade'):
                            self.execute_trading_strategy(pair, analysis)

                    except Exception as e:
                        logging.error(f"處理 {pair} 時發生錯誤: {str(e)}")
                        continue

                # 等待一段時間再進行下一次檢查
                time.sleep(60)  # 每分鐘檢查一次

        except Exception as e:
            logging.error(f"交易循環執行失敗: {str(e)}")
            self.is_trading = False
            raise

    def place_buy_order(self, pair, analysis):
        """執行買入訂單"""
        try:
            # 獲取當前價格
            current_price = self.get_current_price(pair)
            if current_price is None:
                raise ValueError("無法獲取當前價格")

            # 計算倉位大小
            position_size = self.optimize_position_management(
                pair, analysis['sentiment'])
            if position_size is None or position_size <= 0:
                raise ValueError("無效的倉位大小")

            # 計算止盈止損點
            targets = self.calculate_dynamic_targets(
                pair, analysis['sentiment'])
            if targets is None:
                raise ValueError("無法計算止盈止損點")

            # 執行市價買入訂單
            order_id = self.place_order(pair, 'buy', position_size)
            if order_id:
                logging.info(f"買入訂單執行成功: {pair} 數量={
                             position_size:.4f} 價格={current_price:.2f}")
                logging.info(f"止盈={targets['take_profit']:.2f} 止損={
                             targets['stop_loss']:.2f}")
                return order_id
            return None

        except Exception as e:
            logging.error(f"買入訂單執行失敗: {str(e)}")
            return None

    def place_sell_order(self, pair, analysis):
        """執行賣出訂單"""
        try:
            # 獲取當前價格
            current_price = self.get_current_price(pair)
            if current_price is None:
                logging.error(f"無法獲取 {pair} 的當前價格")
                return None

            # 檢查是否有足夠的餘額
            account_info = self.get_account_status()
            if account_info is None or account_info['available_balance'] <= 0:
                logging.error("無法獲取帳戶資訊或餘額不足")
                return None

            # 計算倉位大小
            position_size = self.optimize_position_management(
                pair, analysis.get('sentiment', {'confidence': 0.5}))
            if position_size is None or position_size <= 0:
                logging.error("無效的倉位大小")
                return None

            # 計算止盈止損點
            targets = self.calculate_dynamic_targets(
                pair, analysis.get('sentiment', {'confidence': 0.5}))
            if targets is None:
                logging.error("無法計算止盈止損點")
                return None

            # 執行市價賣出訂單
            order_id = self.place_order(pair, 'sell', position_size)
            if order_id:
                logging.info(f"賣出訂單執行成功: {pair} 數量={
                             position_size:.4f} 價格={current_price:.2f}")
                logging.info(f"止盈={targets['take_profit']:.2f} 止損={
                             targets['stop_loss']:.2f}")
                return order_id

            logging.error("訂單執行失敗")
            return None

        except Exception as e:
            logging.error(f"賣出訂單執行失敗: {str(e)}")
            return None
