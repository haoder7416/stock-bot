import logging
import time
import pandas as pd


class EnhancedMarketAnalyzer:
    def __init__(self):
        self.market_data = {}
        self.analysis_results = {}

    def get_market_data(self, symbol=None, timeframe=None, limit=None):
        """獲取市場數據
        使用 Get 24hr Ticker API 獲取市場數據
        """
        try:
            # 構建請求參數
            params = {'type': 'PERP'}  # 預設獲取所有永續合約

            if symbol:
                # 格式化交易對符號
                formatted_symbol = symbol.replace('/', '_').upper()
                if not formatted_symbol.endswith('_PERP'):
                    formatted_symbol = f"{formatted_symbol}_PERP"
                params['symbol'] = formatted_symbol

            # 使用 tickers API
            response = self.trading_bot.make_request(
                'GET', '/api/v1/market/tickers', params)

            if not response.get('result', False):
                logging.error(f"獲取市場數據失敗: {response.get('message', '未知錯誤')}")
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

    def analyze_market_sentiment(self, symbol, market_data=None):
        """分析市場情緒"""
        try:
            sentiment = {
                'fear_greed_index': 50,  # 預設值
                'trend_strength': 0,
                'volume_trend': 0,
                'volatility_level': 0,
                'market_momentum': 0
            }

            # 使用傳入的市場數據或獲取新數據
            if market_data is not None:
                data = market_data
            else:
                data = self.get_market_data(symbol)
                if data is not None:
                    # 如果是新獲取的數據，需要計算技術指標
                    data = self.trading_bot.calculate_indicators(data)

            if data is None:
                logging.error(f"無法獲取 {symbol} 的市場數據")
                return None

            # 過濾特定交易對的數據
            if isinstance(data, pd.DataFrame):
                data = data[data['symbol'] == symbol]
                if data.empty:
                    logging.error(f"未找到 {symbol} 的市場數據")
                    return None

            latest_data = data.iloc[-1]

            # 檢查必要的欄位是否存在
            required_fields = ['market_strength',
                               'volume_intensity', 'true_range', 'price_change']
            missing_fields = [
                field for field in required_fields if field not in latest_data]
            if missing_fields:
                logging.error(f"缺少必要的欄位: {', '.join(missing_fields)}")
                return None

            # 計算趨勢強度
            sentiment['trend_strength'] = float(latest_data['market_strength'])

            # 分析成交量趨勢
            volume_intensity = float(latest_data['volume_intensity'])
            sentiment['volume_trend'] = 1 if volume_intensity > 1000 else -1

            # 計算波動率
            sentiment['volatility_level'] = float(
                latest_data['true_range']) / float(latest_data['close'])

            # 計算市場動能
            sentiment['market_momentum'] = float(
                latest_data['price_change']) / 100

            return sentiment

        except Exception as e:
            logging.error(f"市場情緒分析失敗: {str(e)}")
            return None

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

    def calculate_rsi(self, prices, period=14):
        """計算 RSI 指標"""
        try:
            # 計算價格變化
            delta = prices.diff()

            # 分離漲跌
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

            # 計算 RS 和 RSI
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))

            return rsi.iloc[-1] if not rsi.empty else 50

        except Exception as e:
            logging.error(f"RSI 計算失敗: {str(e)}")
            return 50

    def calculate_bollinger_bandwidth(self, data, period=20, num_std=2):
        """計算布林帶寬度"""
        try:
            # 計算移動平均
            ma = data['close'].rolling(window=period).mean()

            # 計算標準差
            std = data['close'].rolling(window=period).std()

            # 計算上下軌
            upper = ma + (std * num_std)
            lower = ma - (std * num_std)

            # 計算帶寬
            bandwidth = (upper - lower) / ma

            return bandwidth.iloc[-1] if not bandwidth.empty else 0.1

        except Exception as e:
            logging.error(f"布林帶寬度計算失敗: {str(e)}")
            return 0.1
