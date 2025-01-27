from datetime import datetime  # 添加這行在文件頂部的導入區域

class AdvancedReportSystem:
    def __init__(self):
        self.daily_reports = []
        self.weekly_reports = []
        
    def generate_smart_report(self, trading_data, market_condition):
        """生成智能分析報告"""
        report = {
            'summary': self.generate_summary(trading_data),
            'risk_analysis': self.analyze_risk_metrics(trading_data),
            'market_insight': self.analyze_market_condition(market_condition),
            'recommendations': self.generate_recommendations(trading_data)
        }
        
        # 生成人性化報告
        report_message = f"""
📊 交易日報 ({datetime.now().strftime('%Y-%m-%d %H:%M')})

🔸 整體表現
- 當日獲利: {report['summary']['daily_profit']} USDT
- 當日勝率: {report['summary']['win_rate']}%
- 最大單筆獲利: {report['summary']['max_profit']} USDT
- 平均持倉時間: {report['summary']['avg_hold_time']} 小時

🔸 風險指標
- 當前風險等級: {report['risk_analysis']['risk_level']}
- 資金使用率: {report['risk_analysis']['capital_usage']}%
- 最大回撤: {report['risk_analysis']['max_drawdown']}%

🔸 市場洞察
- 市場趨勢: {report['market_insight']['trend']}
- 波動程度: {report['market_insight']['volatility']}
- 建議策略: {report['market_insight']['strategy']}

🔸 投資建議
{report['recommendations']['action_points']}

⚠️ 風險提醒
{report['recommendations']['risk_warnings']}
        """
        
        return report_message 