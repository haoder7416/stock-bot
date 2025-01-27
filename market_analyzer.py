import logging
import time
import pandas as pd


class EnhancedMarketAnalyzer:
    def __init__(self):
        self.market_data = {}
        self.analysis_results = {}

    def get_market_data(self, symbol, timeframe='1h', limit=100):
        """獲取市場數據"""
        try:
            # 格式化交易對符號
            formatted_symbol = symbol.replace('/', '_').upper()
            if not formatted_symbol.endswith('_PERP'):
                formatted_symbol = f"{formatted_symbol}_PERP"

            # 轉換時間框架格式
            timeframe_mapping = {
                '1m': '1M',
                '5m': '5M',
                '15m': '15M',
                '30m': '30M',
                '1h': '60M',
                '4h': '4H',
                '1d': '1D'
            }
            formatted_timeframe = timeframe_mapping.get(timeframe, timeframe)

            # 構建請求參數
            params = {
                'symbol': formatted_symbol,
                'interval': formatted_timeframe,
                'limit': str(limit)
            }

            logging.info(f"正在獲取 {formatted_symbol} 的市場數據，時間間隔: {
                         formatted_timeframe}")

            # 使用交易機器人的 API 請求數據
            response = self.trading_bot.make_request(
                'GET', '/api/v1/market/klines', params)

            if not response.get('result', False):
                raise Exception(f"獲取市場數據失敗: {response.get('message', '未知錯誤')}")

            # 解析數據
            klines = response.get('data', [])
            if not klines:
                logging.warning(f"未獲取到 {formatted_symbol} 的市場數據")
                return None

            # 轉換為 DataFrame
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low',
                'close', 'volume', 'close_time', 'quote_volume',
                'trades', 'taker_base', 'taker_quote'
            ])

            # 轉換數據類型
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = df[col].astype(float)

            return df

        except Exception as e:
            logging.error(f"獲取市場數據失敗: {str(e)}")
            return None

    def set_trading_bot(self, trading_bot):
        """設置交易機器人實例"""
        self.trading_bot = trading_bot

    def comprehensive_analysis(self, symbol, timeframe='1h'):
        """綜合市場分析"""
        analysis = {
            'technical': self.technical_analysis(),
            'sentiment': self.sentiment_analysis(),
            'volume': self.volume_analysis(),
            'correlation': self.correlation_analysis(),
            'volatility': self.volatility_analysis()
        }

        # 生成市場洞察
        insights = self.generate_market_insights(analysis)

        # 制定交易建議
        recommendations = self.generate_trading_recommendations(insights)

        return {
            'analysis': analysis,
            'insights': insights,
            'recommendations': recommendations
        }

    def get_top_volume_pairs(self, trading_bot, limit=5):
        """獲取前五大交易量的合約幣種"""
        try:
            if not trading_bot:
                raise ValueError("交易機器人實例未初始化")

            # 使用正確的API端點獲取市場數據
            params = {
                'type': 'PERP'  # 指定獲取合約交易對
            }
            response = trading_bot.make_request(
                'GET', '/api/v1/market/tickers', params=params)
            logging.debug(f"Tickers API 響應: {response}")

            # 檢查響應格式
            if not isinstance(response, dict):
                raise ValueError("API響應格式錯誤")

            # 檢查result字段
            if not response.get('result', False):
                raise ValueError("無法獲取市場數據")

            # 獲取tickers數據
            tickers = response.get('data', {}).get('tickers', [])
            if not isinstance(tickers, list):
                raise ValueError("無效的tickers數據格式")

            # 篩選USDT合約對並按交易量排序
            usdt_pairs = []
            for ticker in tickers:
                try:
                    symbol = ticker.get('symbol', '')
                    if not symbol or not symbol.endswith('_USDT_PERP'):
                        continue

                    # 獲取時間戳
                    timestamp = ticker.get('time', int(time.time() * 1000))

                    # 獲取交易數據
                    volume = float(ticker.get('volume', 0))  # 24小時交易量
                    amount = float(ticker.get('amount', 0))  # 24小時交易額
                    if amount <= 0:
                        continue

                    # 處理價格數據
                    close_price = float(ticker.get('close', 0))
                    open_price = float(ticker.get('open', 0))
                    high_price = float(ticker.get('high', 0))
                    low_price = float(ticker.get('low', 0))

                    # 計算價格變化百分比
                    price_change = 0
                    if open_price > 0:
                        price_change = (
                            (close_price - open_price) / open_price) * 100

                    # 構建交易對數據
                    pair_data = {
                        'symbol': symbol,
                        'price': close_price,
                        'volume': amount,  # 使用交易額
                        'price_change': price_change,
                        'high': high_price,
                        'low': low_price,
                        'volume_coin': volume,  # 原始幣種交易量
                        'time': timestamp,  # 添加時間戳
                        'count': int(ticker.get('count', 0))  # 交易次數
                    }
                    usdt_pairs.append((symbol, amount, pair_data))
                    logging.debug(f"處理交易對數據: {pair_data}")

                except Exception as e:
                    logging.warning(f"處理交易對{symbol}時出錯: {str(e)}")
                    continue

            # 按交易額排序並取前N個
            usdt_pairs.sort(key=lambda x: x[1], reverse=True)
            top_pairs = [pair[2] for pair in usdt_pairs[:limit]]

            if not top_pairs:
                raise ValueError("未找到活躍的USDT合約交易對")

            logging.info(f"成功獲取{len(top_pairs)}個合約交易對的數據")
            return top_pairs

        except Exception as e:
            logging.error(f"獲取熱門交易對失敗: {str(e)}")
            raise

    def analyze_market_sentiment(self, symbol):
        """分析市場情緒"""
        try:
            sentiment = {
                'fear_greed_index': 50,  # 預設值
                'trend_strength': 0,
                'volume_trend': 0,
                'volatility_level': 0,
                'market_momentum': 0
            }

            # 獲取市場數據
            data = self.get_market_data(symbol, timeframe='4h', limit=100)
            if data is None:
                logging.warning(f"無法獲取 {symbol} 的市場數據")
                return sentiment

            # 計算恐懼貪婪指數
            sentiment['fear_greed_index'] = self.calculate_fear_greed_index(
                data)

            # 計算趨勢強度
            close_prices = data['close']
            ema20 = close_prices.ewm(span=20).mean()
            ema50 = close_prices.ewm(span=50).mean()
            sentiment['trend_strength'] = (
                ema20.iloc[-1] - ema50.iloc[-1]) / ema50.iloc[-1]

            # 分析成交量趨勢
            volume = data['volume']
            volume_ma = volume.rolling(window=20).mean()
            sentiment['volume_trend'] = (
                volume.iloc[-1] - volume_ma.iloc[-1]) / volume_ma.iloc[-1]

            # 計算波動率
            returns = close_prices.pct_change()
            sentiment['volatility_level'] = returns.std()

            # 計算市場動能
            sentiment['market_momentum'] = (
                close_prices.iloc[-1] / close_prices.iloc[-20] - 1)

            return sentiment

        except Exception as e:
            logging.error(f"市場情緒分析失敗: {str(e)}")
            return {
                'fear_greed_index': 50,
                'trend_strength': 0,
                'volume_trend': 0,
                'volatility_level': 0,
                'market_momentum': 0
            }

    def calculate_fear_greed_index(self, data):
        """計算恐懼貪婪指數"""
        try:
            # 價格波動率
            price_volatility = data['close'].pct_change().std()

            # 成交量變化
            volume_change = data['volume'].pct_change().mean()

            # RSI 指標
            rsi = self.calculate_rsi(data['close'])

            # 布林帶寬度
            bb_width = self.calculate_bollinger_bandwidth(data)

            # 綜合計算
            index = (
                (1 - price_volatility) * 0.3 +
                volume_change * 0.2 +
                (rsi / 100) * 0.3 +
                bb_width * 0.2
            ) * 100

            return max(0, min(100, index))

        except Exception as e:
            logging.error(f"恐懼貪婪指數計算失敗: {str(e)}")
            return 50

    def analyze_market_trend(self, symbol):
        """分析市場趨勢"""
        try:
            # 獲取市場數據，使用4小時時間框架
            data = self.get_market_data(
                symbol, '240', 100)  # 使用 240 分鐘 (4小時) 的時間間隔
            if data is None:
                return None

            # 計算趨勢強度
            trend_strength = self.calculate_trend_strength(data)

            return trend_strength

        except Exception as e:
            logging.error(f"市場趨勢分析失敗: {str(e)}")
            return None
