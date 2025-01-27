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

    def get_top_volume_pairs(self, exchange, limit=5):
        """獲取前五大交易量的合約幣種"""
        try:
            # 獲取所有市場數據
            markets = exchange.fetch_markets()
            
            # 篩選USDT合約對
            futures_pairs = [
                market['symbol'] for market in markets 
                if market['quote'] == 'USDT' and 
                market['type'] == 'future'
            ]
            
            # 獲取24小時交易量
            volumes = []
            for pair in futures_pairs:
                ticker = exchange.fetch_ticker(pair)
                volumes.append((
                    pair,
                    ticker['quoteVolume']  # USDT交易量
                ))
            
            # 按交易量排序並返回前5個
            return sorted(
                volumes,
                key=lambda x: x[1],
                reverse=True
            )[:limit]
            
        except Exception as e:
            logging.error(f"獲取交易量數據失敗: {str(e)}")
            return [] 

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
            sentiment['fear_greed_index'] = self.calculate_fear_greed_index(data)
            
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