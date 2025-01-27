class PerformanceOptimizer:
    def __init__(self, trading_bot):
        self.bot = trading_bot
        self.performance_history = []
        
    def optimize_parameters(self):
        """優化交易參數"""
        recent_performance = self.analyze_recent_performance()
        
        if recent_performance['win_rate'] < 0.6:
            self.adjust_risk_parameters('conservative')
        elif recent_performance['win_rate'] > 0.75:
            self.adjust_risk_parameters('aggressive')
            
        self.optimize_entry_points()
        self.optimize_exit_points() 