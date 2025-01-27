class MarketSentiment:
    def __init__(self):
        self.fear_greed_index = None
        self.market_trends = {}
        
    def analyze_market_sentiment(self):
        """分析市場情緒"""
        sentiment_score = 0
        
        # 分析恐懼貪婪指數
        if self.fear_greed_index < 20:  # 極度恐懼
            sentiment_score += 2  # 可能是買入機會
        elif self.fear_greed_index > 80:  # 極度貪婪
            sentiment_score -= 2  # 可能需要謹慎
            
        # 分析市場趨勢
        if self.market_trends['short_term'] == 'up' and \
           self.market_trends['mid_term'] == 'up':
            sentiment_score += 1
            
        return sentiment_score 