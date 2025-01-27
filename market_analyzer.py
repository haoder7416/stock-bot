import logging


class EnhancedMarketAnalyzer:
    def __init__(self):
        self.market_data = {}
        self.analysis_results = {}

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

            # 使用Pionex API獲取市場數據
            response = trading_bot.make_request(
                'GET', '/api/v1/market/tickers')

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
                    if not symbol or 'USDT' not in symbol.upper():
                        continue

                    volume = float(ticker.get('amount', 0))
                    if volume <= 0:
                        continue

                    usdt_pairs.append((symbol, volume))
                except Exception as e:
                    logging.warning(f"處理交易對{symbol}時出錯: {str(e)}")
                    continue

            # 按交易量排序並取前N個
            usdt_pairs.sort(key=lambda x: x[1], reverse=True)
            top_pairs = usdt_pairs[:limit]

            # 獲取詳細數據
            pairs_data = []
            for symbol, _ in top_pairs:
                try:
                    ticker_data = trading_bot.fetch_ticker(symbol)
                    pairs_data.append(ticker_data)
                except Exception as e:
                    logging.warning(f"獲取{symbol}詳細數據失敗: {str(e)}")
                    continue

            if not pairs_data:
                raise ValueError("未找到活躍的USDT交易對")

            logging.info(f"成功獲取{len(pairs_data)}個交易對的詳細數據")
            return pairs_data

        except Exception as e:
            logging.error(f"獲取熱門交易對失敗: {str(e)}")
            raise

    def analyze_market_sentiment(self, symbol):
        """分析市場情緒"""
        try:
            sentiment = {
                'fear_greed_index': 0,
                'trend_strength': 0,
                'volume_trend': 0,
                'volatility_level': 0,
                'market_momentum': 0
            }

            # 獲取市場數據
            data = self.get_market_data(symbol, '4h', 100)

            # 計算恐懼貪婪指數
            sentiment['fear_greed_index'] = self.calculate_fear_greed_index(
                data)

            # 計算趨勢強度
            sentiment['trend_strength'] = self.calculate_trend_strength(data)

            # 分析成交量趨勢
            sentiment['volume_trend'] = self.analyze_volume_trend(data)

            # 計算波動率水平
            sentiment['volatility_level'] = self.calculate_volatility(data)

            # 計算市場動能
            sentiment['market_momentum'] = self.calculate_momentum(data)

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
