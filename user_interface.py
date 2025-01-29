import logging
import json
from datetime import datetime
import time
import os
from trading_bot import PionexTradingBot
from market_analyzer import EnhancedMarketAnalyzer
import getpass  # 添加 getpass 導入


class TradingUI:
    def __init__(self):
        self.trading_bot = None
        self.setup_logging()
        self.load_config()
        self.load_user_settings()

        # 初始化市場分析器
        self.market_analyzer = EnhancedMarketAnalyzer()

        # 初始化狀態變量
        self.is_trading = False
        self.current_status = "未連接"
        self.last_status_update = 0
        self.status_update_interval = 5  # 狀態更新間隔（秒）
        self.trading_start_time = None  # 添加交易開始時間變量

        # 清除終端機
        os.system('clear' if os.name == 'posix' else 'cls')

        print("\n=== Pionex 交易系統 ===\n")
        print("歡迎使用 Pionex 自動交易系統！")
        print("輸入 'help' 查看可用命令\n")

    def setup_logging(self):
        """設置日誌"""
        logging.basicConfig(
            filename=f'trading_log_{datetime.now().strftime("%Y%m%d")}.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def load_config(self):
        """載入配置"""
        try:
            with open('config.json', 'r') as f:
                self.config = json.load(f)
        except Exception as e:
            logging.error(f"載入配置文件失敗: {str(e)}")
            self.config = {}

    def load_user_settings(self):
        """載入用戶設置"""
        try:
            with open('user_settings.json', 'r') as f:
                self.settings = json.load(f)
        except Exception as e:
            logging.error(f"載入用戶設置失敗: {str(e)}")
            self.settings = {
                "investment_amount": 0,
                "leverage": 1,
                "risk_level": "保守",
                "grid_trading": True,
                "smart_entry": True,
                "auto_compound": True
            }

    def save_user_settings(self):
        """保存用戶設置"""
        try:
            with open('user_settings.json', 'w') as f:
                json.dump(self.settings, f, indent=4)
            print("\n✅ 設置已保存")
            logging.info("用戶設置已保存")
        except Exception as e:
            print(f"\n❌ 保存設置失敗: {str(e)}")
            logging.error(f"保存用戶設置失敗: {str(e)}")

    def print_help(self):
        """顯示幫助信息"""
        print("\n=== 可用命令 ===")
        print("1. start - 開始交易")
        print("2. stop - 停止交易")
        print("3. status - 查看系統狀態")
        print("4. settings - 查看/修改設置")
        print("5. account - 查看帳戶信息")
        print("6. pairs - 查看熱門交易對")
        print("7. logs - 查看交易日誌")
        print("8. clear - 清除屏幕")
        print("9. help - 顯示此幫助")
        print("10. exit - 退出系統")
        print("\n輸入命令編號或完整命令名稱來執行\n")

    def print_status(self):
        """顯示系統狀態"""
        print("\n=== 系統狀態 ===")
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"更新時間: {current_time}")

        # 顯示運行時間
        if self.is_trading and self.trading_start_time:
            running_time = datetime.now() - self.trading_start_time
            hours = running_time.total_seconds() // 3600
            minutes = (running_time.total_seconds() % 3600) // 60
            seconds = running_time.total_seconds() % 60
            print(f"運行時間: {int(hours)}小時 {int(minutes)}分鐘 {int(seconds)}秒")

        # 檢查交易機器人是否初始化
        if not self.trading_bot:
            print("\n❌ 系統狀態: 未初始化")
            print("請先使用 'start' 命令初始化交易系統")
            return

        # 檢查API連接狀態
        try:
            api_status = self.trading_bot.test_connection()
            print(f"\n🔌 API連接狀態: {'🟢 正常' if api_status else '🔴 異常'}")
        except Exception as e:
            print(f"🔴 API連接異常: {str(e)}")

        # 顯示交易狀態
        print(f"\n💫 交易狀態: {'🟢 運行中' if self.is_trading else '⚪ 未運行'}")

        # 檢查配置文件
        try:
            if not self.trading_bot.config:
                print("\n❌ 配置文件: 未找到或無效")
            else:
                print("\n⚙️ 配置狀態:")
                investment_amount = self.settings.get('investment_amount', 0)
                print(f"  - 投資金額: {investment_amount:.2f} USDT")
                print(f"  - 槓桿倍數: {self.settings.get('leverage', 1)}x")
                print(f"  - 風險等級: {self.settings.get('risk_level', '未設置')}")
        except Exception as e:
            print(f"\n❌ 配置檢查失敗: {str(e)}")

        # 獲取帳戶狀態
        try:
            account_status = self.trading_bot.get_account_status()
            if account_status:
                print("\n💰 帳戶概覽:")
                print(f"  - 總資產: {account_status['total_balance']:.2f} USDT")
                print(
                    f"  - 可用資金: {account_status['available_balance']:.2f} USDT")
                print(f"  - 資金使用率: {account_status['capital_usage']:.1f}%")

                # 顯示收益信息
                print("\n📈 收益統計:")
                daily_pnl = account_status.get('daily_pnl', 0)
                total_pnl = account_status.get('total_pnl', 0)
                win_rate = account_status.get('win_rate', 0)

                print(f"  - 日收益: {'🟢' if daily_pnl >=
                      0 else '🔴'} {daily_pnl:+.2f}%")
                print(f"  - 總收益: {'🟢' if total_pnl >=
                      0 else '🔴'} {total_pnl:+.2f}%")
                print(f"  - 勝率: {'🎯' if win_rate >=
                      50 else '🎲'} {win_rate:.1f}%")

                # 顯示持倉信息
                positions = account_status.get('position_details', {})
                if positions:
                    print("\n📊 當前持倉:")
                    for symbol, pos in positions.items():
                        pnl = pos.get('unrealized_pnl', 0)
                        roi = pos.get('roi', 0)
                        print(f"\n  {symbol}:")
                        print(f"    數量: {pos.get('amount', 0)}")
                        print(f"    均價: {pos.get('entry_price', 0):.2f}")
                        print(f"    未實現盈虧: {'🟢' if pnl >=
                              0 else '🔴'} {pnl:+.2f} USDT")
                        print(f"    收益率: {'🟢' if roi >=
                              0 else '🔴'} {roi:+.2f}%")
                else:
                    print("\n📊 當前無持倉")
        except Exception as e:
            print(f"\n❌ 獲取帳戶狀態失敗: {str(e)}")

        # 檢查系統錯誤
        try:
            # 讀取最新的錯誤日誌
            log_file = f'trading_log_{datetime.now().strftime("%Y%m%d")}.log'
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    logs = f.readlines()
                    recent_errors = [
                        log for log in logs[-10:] if 'ERROR' in log]
                    if recent_errors:
                        print("\n⚠️ 最近的系統錯誤:")
                        for error in recent_errors[-3:]:  # 只顯示最後3條錯誤
                            print(f"  ❌ {error.strip()}")
        except Exception as e:
            print(f"\n❌ 日誌檢查失敗: {str(e)}")

        # 顯示交易對狀態
        try:
            if self.trading_bot.trading_pairs:
                print("\n📊 交易對狀態:")
                for pair in self.trading_bot.trading_pairs[:3]:  # 顯示前3個交易對
                    print(f"  - {pair}")
            else:
                print("\n❌ 無可用交易對")
        except Exception as e:
            print(f"\n❌ 獲取交易對狀態失敗: {str(e)}")

        print("\n💡 提示: 使用 'help' 查看更多命令")

    def print_settings(self):
        """顯示當前設置"""
        print("\n=== 當前設置 ===")
        print(f"投資金額: {self.settings['investment_amount']:.2f} USDT")
        print(f"槓桿倍數: {self.settings['leverage']}x")
        print(f"風險等級: {self.settings['risk_level']}")
        print(f"網格交易: {'✅' if self.settings['grid_trading'] else '❌'}")
        print(f"智能入場: {'✅' if self.settings['smart_entry'] else '❌'}")
        print(f"自動複利: {'✅' if self.settings['auto_compound'] else '❌'}")
        print()

    def modify_settings(self):
        """修改設置"""
        print("\n=== 修改設置 ===")
        print("請選擇要修改的項目：")
        print("1. 投資金額設置")
        print("2. 槓桿倍數")
        print("3. 風險等級")
        print("4. 網格交易")
        print("5. 智能入場")
        print("6. 自動複利")
        print("0. 返回")

        choice = input("\n請輸入選項: ")

        if choice == "1":
            self.set_investment_amount()
        elif choice == "2":
            try:
                leverage = int(input("請輸入槓桿倍數(1-20): "))
                if 1 <= leverage <= 20:
                    self.settings['leverage'] = leverage
                    print("✅ 槓桿倍數已更新")
                else:
                    print("❌ 槓桿倍數必須在1-20之間")
            except ValueError:
                print("❌ 請輸入有效的數字")

        elif choice == "3":
            print("\n風險等級選項：")
            print("1. 保守")
            print("2. 中等")
            print("3. 激進")
            risk_choice = input("請選擇風險等級: ")
            risk_levels = {"1": "保守", "2": "中等", "3": "激進"}
            if risk_choice in risk_levels:
                self.settings['risk_level'] = risk_levels[risk_choice]
                print("✅ 風險等級已更新")
            else:
                print("❌ 無效的選擇")

        elif choice in ["4", "5", "6"]:
            setting_map = {
                "4": "grid_trading",
                "5": "smart_entry",
                "6": "auto_compound"
            }
            setting_name = setting_map[choice]
            current = self.settings[setting_name]
            self.settings[setting_name] = not current
            print(f"✅ {setting_name} 已切換為: {'開啟' if not current else '關閉'}")

        elif choice == "0":
            return

        else:
            print("❌ 無效的選項")

        # 保存更改
        self.save_user_settings()

    def set_investment_amount(self):
        """設置投資金額"""
        print("\n=== 投資金額設置 ===")
        try:
            current_amount = self.settings['investment_amount']
            print(f"當前設置: {current_amount:.2f} USDT")

            usdt_amount = float(input("\n請輸入投資金額 (USDT): "))
            if usdt_amount <= 0:
                print("❌ 金額必須大於0")
                return

            confirm = input(
                f"\n確認設置投資金額為 {usdt_amount:.2f} USDT? (y/n): ").lower()
            if confirm == 'y':
                self.settings['investment_amount'] = usdt_amount
                print(f"\n✅ 投資金額已設置為: {usdt_amount:.2f} USDT")
            else:
                print("\n❌ 已取消設置")

        except ValueError:
            print("\n❌ 請輸入有效的數字")

    def start_trading(self):
        """開始交易"""
        if self.is_trading:
            print("\n❌ 交易系統已在運行中")
            return

        try:
            print("\n正在啟動交易系統...")

            # 驗證設置
            if self.settings['investment_amount'] <= 0:
                print("❌ 請先設置投資金額")
                self.set_investment_amount()
                if self.settings['investment_amount'] <= 0:
                    return
            else:
                print(f"\n當前投資金額: {
                      self.settings['investment_amount']:.2f} USDT")

            # 初始化交易機器人
            if not self.trading_bot:
                print("\n請輸入 API 信息：")
                api_key = input("API Key: ").strip()
                api_secret = getpass.getpass("API Secret: ").strip()

                print("\n正在連接到 Pionex...")
                self.trading_bot = PionexTradingBot(api_key, api_secret)

            # 驗證投資金額
            validation = self.trading_bot.validate_investment_amount(
                self.settings['investment_amount']
            )

            if not validation['valid']:
                print(f"\n❌ {validation['message']}")
                return

            # 開始交易
            success = self.trading_bot.start_trading(self.settings)

            if success:
                self.is_trading = True
                self.current_status = "交易中"
                self.trading_start_time = datetime.now()  # 記錄開始時間
                print("\n✅ 交易系統已成功啟動！")
                logging.info("交易系統已啟動")
            else:
                print("\n❌ 交易系統啟動失敗")
                logging.error("交易系統啟動失敗")

        except Exception as e:
            print(f"\n❌ 啟動失敗: {str(e)}")
            logging.error(f"啟動交易系統失敗: {str(e)}")

    def stop_trading(self):
        """停止交易"""
        if not self.is_trading:
            print("\n❌ 交易系統未在運行")
            return

        try:
            print("\n正在安全停止交易系統...")
            # 這裡應該調用交易機器人的停止邏輯
            self.is_trading = False
            self.current_status = "已停止"
            self.trading_start_time = None  # 重置開始時間
            print("✅ 交易系統已安全停止")
            logging.info("交易系統已停止")

        except Exception as e:
            print(f"\n❌ 停止失敗: {str(e)}")
            logging.error(f"停止交易系統失敗: {str(e)}")

    def show_account_info(self):
        """顯示帳戶信息"""
        if not self.trading_bot:
            print("\n❌ 請先連接到交易所")
            return

        try:
            account_status = self.trading_bot.get_account_status()
            if account_status:
                print("\n=== 帳戶信息 ===")
                print(f"總資產: {account_status['total_balance']:.2f} USDT")
                print(f"可用資金: {account_status['available_balance']:.2f} USDT")
                print(f"資金使用率: {account_status['capital_usage']:.2f}%")

                # 收益信息
                daily_pnl = account_status['daily_pnl']
                total_pnl = account_status['total_pnl']
                win_rate = account_status['win_rate']

                print("\n=== 收益統計 ===")
                print(f"今日收益: {'🟢' if daily_pnl >=
                      0 else '🔴'} {daily_pnl:+.2f}%")
                print(f"總收益: {'🟢' if total_pnl >= 0 else '🔴'} {
                      total_pnl:+.2f}%")
                print(f"交易勝率: {'🎯' if win_rate >=
                      50 else '🎲'} {win_rate:.1f}%")

                if account_status['position_details']:
                    print("\n=== 當前持倉 ===")
                    for symbol, pos in account_status['position_details'].items():
                        print(f"\n📊 {symbol}:")
                        print(f"  持倉數量: {pos['amount']}")
                        print(f"  開倉均價: {pos['entry_price']:.2f}")

                        # 計算並顯示盈虧
                        pnl = pos['unrealized_pnl']
                        roi = pos['roi']
                        pnl_color = '🟢' if pnl >= 0 else '🔴'

                        print(f"  未實現盈虧: {pnl_color} {pnl:+.2f} USDT")
                        print(f"  收益率: {pnl_color} {roi:+.2f}%")
                else:
                    print("\n💡 當前無持倉")

        except Exception as e:
            print(f"\n❌ 獲取帳戶信息失敗: {str(e)}")
            logging.error(f"獲取帳戶信息失敗: {str(e)}")

    def show_popular_pairs(self):
        """顯示熱門交易對"""
        if not self.trading_bot:
            print("\n❌ 請先連接到交易所")
            return

        try:
            pairs_data = self.market_analyzer.get_top_volume_pairs(
                self.trading_bot)
            if pairs_data:
                print("\n=== 熱門合約交易對 ===")
                print("更新時間:", datetime.now().strftime("%H:%M:%S"))
                print("\n排名  交易對      價格          24h成交量     漲跌幅")
                print("-" * 60)

                for i, pair in enumerate(pairs_data, 1):
                    symbol = pair['symbol'].replace('_PERP', '')
                    price = pair['price']
                    volume = pair['volume']
                    change = pair['price_change']

                    # 根據漲跌幅選擇顏色
                    change_color = '🟢' if change >= 0 else '🔴'

                    # 格式化輸出
                    print(f"{i:2d}.   {symbol:<10} ${price:10,.2f}  {
                          volume:12,.0f}  {change_color} {change:+.2f}%")
                print()
            else:
                print("\n❌ 無法獲取交易對數據")

        except Exception as e:
            print(f"\n❌ 獲取熱門交易對失敗: {str(e)}")
            logging.error(f"獲取熱門交易對失敗: {str(e)}")

    def show_logs(self):
        """顯示交易日誌"""
        try:
            log_file = f'trading_log_{datetime.now().strftime("%Y%m%d")}.log'
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    logs = f.readlines()

                print("\n=== 最近的交易日誌 ===")
                print(f"顯示最後 20 條記錄 (共 {len(logs)} 條)")
                print("-" * 80)

                # 只顯示最後20條日誌
                for log in logs[-20:]:
                    # 解析日誌級別並添加對應的表情
                    if "ERROR" in log:
                        print("❌", log.strip())
                    elif "WARNING" in log:
                        print("⚠️", log.strip())
                    elif "INFO" in log:
                        print("ℹ️", log.strip())
                    else:
                        print("  ", log.strip())
            else:
                print("\n❌ 未找到今日的日誌文件")
        except Exception as e:
            print(f"\n❌ 讀取日誌失敗: {str(e)}")

    def clear_screen(self):
        """清除屏幕"""
        os.system('clear' if os.name == 'posix' else 'cls')
        print("\n=== Pionex 交易系統 ===\n")

    def run(self):
        """運行交易系統"""
        while True:
            command = input("\n請輸入命令或輸入9 (help 查看幫助): ").lower().strip()

            if command in ['1', 'start']:
                self.start_trading()
            elif command in ['2', 'stop']:
                self.stop_trading()
            elif command in ['3', 'status']:
                self.print_status()
            elif command in ['4', 'settings']:
                self.print_settings()
                self.modify_settings()
            elif command in ['5', 'account']:
                self.show_account_info()
            elif command in ['6', 'pairs']:
                self.show_popular_pairs()
            elif command in ['7', 'logs']:
                self.show_logs()
            elif command in ['8', 'clear']:
                self.clear_screen()
            elif command in ['9', 'help']:
                self.print_help()
            elif command in ['10', 'exit', 'quit']:
                if self.is_trading:
                    print("\n⚠️ 請先停止交易後再退出")
                    continue
                print("\n感謝使用！再見！")
                break
            else:
                print("\n❌ 無效的命令，輸入 'help' 查看可用命令")
