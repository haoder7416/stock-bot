import openai
import logging
from datetime import datetime
import json
import pandas as pd
import numpy as np


class AITradeAdvisor:
    def __init__(self, api_key=None):
        """初始化AI交易顧問"""
        self.api_key = api_key
        self.client = None
        if api_key:
            self.setup_client()
        self.conversation_history = []
        self.logger = logging.getLogger(__name__)

    def setup_client(self):
        """設置 OpenAI 客戶端"""
        try:
            self.client = openai.OpenAI(api_key=self.api_key)
        except Exception as e:
            self.logger.error(f"設置 OpenAI 客戶端失敗: {str(e)}")
            raise

    def validate_api_key(self):
        """驗證 OpenAI API Key 是否有效"""
        if not self.api_key:
            return False, "未提供 API Key"

        try:
            # 嘗試發送一個簡單的請求來驗證 API Key
            self.client = openai.OpenAI(api_key=self.api_key)
            response = self.client.models.list()
            return True, "API Key 驗證成功"
        except openai.AuthenticationError:
            return False, "API Key 無效或已過期"
        except openai.RateLimitError:
            return False, "達到 API 使用限制"
        except Exception as e:
            return False, f"驗證過程中發生錯誤: {str(e)}"

    def analyze_market_conditions(self, market_data, technical_indicators):
        """分析市場狀況"""
        try:
            # 如果是 DataFrame，先轉換為字典格式
            if isinstance(market_data, pd.DataFrame):
                market_data = self._prepare_market_data(market_data)
                if market_data is None:
                    raise ValueError("市場數據準備失敗")

            # 如果是字典，確保所有值都是可序列化的
            if isinstance(market_data, dict):
                market_data = self._ensure_serializable(market_data)

            # 處理技術指標
            if isinstance(technical_indicators, (pd.DataFrame, pd.Series)):
                technical_indicators = self._prepare_technical_indicators(
                    technical_indicators)
                if technical_indicators is None:
                    raise ValueError("技術指標準備失敗")
            elif isinstance(technical_indicators, dict):
                technical_indicators = self._ensure_serializable(
                    technical_indicators)

            # 準備市場分析提示
            prompt = self._prepare_market_analysis_prompt(
                market_data, technical_indicators)

            # 調用 OpenAI API
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "你是一個專業的加密貨幣市場分析師，專注於技術分析和市場情緒分析。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )

            # 解析回應
            analysis = self._parse_analysis_response(
                response.choices[0].message.content)

            if analysis:
                logging.info("AI市場分析完成")
                return analysis

            return None

        except Exception as e:
            logging.error(f"AI市場分析失敗: {str(e)}")
            return None

    def get_trading_recommendation(self, market_analysis, risk_profile):
        """獲取交易建議"""
        try:
            prompt = self._prepare_trading_recommendation_prompt(
                market_analysis, risk_profile)

            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "你是一個保守且專業的交易顧問，注重風險管理和資金保護。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5
            )

            recommendation = response.choices[0].message.content
            return self._parse_recommendation_response(recommendation)

        except Exception as e:
            logging.error(f"AI交易建議生成失敗: {str(e)}")
            return None

    def optimize_trade_parameters(self, market_conditions, historical_performance):
        """優化交易參數"""
        try:
            prompt = self._prepare_parameter_optimization_prompt(
                market_conditions,
                historical_performance
            )

            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "你是一個專業的交易策略優化專家，專注於參數調優和風險控制。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )

            parameters = response.choices[0].message.content
            return self._parse_optimization_response(parameters)

        except Exception as e:
            logging.error(f"AI參數優化失敗: {str(e)}")
            return None

    def _prepare_market_analysis_prompt(self, market_data, technical_indicators):
        """準備市場分析提示"""
        return f"""
請分析以下市場數據和技術指標，並提供詳細的市場分析：

市場數據：
{json.dumps(market_data, indent=2)}

技術指標：
{json.dumps(technical_indicators, indent=2)}

請提供：
1. 當前市場趨勢分析
2. 關鍵支撐和阻力位
3. 市場情緒評估
4. 潛在的交易機會
5. 需要注意的風險因素
"""

    def _prepare_trading_recommendation_prompt(self, market_analysis, risk_profile):
        """準備交易建議提示"""
        return f"""
基於以下市場分析和風險配置，請提供具體的交易建議：

市場分析：
{json.dumps(market_analysis, indent=2)}

風險配置：
{json.dumps(risk_profile, indent=2)}

請提供：
1. 建議的交易方向（做多/做空/觀望）
2. 建議的倉位大小
3. 建議的止損止盈位置
4. 風險管理建議
5. 特別注意事項
"""

    def _prepare_parameter_optimization_prompt(self, market_conditions, historical_performance):
        """準備參數優化提示"""
        return f"""
請基於以下市場條件和歷史表現，優化交易參數：

市場條件：
{json.dumps(market_conditions, indent=2)}

歷史表現：
{json.dumps(historical_performance, indent=2)}

請提供以下參數的優化建議：
1. 止損比例
2. 止盈比例
3. 倉位大小
4. 槓桿倍數
5. 追蹤止損設置
"""

    def _parse_analysis_response(self, response):
        """解析分析回應"""
        try:
            # 這裡可以添加更複雜的解析邏輯
            return {
                "market_trend": self._extract_market_trend(response),
                "support_resistance": self._extract_support_resistance(response),
                "market_sentiment": self._extract_market_sentiment(response),
                "trading_opportunities": self._extract_trading_opportunities(response),
                "risk_factors": self._extract_risk_factors(response)
            }
        except Exception as e:
            logging.error(f"解析AI分析回應失敗: {str(e)}")
            return None

    def _parse_recommendation_response(self, response):
        """解析建議回應"""
        try:
            # 這裡可以添加更複雜的解析邏輯
            return {
                "action": self._extract_trading_action(response),
                "position_size": self._extract_position_size(response),
                "stop_loss": self._extract_stop_loss(response),
                "take_profit": self._extract_take_profit(response),
                "risk_management": self._extract_risk_management(response)
            }
        except Exception as e:
            logging.error(f"解析AI建議回應失敗: {str(e)}")
            return None

    def _parse_optimization_response(self, response):
        """解析優化回應"""
        try:
            # 這裡可以添加更複雜的解析邏輯
            return {
                "stop_loss_ratio": self._extract_stop_loss_ratio(response),
                "take_profit_ratio": self._extract_take_profit_ratio(response),
                "position_size": self._extract_position_size_ratio(response),
                "leverage": self._extract_leverage(response),
                "trailing_stop": self._extract_trailing_stop(response)
            }
        except Exception as e:
            logging.error(f"解析AI優化回應失敗: {str(e)}")
            return None

    # 輔助方法用於提取具體資訊
    def _extract_market_trend(self, text):
        # 實現提取市場趨勢的邏輯
        pass

    def _extract_support_resistance(self, text):
        # 實現提取支撐阻力位的邏輯
        pass

    def _extract_market_sentiment(self, text):
        # 實現提取市場情緒的邏輯
        pass

    def _extract_trading_opportunities(self, text):
        # 實現提取交易機會的邏輯
        pass

    def _extract_risk_factors(self, text):
        # 實現提取風險因素的邏輯
        pass

    def _extract_trading_action(self, text):
        # 實現提取交易動作的邏輯
        pass

    def _extract_position_size(self, text):
        # 實現提取倉位大小的邏輯
        pass

    def _extract_stop_loss(self, text):
        # 實現提取止損的邏輯
        pass

    def _extract_take_profit(self, text):
        # 實現提取止盈的邏輯
        pass

    def _extract_risk_management(self, text):
        # 實現提取風險管理建議的邏輯
        pass

    def _extract_stop_loss_ratio(self, text):
        # 實現提取止損比例的邏輯
        pass

    def _extract_take_profit_ratio(self, text):
        # 實現提取止盈比例的邏輯
        pass

    def _extract_position_size_ratio(self, text):
        # 實現提取倉位大小比例的邏輯
        pass

    def _extract_leverage(self, text):
        # 實現提取槓桿倍數的邏輯
        pass

    def _extract_trailing_stop(self, text):
        # 實現提取追蹤止損的邏輯
        pass

    def _prepare_market_data(self, df):
        """準備市場數據供AI分析"""
        try:
            latest_data = df.iloc[-1]

            # 處理時間戳
            timestamp = latest_data.name
            if isinstance(timestamp, pd.Timestamp):
                timestamp = timestamp.isoformat()
            elif isinstance(timestamp, (int, float)):
                timestamp = pd.Timestamp(timestamp, unit='ms').isoformat()
            else:
                timestamp = str(timestamp)

            # 確保所有數值都是基本類型
            market_data = {
                'symbol': str(latest_data.get('symbol', '')),
                'timestamp': timestamp,
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

            return market_data

        except Exception as e:
            logging.error(f"準備市場數據失敗: {str(e)}")
            return None

    def _prepare_technical_indicators(self, df):
        """準備技術指標供AI分析"""
        try:
            # 確保所有數值都是基本類型
            indicators = {
                'rsi': float(self.calculate_rsi(df['close'])),
                'kdj': [float(x) for x in self.calculate_kdj(df)],
                'macd': [float(x) for x in self.calculate_macd(df['close'])],
                'bollinger_bands': [float(x) for x in self.calculate_bollinger_bands(df['close'])],
                'moving_averages': {
                    'ma5': float(df['close'].rolling(window=5).mean().iloc[-1]),
                    'ma10': float(df['close'].rolling(window=10).mean().iloc[-1]),
                    'ma20': float(df['close'].rolling(window=20).mean().iloc[-1])
                }
            }

            return indicators

        except Exception as e:
            logging.error(f"準備技術指標失敗: {str(e)}")
            return None

    def _ensure_serializable(self, data):
        """確保數據可序列化"""
        if isinstance(data, dict):
            return {k: self._ensure_serializable(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._ensure_serializable(item) for item in data]
        elif isinstance(data, (pd.Timestamp, datetime)):
            return data.isoformat()
        elif isinstance(data, (pd.Series, pd.DataFrame)):
            return data.to_dict()
        elif isinstance(data, np.ndarray):
            return data.tolist()
        elif isinstance(data, (int, float, str, bool, type(None))):
            return data
        else:
            return str(data)
