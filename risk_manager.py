import logging

class RiskManager:
    def __init__(self, config):
        self.config = config
        self.daily_pnl = 0
        self.positions = {}
        
    def check_position_risk(self, symbol, position_size, current_price):
        max_loss = self.config['risk_management']['max_loss_percentage']
        initial_price = self.positions.get(symbol, {}).get('entry_price', current_price)
        
        loss_percentage = ((current_price - initial_price) / initial_price) * 100
        
        if abs(loss_percentage) > max_loss:
            return {
                'should_close': True,
                'reason': f'Max loss threshold ({max_loss}%) exceeded'
            }
            
        return {'should_close': False}
        
    def update_daily_pnl(self, pnl):
        self.daily_pnl += pnl
        if abs(self.daily_pnl) > self.config['risk_management']['daily_loss_limit']:
            return {
                'should_stop_trading': True,
                'reason': 'Daily loss limit reached'
            }
        return {'should_stop_trading': False}

class EnhancedRiskManager:
    def __init__(self, config):
        self.config = config
        self.risk_levels = self.initialize_risk_levels()
        
    def calculate_dynamic_stop_loss(self, position, volatility):
        """動態止損計算"""
        base_stop_loss = self.config['risk_management']['base_stop_loss']
        
        # 根據波動率調整止損
        adjusted_stop_loss = base_stop_loss * (1 + volatility)
        
        # 根據盈利情況調整
        if position['unrealized_profit'] > 0:
            profit_factor = min(position['unrealized_profit'] / position['entry_price'], 0.03)
            adjusted_stop_loss = max(adjusted_stop_loss - profit_factor, base_stop_loss * 0.5)
            
        return adjusted_stop_loss 

class AdvancedRiskManager:
    def __init__(self, config):
        self.config = config
        self.risk_metrics = self.initialize_risk_metrics()
        
    def dynamic_risk_assessment(self, position, market_data):
        """動態風險評估"""
        risk_score = 0
        
        # 市場風險評估
        market_risk = self.assess_market_risk(market_data)
        
        # 倉位風險評估
        position_risk = self.assess_position_risk(position)
        
        # 資金風險評估
        capital_risk = self.assess_capital_risk()
        
        # 綜合風險評分
        risk_score = (market_risk * 0.4 + 
                     position_risk * 0.3 + 
                     capital_risk * 0.3)
                     
        return {
            'risk_score': risk_score,
            'risk_level': self.get_risk_level(risk_score),
            'suggested_actions': self.get_risk_actions(risk_score)
        }
        
    def adaptive_position_sizing(self, risk_score, market_condition):
        """自適應倉位管理"""
        base_size = self.config['base_position_size']
        
        # 根據風險分數調整
        if risk_score > 0.7:
            return base_size * 0.5  # 高風險減倉
        elif risk_score < 0.3:
            return base_size * 1.5  # 低風險加倉
            
        return base_size 

    def calculate_dynamic_targets(self, symbol, sentiment):
        """計算動態止盈止損點"""
        try:
            # 獲取市場數據
            data = self.get_market_data(symbol)
            
            # 計算 ATR
            atr = self.calculate_atr(data)
            
            # 基礎止盈止損比率
            base_tp_ratio = 3  # 基礎止盈比率
            base_sl_ratio = 2  # 基礎止損比率
            
            # 根據市場情緒調整
            if sentiment['trend_strength'] > 0.7:
                # 強趨勢時擴大止盈
                tp_ratio = base_tp_ratio * 1.5
                sl_ratio = base_sl_ratio * 0.8
            elif sentiment['volatility_level'] > 0.8:
                # 高波動時收緊止盈止損
                tp_ratio = base_tp_ratio * 0.8
                sl_ratio = base_sl_ratio * 0.6
            else:
                tp_ratio = base_tp_ratio
                sl_ratio = base_sl_ratio
            
            # 計算具體價格
            current_price = data['close'].iloc[-1]
            take_profit = current_price * (1 + tp_ratio * atr)
            stop_loss = current_price * (1 - sl_ratio * atr)
            
            return {
                'take_profit': take_profit,
                'stop_loss': stop_loss,
                'tp_ratio': tp_ratio,
                'sl_ratio': sl_ratio
            }
            
        except Exception as e:
            logging.error(f"動態止盈止損計算失敗: {str(e)}")
            return None 