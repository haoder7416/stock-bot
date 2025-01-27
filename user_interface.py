import tkinter as tk
from tkinter import ttk, messagebox, font
import json
from PIL import Image, ImageTk
from datetime import datetime
import logging
from market_analyzer import EnhancedMarketAnalyzer
from trading_bot import PionexTradingBot


class TradingUI:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("交易系統")
        self.window.geometry("1200x800")
        self.window.minsize(800, 600)

        # 初始化字體設置
        self.init_fonts()

        # 設置網格配置權重
        self.window.grid_columnconfigure(0, weight=1)
        self.window.grid_columnconfigure(1, weight=2)
        self.window.grid_rowconfigure(1, weight=1)

        # 綁定視窗大小變化事件
        self.window.bind('<Configure>', self.on_window_resize)

        # 現代化深色主題 (Nord Dark)
        self.dark_theme = {
            'bg': '#2E3440',           # 深沉背景
            'surface': '#3B4252',       # 表面層
            'card': '#434C5E',          # 卡片背景
            'input': '#4C566A',         # 輸入框
            'text': '#ECEFF4',          # 主要文字
            'text_muted': '#D8DEE9',    # 次要文字
            'primary': '#88C0D0',       # 主要按鈕
            'primary_hover': '#8FBCBB',  # 按鈕懸停
            'success': '#A3BE8C',       # 成功
            'warning': '#EBCB8B',       # 警告
            'error': '#BF616A',         # 錯誤
            'info': '#81A1C1',          # 信息
            'border': '#434C5E',        # 邊框
            'shadow': '0 2px 4px rgba(0,0,0,0.2)',  # 陰影
            'gradient': 'linear-gradient(135deg, #2E3440, #3B4252)'  # 漸變
        }

        # 柔和淺色主題 (Nord Light)
        self.light_theme = {
            'bg': '#ECEFF4',           # 淺色背景
            'surface': '#E5E9F0',       # 表面層
            'card': '#D8DEE9',          # 卡片背景
            'input': '#FFFFFF',         # 輸入框
            'text': '#2E3440',          # 主要文字
            'text_muted': '#4C566A',    # 次要文字
            'primary': '#5E81AC',       # 主要按鈕
            'primary_hover': '#81A1C1',  # 按鈕懸停
            'success': '#A3BE8C',       # 成功
            'warning': '#EBCB8B',       # 警告
            'error': '#BF616A',         # 錯誤
            'info': '#88C0D0',          # 信息
            'border': '#D8DEE9',        # 邊框
            'shadow': '0 2px 4px rgba(0,0,0,0.1)',  # 陰影
            'gradient': 'linear-gradient(135deg, #ECEFF4, #E5E9F0)'  # 漸變
        }

        self.current_theme = self.dark_theme
        self.style = ttk.Style()

        # 先創建所有介面元素
        self.create_widgets()

        # 更新樣式
        self.update_styles()

        # 最後禁用所有交易相關設置
        self.disable_trading_settings()

    def init_fonts(self):
        """初始化字體設置"""
        available_fonts = font.families()

        # 優先使用現代字體
        heading_font = next((f for f in [
            'Inter',
            'Roboto',
            'SF Pro Display',
            '微軟正黑體',
            'Arial'
        ] if f in available_fonts), 'Arial')

        body_font = next((f for f in [
            'Inter',
            'Roboto',
            'SF Pro Text',
            '微軟正黑體',
            'Arial'
        ] if f in available_fonts), 'Arial')

        # 更新字體設置
        self.fonts = {
            'h1': (heading_font, 24, 'bold'),    # 主標題
            'h2': (heading_font, 20, 'bold'),    # 次標題
            'h3': (heading_font, 16, 'bold'),    # 小標題
            'body': (body_font, 14),             # 正文
            'small': (body_font, 12),            # 小字
            'tiny': (body_font, 11),             # 最小字
            'mono': ('JetBrains Mono', 13)       # 等寬字體
        }

        # 設置基礎字體大小
        self.font_size = 13

    def on_window_resize(self, event):
        """處理視窗大小變化"""
        if not hasattr(self, 'last_width'):
            self.last_width = event.width
            self.last_height = event.height
            return

        # 檢查是否真的改變了大小
        if event.width != self.last_width or event.height != self.last_height:
            self.last_width = event.width
            self.last_height = event.height
            self.adjust_layout()

    def adjust_layout(self):
        """根據視窗大小調整布局"""
        window_width = self.window.winfo_width()

        # 當視窗寬度小於 1000 像素時，切換為單列布局
        if window_width < 1000:
            self.switch_to_single_column()
        else:
            self.switch_to_double_column()

    def switch_to_single_column(self):
        """切換到單列布局"""
        for widget in self.window.grid_slaves():
            if int(widget.grid_info()['column']) == 1:
                widget.grid(column=0, row=int(widget.grid_info()['row']) + 10)

    def switch_to_double_column(self):
        """切換到雙列布局"""
        widgets = self.window.grid_slaves()
        for widget in widgets:
            if int(widget.grid_info()['row']) > 10:
                widget.grid(column=1, row=int(widget.grid_info()['row']) - 10)

    def create_widgets(self):
        """創建所有介面元素"""
        # 頂部導航欄
        self.create_navbar()

        # 左側面板 (API和設置)
        left_panel = self.create_panel("設置", 0)
        left_panel.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        left_panel.grid_columnconfigure(0, weight=1)

        # 創建設置區域（包含滾動條）
        self.create_settings_section(left_panel)

        # 右側面板 (交易和監控)
        right_panel = self.create_panel("交易", 1)
        right_panel.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)
        right_panel.grid_columnconfigure(0, weight=1)

        # 創建帳戶狀態區域
        self.create_account_status_section(right_panel)

        # 創建交易狀態監控區域
        self.create_status_section(right_panel)

    def create_navbar(self):
        """創建頂部導航欄"""
        navbar = ttk.Frame(self.window, style='Navbar.TFrame')
        navbar.grid(row=0, column=0, columnspan=2, sticky="ew")

        # Logo和標題
        logo_frame = ttk.Frame(navbar)
        logo_frame.pack(side="left", padx=20)

        ttk.Label(
            logo_frame,
            text="交易系統",
            style='Logo.TLabel'
        ).pack(side="left")

        # 字體大小控制
        controls = ttk.Frame(navbar)
        controls.pack(side="right", padx=20)

        ttk.Label(
            controls,
            text="文字大小:",
            style='Control.TLabel'
        ).pack(side="left", padx=(0, 5))

        ttk.Button(
            controls,
            text="-",
            width=2,
            style='Control.TButton',
            command=self.decrease_font_size
        ).pack(side="left", padx=1)

        ttk.Button(
            controls,
            text="+",
            width=2,
            style='Control.TButton',
            command=self.increase_font_size
        ).pack(side="left", padx=1)

    def create_panel(self, title, column):
        """創建面板基礎結構"""
        panel = ttk.Frame(self.window, style='Panel.TFrame')
        panel.grid(row=1, column=column, sticky="nsew", padx=10, pady=10)

        # 面板標題
        ttk.Label(
            panel,
            text=title,
            style='PanelTitle.TLabel'
        ).pack(fill="x", padx=15, pady=10)

        return panel

    def start_trading(self):
        """開始交易"""
        if not self.validate_inputs():
            return

        try:
            # 獲取設置
            settings = self.get_settings()
            if not settings:
                return

            # 再次確認投資金額
            confirm = messagebox.askyesno("確認",
                                          f"確定要投資 {
                                              settings['investment_amount']:.2f} USDT 開始交易嗎？\n"
                                          f"槓桿倍數: {settings['leverage']}x\n"
                                          f"風險等級: {settings['risk_level']}"
                                          )

            if not confirm:
                return

            # 禁用所有交易相關設置
            self.disable_trading_settings()

            # 開始交易
            self.update_status("交易系統啟動中...")
            self.bot.start_trading(settings)

        except Exception as e:
            self.update_status(f"啟動失敗: {str(e)}")
            messagebox.showerror("錯誤", f"啟動失敗: {str(e)}")
            self.enable_trading_settings()

    def stop_trading(self):
        """停止交易"""
        if hasattr(self, 'bot'):
            self.update_status("正在安全停止交易系統...")
            # 停止交易邏輯
            self.update_status("交易系統已停止")

            # 啟用所有交易相關設置
            self.enable_trading_settings()

    def disable_trading_settings(self):
        """禁用所有交易相關設置"""
        # 禁用投資金額設置
        if hasattr(self, 'investment_amount'):
            self.investment_amount.configure(state='disabled')
            self.investment_amount_value.configure(state='disabled')

        # 禁用槓桿設置
        if hasattr(self, 'leverage'):
            self.leverage.configure(state='disabled')
            self.leverage_value.configure(state='disabled')
            for button in self.leverage_buttons.winfo_children():
                button.configure(state='disabled')

        # 禁用風險等級設置
        if hasattr(self, 'risk_frame'):
            for widget in self.risk_frame.winfo_children():
                if isinstance(widget, ttk.Radiobutton):
                    widget.configure(state='disabled')

        # 禁用策略設置
        if hasattr(self, 'strategy_frame'):
            for widget in self.strategy_frame.winfo_children():
                if isinstance(widget, ttk.Checkbutton):
                    widget.configure(state='disabled')

        # 禁用保存設置按鈕
        if hasattr(self, 'save_button'):
            self.save_button.configure(state='disabled')

        # 更新按鈕狀態
        if hasattr(self, 'start_button'):
            self.start_button.configure(state='disabled')
        if hasattr(self, 'stop_button'):
            self.stop_button.configure(state='disabled')

    def enable_trading_settings(self):
        """啟用所有交易相關設置"""
        # 啟用投資金額設置
        if hasattr(self, 'investment_amount'):
            self.investment_amount.configure(state='normal')
            self.investment_amount_value.configure(state='normal')

        # 啟用槓桿設置
        if hasattr(self, 'leverage'):
            self.leverage.configure(state='normal')
            self.leverage_value.configure(state='normal')
            for button in self.leverage_buttons.winfo_children():
                button.configure(state='normal')

        # 啟用風險等級設置
        if hasattr(self, 'risk_frame'):
            for widget in self.risk_frame.winfo_children():
                if isinstance(widget, ttk.Radiobutton):
                    widget.configure(state='normal')

        # 啟用策略設置
        if hasattr(self, 'strategy_frame'):
            for widget in self.strategy_frame.winfo_children():
                if isinstance(widget, ttk.Checkbutton):
                    widget.configure(state='normal')

        # 啟用保存設置按鈕
        if hasattr(self, 'save_button'):
            self.save_button.configure(state='normal')

        # 更新按鈕狀態
        if hasattr(self, 'start_button'):
            self.start_button.configure(state='normal')
        if hasattr(self, 'stop_button'):
            self.stop_button.configure(state='disabled')

    def save_settings(self):
        """保存設置"""
        settings = self.get_settings()
        if settings:  # 只有在設置有效時才保存
            try:
                # 獲取舊設置（如果存在）
                old_settings = {}
                try:
                    with open('user_settings.json', 'r') as f:
                        old_settings = json.load(f)
                        # 保留原有的API金鑰（如果存在）
                        if 'api_key' in old_settings:
                            settings['api_key'] = old_settings['api_key']
                        if 'api_secret' in old_settings:
                            settings['api_secret'] = old_settings['api_secret']
                except FileNotFoundError:
                    # 如果檔案不存在，移除API金鑰相關資訊
                    settings.pop('api_key', None)
                    settings.pop('api_secret', None)

                # 保存新設置（不包含API金鑰）
                settings_to_save = {k: v for k, v in settings.items() if k not in [
                    'api_key', 'api_secret']}
                with open('user_settings.json', 'w') as f:
                    json.dump(settings_to_save, f, indent=4)

                # 記錄變更到日誌
                self.update_status("設置已保存，更新內容：")

                # 比較並記錄變更（排除API金鑰）
                for key, new_value in settings_to_save.items():
                    old_value = old_settings.get(key)
                    if old_value != new_value:
                        self.update_status(
                            f"- {key}: {old_value} → {new_value}")

                messagebox.showinfo("成功", "設置已保存")

            except Exception as e:
                messagebox.showerror("錯誤", f"保存失敗: {str(e)}")
                self.update_status(f"保存設置失敗: {str(e)}")

    def validate_inputs(self):
        """驗證輸入"""
        if not self.api_key.get() or not self.api_secret.get():
            messagebox.showerror("錯誤", "請輸入 API 金鑰")
            return False

        try:
            investment_amount = float(self.investment_amount.get())
            if investment_amount <= 0:
                raise ValueError("投資金額必須大於 0")

            # 驗證投資金額
            if hasattr(self, 'bot'):
                # 獲取帳戶狀態
                status = self.bot.get_account_status()
                if status:
                    total_balance = float(status['total_balance'])
                    if investment_amount > total_balance:
                        messagebox.showerror(
                            "錯誤", f"投資金額不能超過總資產 ({total_balance:.2f} USDT)")

                        # 自動將投資金額設為總資產的值
                        self.investment_amount.delete(0, tk.END)
                        self.investment_amount.insert(0, str(total_balance))
                        return False

                validation = self.bot.validate_investment_amount(
                    investment_amount)
                if not validation['valid']:
                    messagebox.showerror("錯誤", validation['message'])

                    # 如果有建議金額，詢問是否使用
                    if 'suggested' in validation:
                        if messagebox.askyesno("建議", f"是否使用建議投資金額 {validation['suggested']:.2f} USDT？"):
                            self.investment_amount.delete(0, tk.END)
                            self.investment_amount.insert(
                                0, str(validation['suggested']))
                            return self.validate_inputs()  # 重新驗證
                    return False

                # 顯示可用餘額資訊
                self.update_status(
                    f"可用餘額: {validation['available']:.2f} USDT\n"
                    f"計劃投資: {investment_amount:.2f} USDT"
                )

        except ValueError as e:
            messagebox.showerror("錯誤", str(e))
            return False

        return True

    def get_settings(self):
        """獲取設置，並進行數據驗證"""
        try:
            # 直接獲取滑動條的值（已經是float類型）
            investment_amount = float(self.investment_amount.get())
            leverage = float(self.leverage.get())

            # 驗證投資金額
            if investment_amount <= 0:
                raise ValueError("請輸入投資金額")

            # 驗證槓桿倍數
            if not 1 <= leverage <= 20:
                raise ValueError("槓桿倍數必須在 1-20 倍之間")

            return {
                'api_key': self.api_key.get().strip(),
                'api_secret': self.api_secret.get().strip(),
                'investment_amount': investment_amount,
                'leverage': int(leverage),
                'risk_level': self.risk_level.get(),
                'grid_trading': self.grid_trading.get(),
                'smart_entry': self.smart_entry.get(),
                'auto_compound': self.auto_compound.get()
            }
        except ValueError as e:
            messagebox.showerror("錯誤", str(e))
            return None

    def update_status(self, message):
        self.status_text.insert("end", f"{message}\n")
        self.status_text.see("end")

    def update_styles(self):
        """更新所有樣式"""
        # 基礎樣式
        self.style.configure('.',
                             font=(self.fonts['body'][0], self.font_size),
                             background=self.current_theme['bg'],
                             foreground=self.current_theme['text']
                             )

        # 輸入框樣式
        self.style.configure('TEntry',
                             font=(self.fonts['body'][0], self.font_size),
                             fieldbackground=self.current_theme['input'],
                             foreground=self.current_theme['text'],
                             padding=8
                             )

        # 滑動條樣式
        self.style.configure('TScale',
                             background=self.current_theme['surface']
                             )

        # 導航欄樣式
        self.style.configure('Navbar.TFrame',
                             background=self.current_theme['surface'],
                             relief="flat"
                             )

        # Logo樣式
        self.style.configure('Logo.TLabel',
                             font=(self.fonts['h1'][0],
                                   self.font_size + 8, 'bold'),
                             foreground=self.current_theme['primary'],
                             background=self.current_theme['surface'],
                             padding=(0, 15)
                             )

        # 控制按鈕樣式
        self.style.configure('Control.TButton',
                             font=(self.fonts['body'][0], self.font_size),
                             padding=3
                             )

        self.style.configure('Control.TLabel',
                             font=(self.fonts['body'][0], self.font_size),
                             background=self.current_theme['surface']
                             )

        # 面板樣式
        self.style.configure('Panel.TFrame',
                             background=self.current_theme['surface'],
                             relief="flat",
                             borderwidth=0
                             )

        # 面板標題樣式
        self.style.configure('PanelTitle.TLabel',
                             font=(self.fonts['h1'][0],
                                   self.font_size + 6, 'bold'),
                             background=self.current_theme['surface'],
                             foreground=self.current_theme['text'],
                             padding=(0, 10)
                             )

        # 標籤框架樣式
        self.style.configure('Card.TLabelframe',
                             font=(self.fonts['h2'][0],
                                   self.font_size + 2, 'bold'),
                             background=self.current_theme['surface'],
                             foreground=self.current_theme['text'],
                             borderwidth=1,
                             relief="solid",
                             padding=15
                             )

        self.style.configure('Card.TLabelframe.Label',
                             font=(self.fonts['h2'][0],
                                   self.font_size + 2, 'bold'),
                             background=self.current_theme['surface'],
                             foreground=self.current_theme['text']
                             )

        # 輸入框標籤樣式
        self.style.configure('FieldLabel.TLabel',
                             font=(self.fonts['body'][0], self.font_size),
                             background=self.current_theme['surface'],
                             foreground=self.current_theme['text']
                             )

        # 更新文本框字體（這是 tk 組件，可以直接設置字體）
        if hasattr(self, 'status_text'):
            self.status_text.configure(
                font=(self.fonts['mono'][0], self.font_size)
            )

        if hasattr(self, 'trade_history_text'):
            self.trade_history_text.configure(
                font=(self.fonts['mono'][0], self.font_size)
            )

        # 更新輸入框樣式
        self.style.configure('TEntry',
                             font=(self.fonts['body'][0], self.font_size),
                             padding=8
                             )

        # 更新單選按鈕樣式
        self.style.configure('TRadiobutton',
                             font=(self.fonts['body'][0], self.font_size),
                             background=self.current_theme['surface']
                             )

    def increase_font_size(self):
        """增加字體大小"""
        if self.font_size < 20:
            self.font_size += 1
            self.update_styles()
            self.update_status(f"字體大小已調整為: {self.font_size}")

    def decrease_font_size(self):
        """減小字體大小"""
        if self.font_size > 8:
            self.font_size -= 1
            self.update_styles()
            self.update_status(f"字體大小已調整為: {self.font_size}")

    def toggle_theme(self):
        """切換深色/淺色主題"""
        self.current_theme = self.dark_theme if self.current_theme == self.light_theme else self.light_theme
        self.update_styles()

        # 更新主題按鈕文字
        self.theme_button.configure(text="切換主題")

    def run(self):
        self.window.mainloop()

    def create_settings_section(self, parent):
        """創建設置區域"""
        # 創建一個容器來包含所有設置
        settings_container = ttk.Frame(parent)
        settings_container.pack(fill="both", expand=True)  # 移除 padx 和 pady

        # 創建一個 Canvas 和滾動條
        canvas = tk.Canvas(settings_container,
                           bg=self.current_theme['surface'],
                           highlightthickness=0,  # 移除白色外框
                           bd=0)  # 移除邊框
        scrollbar = ttk.Scrollbar(
            settings_container, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        # 配置滾動
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        # 調整 canvas window 的寬度以填滿整個區域
        def configure_canvas(event):
            canvas.itemconfig('window', width=event.width)
        canvas.bind('<Configure>', configure_canvas)

        # 創建 window 時設置 tag
        canvas.create_window((0, 0), window=scrollable_frame,
                             anchor="nw", tags='window')
        canvas.configure(yscrollcommand=scrollbar.set)

        # 打包滾動元素（移除間距）
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # API 設置
        settings_frame = ttk.LabelFrame(
            scrollable_frame,
            text="API 設置",
            style='Card.TLabelframe'
        )
        settings_frame.pack(fill="x", pady=5)

        # API Key 輸入
        api_key_frame = ttk.Frame(settings_frame)
        api_key_frame.pack(fill="x", padx=5, pady=2)
        ttk.Label(api_key_frame, text="API Key",
                  style='FieldLabel.TLabel').pack(side="top", anchor="w")
        self.api_key_entry = ttk.Entry(api_key_frame, width=50)
        self.api_key_entry.pack(side="top", fill="x")

        # API Secret 輸入
        api_secret_frame = ttk.Frame(settings_frame)
        api_secret_frame.pack(fill="x", padx=5, pady=2)
        ttk.Label(api_secret_frame, text="API Secret",
                  style='FieldLabel.TLabel').pack(side="top", anchor="w")
        self.api_secret_entry = ttk.Entry(api_secret_frame, show="*", width=50)
        self.api_secret_entry.pack(side="top", fill="x")

        # 顯示密碼選項和連接按鈕框架
        control_frame = ttk.Frame(settings_frame)
        control_frame.pack(fill="x", padx=5, pady=2)

        # 顯示密碼選項
        self.show_secret_var = tk.BooleanVar()
        self.show_secret_check = ttk.Checkbutton(
            control_frame,
            text="顯示",
            variable=self.show_secret_var,
            command=self.toggle_secret_display,
            style='Switch.TCheckbutton'
        )
        self.show_secret_check.pack(side="left")

        # 連接狀態指示
        self.connection_status = ttk.Label(
            control_frame,
            text="● 未連接",
            style='StatusError.TLabel'
        )
        self.connection_status.pack(side="left", padx=10)

        # 按鈕框架
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(side="right")

        # 連接按鈕
        self.connect_button = ttk.Button(
            button_frame,
            text="連接交易所",
            style='Primary.TButton',
            command=self.connect_exchange
        )
        self.connect_button.pack(side="left", padx=5)

        # 取消連線按鈕
        self.disconnect_button = ttk.Button(
            button_frame,
            text="取消連線",
            style='Error.TButton',
            command=self.disconnect_exchange,
            state='disabled'
        )
        self.disconnect_button.pack(side="left", padx=5)

        # 投資設置
        self.create_investment_section(scrollable_frame)

        # 風險管理
        self.create_risk_section(scrollable_frame)

        # 交易策略
        self.create_strategy_section(scrollable_frame)

        # 熱門合約交易對
        self.create_popular_pairs_section(scrollable_frame)

        # 綁定滾輪事件
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)

    def connect_exchange(self):
        """連接交易所"""
        try:
            api_key = self.api_key_entry.get().strip()
            api_secret = self.api_secret_entry.get().strip()

            if not api_key or not api_secret:
                self.add_log("請輸入 API Key 和 Secret", "error")
                return

            # 初始化交易機器人
            self.trading_bot = PionexTradingBot(api_key, api_secret)

            # 更新UI狀態
            self.connection_status.configure(
                text="● 已連接", style='StatusSuccess.TLabel')
            self.connect_button.configure(state='disabled')
            self.disconnect_button.configure(state='normal')

            # 禁用輸入欄位
            self.api_key_entry.configure(state='disabled')
            self.api_secret_entry.configure(state='disabled')
            self.show_secret_check.configure(state='disabled')

            # 啟用交易相關按鈕
            self.start_button.configure(state='normal')

            self.add_log("成功連接到交易所", "success")

        except Exception as e:
            self.add_log(f"連接失敗: {str(e)}", "error")

    def disconnect_exchange(self):
        """取消連線"""
        try:
            # 停止所有交易
            self.stop_trading()

            # 清理交易機器人實例
            self.trading_bot = None

            # 更新UI狀態
            self.connection_status.configure(
                text="● 未連接", style='StatusError.TLabel')
            self.connect_button.configure(state='normal')
            self.disconnect_button.configure(state='disabled')

            # 啟用輸入欄位
            self.api_key_entry.configure(state='normal')
            self.api_secret_entry.configure(state='normal')
            self.show_secret_check.configure(state='normal')

            # 禁用交易相關按鈕
            self.start_button.configure(state='disabled')
            self.stop_button.configure(state='disabled')

            # 重置顯示
            self.reset_display()

            self.add_log("已斷開連接", "info")

        except Exception as e:
            self.add_log(f"斷開連接時發生錯誤: {str(e)}", "error")

    def reset_display(self):
        """重置所有顯示為初始狀態"""
        try:
            # 重置狀態顯示
            self.status_indicator.configure(
                text="⚪ 未連接", style='StatusError.TLabel')
            self.price_label.configure(text="BTC: $ --,---")

            # 重置策略分析顯示
            self.trend_label.configure(text="--")
            self.volatility_label.configure(text="--")
            self.signal_label.configure(text="--")

            # 重置交易對顯示
            for row in self.pair_rows:
                for label in row:
                    label.configure(text="--")

        except Exception as e:
            logging.error(f"重置顯示失敗: {str(e)}")
            self.add_log(f"重置顯示失敗: {str(e)}", "error")

    def create_investment_section(self, parent):
        """創建投資設置區域"""
        inv_frame = ttk.LabelFrame(
            parent, text="投資設置", style='Card.TLabelframe', padding=15)
        inv_frame.pack(fill="x", padx=10, pady=5)

        # 投資金額設置
        amount_frame = ttk.Frame(inv_frame)
        amount_frame.pack(fill="x", pady=10)

        ttk.Label(
            amount_frame,
            text="投資金額 (USDT):",
            style='FieldLabel.TLabel'
        ).pack(side="left")

        # 投資金額滑動條
        self.investment_amount = ttk.Scale(
            amount_frame,
            from_=0,
            to=100,  # 初始最大值，將在連接後更新
            orient="horizontal",
            command=self.update_investment_amount
        )
        self.investment_amount.pack(side="left", fill="x", expand=True, padx=5)
        self.investment_amount.set(0)  # 設置預設值

        # 投資金額顯示
        self.investment_amount_value = ttk.Label(
            amount_frame,
            text="0.00",
            style='FieldLabel.TLabel'
        )
        self.investment_amount_value.pack(side="left", padx=5)

        # 槓桿倍數設置
        leverage_frame = ttk.Frame(inv_frame)
        leverage_frame.pack(fill="x", pady=10)

        ttk.Label(
            leverage_frame,
            text="槓桿倍數:",
            style='FieldLabel.TLabel'
        ).pack(side="left")

        # 槓桿倍數滑動條
        self.leverage = ttk.Scale(
            leverage_frame,
            from_=1,
            to=20,
            orient="horizontal",
            command=self.update_leverage_value
        )
        self.leverage.pack(side="left", fill="x", expand=True, padx=5)
        self.leverage.set(5)  # 設置預設值

        # 槓桿倍數顯示
        self.leverage_value = ttk.Label(
            leverage_frame,
            text="5x",
            style='FieldLabel.TLabel'
        )
        self.leverage_value.pack(side="left", padx=5)

        # 快速選擇按鈕
        self.leverage_buttons = ttk.Frame(inv_frame)
        self.leverage_buttons.pack(fill="x", pady=5)

        for value in [1, 3, 5, 10, 20]:
            ttk.Button(
                self.leverage_buttons,
                text=f"{value}x",
                style='Leverage.TButton',
                command=lambda v=value: self.set_leverage(v)
            ).pack(side="left", padx=2, expand=True)

    def update_investment_amount(self, value):
        """更新投資金額顯示"""
        try:
            value = float(value)
            if hasattr(self, 'investment_amount_value'):
                self.investment_amount_value.configure(text=f"{value:.2f}")
        except (ValueError, AttributeError) as e:
            print(f"更新投資金額時出錯: {e}")

    def update_leverage_value(self, value):
        """更新槓桿倍數顯示"""
        try:
            value = int(float(value))
            if hasattr(self, 'leverage_value'):
                self.leverage_value.configure(text=f"{value}x")
        except (ValueError, AttributeError) as e:
            print(f"更新槓桿值時出錯: {e}")

    def set_leverage(self, value):
        """設置槓桿倍數"""
        self.leverage.set(value)
        self.leverage_value.configure(text=f"{value}x")

    def create_risk_section(self, parent):
        """創建風險管理區域"""
        risk_frame = ttk.LabelFrame(
            parent,
            text="風險管理",
            style='Card.TLabelframe',
            padding=15
        )
        risk_frame.pack(fill="x", padx=10, pady=5)

        # 風險等級選擇
        self.risk_level = tk.StringVar(value="中等")
        risk_options = ["保守", "中等", "激進"]

        ttk.Label(
            risk_frame,
            text="風險等級:",
            style='FieldLabel.TLabel'
        ).pack(anchor="w")

        # 創建風險等級選擇按鈕
        for option in risk_options:
            ttk.Radiobutton(
                risk_frame,
                text=option,
                value=option,
                variable=self.risk_level
            ).pack(anchor="w", pady=2)

    def create_strategy_section(self, parent):
        """創建交易策略區域"""
        strategy_frame = ttk.LabelFrame(
            parent, text="交易策略", style='Card.TLabelframe', padding=15)
        strategy_frame.pack(fill="x", padx=10, pady=5)

        # 策略選項
        self.grid_trading = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            strategy_frame,
            text="網格交易",
            variable=self.grid_trading
        ).pack(anchor="w", pady=2)

        self.smart_entry = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            strategy_frame,
            text="智能入場",
            variable=self.smart_entry
        ).pack(anchor="w", pady=2)

        self.auto_compound = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            strategy_frame,
            text="自動複利",
            variable=self.auto_compound
        ).pack(anchor="w", pady=2)

    def create_account_status_section(self, parent):
        """創建帳戶狀態區域"""
        status_frame = ttk.LabelFrame(
            parent,
            text="帳戶狀態",
            style='Card.TLabelframe'
        )
        status_frame.pack(fill="x", padx=10, pady=5)

        # 資產概覽
        overview_frame = ttk.Frame(status_frame)
        overview_frame.pack(fill="x", padx=10, pady=5)

        # 左側 - 總資產和收益
        left_frame = ttk.Frame(overview_frame)
        left_frame.pack(side="left", padx=20)

        # 總資產
        ttk.Label(
            left_frame,
            text="總資產 (USDT)",
            style='FieldLabel.TLabel'
        ).pack()

        self.total_balance_label = ttk.Label(
            left_frame,
            text="--,---",
            style='ValueLarge.TLabel'
        )
        self.total_balance_label.pack()

        # 總收益
        ttk.Label(
            left_frame,
            text="總收益",
            style='FieldLabel.TLabel'
        ).pack(pady=(10, 0))

        self.total_pnl_label = ttk.Label(
            left_frame,
            text="+0.00%",
            style='ValueSuccess.TLabel'
        )
        self.total_pnl_label.pack()

        # 中間 - 可用資金和日收益
        middle_frame = ttk.Frame(overview_frame)
        middle_frame.pack(side="left", padx=20)

        # 可用資金
        ttk.Label(
            middle_frame,
            text="可用資金",
            style='FieldLabel.TLabel'
        ).pack()

        self.available_balance_label = ttk.Label(
            middle_frame,
            text="--,---",
            style='ValueLarge.TLabel'
        )
        self.available_balance_label.pack()

        # 日收益
        ttk.Label(
            middle_frame,
            text="今日收益",
            style='FieldLabel.TLabel'
        ).pack(pady=(10, 0))

        self.daily_pnl_label = ttk.Label(
            middle_frame,
            text="+0.00%",
            style='ValueSuccess.TLabel'
        )
        self.daily_pnl_label.pack()

        # 右側 - 資金使用率和交易統計
        right_frame = ttk.Frame(overview_frame)
        right_frame.pack(side="left", padx=20)

        # 資金使用率
        ttk.Label(
            right_frame,
            text="資金使用率",
            style='FieldLabel.TLabel'
        ).pack()

        self.capital_usage_label = ttk.Label(
            right_frame,
            text="---%",
            style='ValueLarge.TLabel'
        )
        self.capital_usage_label.pack()

        # 交易勝率
        ttk.Label(
            right_frame,
            text="交易勝率",
            style='FieldLabel.TLabel'
        ).pack(pady=(10, 0))

        self.win_rate_label = ttk.Label(
            right_frame,
            text="0.00%",
            style='ValueInfo.TLabel'
        )
        self.win_rate_label.pack()

        # 持倉詳情
        position_frame = ttk.LabelFrame(
            status_frame,
            text="當前持倉",
            style='Card.TLabelframe'
        )
        position_frame.pack(fill="x", padx=10, pady=5)

        # 持倉表頭
        header_frame = ttk.Frame(position_frame)
        header_frame.pack(fill="x", padx=10, pady=(5, 0))

        headers = ["交易對", "持倉數量", "開倉均價", "當前價格", "未實現盈虧", "收益率", "槓桿"]
        for i, header in enumerate(headers):
            ttk.Label(
                header_frame,
                text=header,
                style='FieldLabel.TLabel'
            ).grid(row=0, column=i, padx=5)

        # 持倉內容容器
        self.position_container = ttk.Frame(position_frame)
        self.position_container.pack(fill="x", padx=10, pady=5)

        # 歷史交易
        history_frame = ttk.LabelFrame(
            status_frame,
            text="今日交易記錄",
            style='Card.TLabelframe'
        )
        history_frame.pack(fill="x", padx=10, pady=5)

        self.trade_history_text = tk.Text(
            history_frame,
            height=4,
            wrap='none',
            font=self.fonts['mono']
        )
        self.trade_history_text.pack(fill="x", padx=10, pady=5)

    def create_popular_pairs_section(self, parent):
        """創建熱門合約交易對區域"""
        volume_frame = ttk.LabelFrame(
            parent,
            text="熱門合約交易對",
            style='Card.TLabelframe'
        )
        volume_frame.pack(fill="x", padx=10, pady=5)

        # 創建表格式布局
        self.pairs_container = ttk.Frame(volume_frame)
        self.pairs_container.pack(fill="x", padx=10, pady=5)

        # 創建表頭
        headers = ["排名", "交易對", "交易額"]
        for i, header in enumerate(headers):
            ttk.Label(
                self.pairs_container,
                text=header,
                style='FieldLabel.TLabel'
            ).grid(row=0, column=i, padx=5, sticky='w')

        # 創建交易對行
        self.pair_rows = []
        for i in range(5):
            row_labels = []
            for j in range(len(headers)):
                label = ttk.Label(
                    self.pairs_container,
                    text="--",
                    style='Info.TLabel'
                )
                label.grid(row=i+1, column=j, padx=5, pady=2, sticky='w')
                row_labels.append(label)
            self.pair_rows.append(row_labels)

    def update_popular_pairs(self, pairs_data):
        """更新熱門合約交易對顯示"""
        try:
            if not pairs_data:
                logging.warning("未收到交易對數據")
                return

            for i, pair_data in enumerate(pairs_data):
                if i >= len(self.pair_rows):
                    logging.warning(f"超出顯示限制: {i + 1}")
                    break

                # 更新排名
                self.pair_rows[i][0].configure(text=f"#{i+1}")

                # 更新交易對名稱
                symbol = pair_data['symbol'].replace(
                    '_USDT_PERP', '')  # 移除 _USDT_PERP 後綴以簡化顯示
                self.pair_rows[i][1].configure(text=f"{symbol}/USDT")

                # 更新交易額，使用億/萬作為單位
                volume = pair_data['volume']
                if volume >= 100_000_000:  # 1億
                    volume_text = f"{volume/100_000_000:.2f}億"
                else:
                    volume_text = f"{volume/10_000:.2f}萬"
                self.pair_rows[i][2].configure(text=volume_text)

            logging.info("成功更新熱門合約交易對顯示")

        except Exception as e:
            logging.error(f"更新熱門合約交易對顯示失敗: {str(e)}")
            self.add_log(f"更新熱門合約交易對顯示失敗: {str(e)}", "error")

    def create_status_section(self, parent):
        """創建交易狀態監控區域"""
        status_frame = ttk.LabelFrame(
            parent,
            text="交易狀態監控",
            style='Card.TLabelframe'
        )
        status_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # 建立左右分割面板
        paned = ttk.PanedWindow(status_frame, orient="horizontal")
        paned.pack(fill="both", expand=True, padx=5, pady=5)

        # 左側面板 - 交易狀態和數據
        left_frame = ttk.Frame(paned)
        paned.add(left_frame, weight=1)

        # 交易狀態指示器
        status_indicator_frame = ttk.Frame(left_frame)
        status_indicator_frame.pack(fill="x", padx=5, pady=5)

        self.status_indicator = ttk.Label(
            status_indicator_frame,
            text="⚪ 未連接",
            style='StatusError.TLabel'
        )
        self.status_indicator.pack(side="left", padx=(0, 15))

        self.price_label = ttk.Label(
            status_indicator_frame,
            text="BTC: $ --,---",
            style='StatusInfo.TLabel'
        )
        self.price_label.pack(side="right")

        # 交易策略分析結果
        strategy_frame = ttk.LabelFrame(
            left_frame,
            text="策略分析",
            style='Card.TLabelframe'
        )
        strategy_frame.pack(fill="x", padx=5, pady=5)

        # 市場趨勢
        trend_frame = ttk.Frame(strategy_frame)
        trend_frame.pack(fill="x", padx=5, pady=2)
        ttk.Label(trend_frame, text="市場趨勢:",
                  style='FieldLabel.TLabel').pack(side="left")
        self.trend_label = ttk.Label(
            trend_frame, text="--", style='ValueInfo.TLabel')
        self.trend_label.pack(side="right")

        # 波動性
        volatility_frame = ttk.Frame(strategy_frame)
        volatility_frame.pack(fill="x", padx=5, pady=2)
        ttk.Label(volatility_frame, text="波動性:",
                  style='FieldLabel.TLabel').pack(side="left")
        self.volatility_label = ttk.Label(
            volatility_frame, text="--", style='ValueInfo.TLabel')
        self.volatility_label.pack(side="right")

        # 交易信號
        signal_frame = ttk.Frame(strategy_frame)
        signal_frame.pack(fill="x", padx=5, pady=2)
        ttk.Label(signal_frame, text="交易信號:",
                  style='FieldLabel.TLabel').pack(side="left")
        self.signal_label = ttk.Label(
            signal_frame, text="--", style='ValueInfo.TLabel')
        self.signal_label.pack(side="right")

        # 右側面板 - 日誌和歷史記錄
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=2)

        # 交易日誌區域
        log_frame = ttk.LabelFrame(
            right_frame, text="交易日誌", style='Card.TLabelframe')
        log_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # 日誌工具欄
        toolbar = ttk.Frame(log_frame)
        toolbar.pack(fill="x", pady=(0, 5))

        # 日誌過濾選項
        self.log_filter = tk.StringVar(value="全部")
        filter_frame = ttk.Frame(toolbar)
        filter_frame.pack(side="left")

        for filter_type in ["全部", "交易", "信號", "系統"]:
            ttk.Radiobutton(
                filter_frame,
                text=filter_type,
                value=filter_type,
                variable=self.log_filter,
                command=self.filter_logs,
                style='Small.TRadiobutton'
            ).pack(side="left", padx=5)

        # 清除按鈕
        ttk.Button(
            toolbar,
            text="清除日誌",
            style='Tool.TButton',
            command=self.clear_log
        ).pack(side="right")

        # 日誌顯示區域
        log_container = ttk.Frame(log_frame)
        log_container.pack(fill="both", expand=True)

        # 垂直滾動條
        scrollbar = ttk.Scrollbar(log_container)
        scrollbar.pack(side="right", fill="y")

        # 水平滾動條
        h_scrollbar = ttk.Scrollbar(log_container, orient="horizontal")
        h_scrollbar.pack(side="bottom", fill="x")

        # 日誌文本區域
        self.status_text = tk.Text(
            log_container,
            height=12,
            wrap="none",  # 不自動換行
            font=self.fonts['mono'],
            relief="flat",
            padx=10,
            pady=10
        )
        self.status_text.pack(fill="both", expand=True)

        # 設置標籤和顏色
        self.status_text.tag_configure(
            "trade", foreground=self.current_theme['success'])
        self.status_text.tag_configure(
            "signal", foreground=self.current_theme['info'])
        self.status_text.tag_configure(
            "system", foreground=self.current_theme['text'])
        self.status_text.tag_configure(
            "error", foreground=self.current_theme['error'])
        self.status_text.tag_configure(
            "warning", foreground=self.current_theme['warning'])

        # 連接滾動條
        self.status_text.configure(
            yscrollcommand=scrollbar.set,
            xscrollcommand=h_scrollbar.set
        )
        scrollbar.configure(command=self.status_text.yview)
        h_scrollbar.configure(command=self.status_text.xview)

        # 控制按鈕區域
        self.create_control_buttons(status_frame)

    def filter_logs(self):
        """根據選擇的過濾條件顯示日誌"""
        filter_type = self.log_filter.get()

        try:
            # 獲取所有日誌內容
            all_content = self.status_text.get(1.0, tk.END)
            self.status_text.delete(1.0, tk.END)

            # 如果選擇顯示全部，直接返回所有內容
            if filter_type == "全部":
                self.status_text.insert(tk.END, all_content)
                return

            # 按行處理日誌
            for line in all_content.split('\n'):
                if line.strip():
                    # 根據不同類型的日誌進行過濾
                    if filter_type == "交易" and "[交易]" in line:
                        self.status_text.insert(tk.END, line + "\n", "trade")
                    elif filter_type == "信號" and "[信號]" in line:
                        self.status_text.insert(tk.END, line + "\n", "signal")
                    elif filter_type == "系統" and "[系統]" in line:
                        self.status_text.insert(tk.END, line + "\n", "system")

        except Exception as e:
            logging.error(f"過濾日誌時發生錯誤: {str(e)}")
            messagebox.showerror("錯誤", f"過濾日誌失敗: {str(e)}")
            # 發生錯誤時恢復原始內容
            self.status_text.delete(1.0, tk.END)
            self.status_text.insert(tk.END, all_content)

    def add_log(self, message, log_type="system"):
        """添加日誌訊息"""
        # 使用完整的日期時間格式
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 根據日誌類型添加標籤
        type_label = {
            "system": "[系統]",
            "trade": "[交易]",
            "signal": "[信號]",
            "error": "[錯誤]",
            "warning": "[警告]"
        }.get(log_type, "[系統]")

        # 組合日誌條目
        log_entry = f"[{timestamp}] {type_label} {message}\n"

        self.status_text.insert(tk.END, log_entry, log_type)
        self.status_text.see(tk.END)  # 自動滾動到最新的日誌

        # 如果當前有過濾，則根據過濾條件顯示/隱藏
        if self.log_filter.get() != "全部":
            self.filter_logs()

    def update_strategy_analysis(self, analysis):
        """更新策略分析結果"""
        if not analysis:
            return

        # 更新市場趨勢
        trend = analysis.get('trend', {})
        trend_text = f"{trend.get('direction', '--')
                        } ({trend.get('strength', 0)}%)"
        self.trend_label.configure(text=trend_text)

        # 更新波動性
        volatility = analysis.get('volatility', {})
        volatility_text = f"{volatility.get(
            'level', '--')} ({volatility.get('value', 0)}%)"
        self.volatility_label.configure(text=volatility_text)

        # 更新交易信號
        signals = analysis.get('signals', [])
        signal_text = ', '.join(signals) if signals else '--'
        self.signal_label.configure(text=signal_text)

    def create_target_section(self, parent):
        """創建盈虧目標設置區域"""
        target_frame = ttk.LabelFrame(
            parent,
            text="目標設置",
            style='Card.TLabelframe'
        )
        target_frame.pack(fill="x", padx=10, pady=5)

        # 止盈目標
        profit_frame = ttk.Frame(target_frame)
        profit_frame.pack(fill="x", pady=5)

        ttk.Label(
            profit_frame,
            text="止盈目標:",
            style='FieldLabel.TLabel'
        ).pack(side="left")

        self.take_profit = ttk.Entry(profit_frame, width=8)
        self.take_profit.pack(side="left", padx=5)
        self.take_profit.insert(0, "3.0")

        ttk.Label(
            profit_frame,
            text="%",
            style='FieldLabel.TLabel'
        ).pack(side="left")

        # 止損設置
        loss_frame = ttk.Frame(target_frame)
        loss_frame.pack(fill="x", pady=5)

        ttk.Label(
            loss_frame,
            text="止損設置:",
            style='FieldLabel.TLabel'
        ).pack(side="left")

        self.stop_loss = ttk.Entry(loss_frame, width=8)
        self.stop_loss.pack(side="left", padx=5)
        self.stop_loss.insert(0, "2.0")

        ttk.Label(
            loss_frame,
            text="%",
            style='FieldLabel.TLabel'
        ).pack(side="left")

    def create_trading_chart(self, parent):
        """創建交易統計圖表區域"""
        chart_frame = ttk.LabelFrame(
            parent,
            text="交易統計",
            style='Card.TLabelframe'
        )
        chart_frame.pack(fill="x", padx=10, pady=5)

    def create_notification_section(self, parent):
        """創建通知設置區域"""
        notification_frame = ttk.LabelFrame(
            parent,
            text="通知設置",
            style='Card.TLabelframe'
        )
        notification_frame.pack(fill="x", padx=10, pady=5)

        self.notify_profit = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            notification_frame,
            text="盈利通知",
            variable=self.notify_profit
        ).pack(anchor="w", pady=2)

        self.notify_loss = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            notification_frame,
            text="虧損通知",
            variable=self.notify_loss
        ).pack(anchor="w", pady=2)

    def create_control_buttons(self, parent):
        """創建控制按鈕區域"""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill="x", padx=10, pady=5)

        # 開始交易按鈕
        self.start_button = ttk.Button(
            button_frame,
            text="開始交易",
            style='Success.TButton',
            command=self.start_trading
        )
        self.start_button.pack(side="left", padx=5)

        # 停止交易按鈕
        self.stop_button = ttk.Button(
            button_frame,
            text="停止交易",
            style='Error.TButton',
            command=self.stop_trading,
            state='disabled'  # 初始時禁用
        )
        self.stop_button.pack(side="left", padx=5)

        # 保存設置按鈕
        self.save_button = ttk.Button(
            button_frame,
            text="保存設置",
            style='Primary.TButton',
            command=self.save_settings
        )
        self.save_button.pack(side="right", padx=5)

    def update_price_display(self, pair):
        """更新價格顯示"""
        try:
            if not self.trading_bot:
                return

            current_price = self.trading_bot.get_current_price(pair)
            self.price_label.configure(
                text=f"{pair.split('_')[0]}: ${current_price:,.2f}")

        except Exception as e:
            logging.error(f"更新價格顯示失敗: {str(e)}")
            self.add_log(f"更新價格顯示失敗: {str(e)}", "error")

    def toggle_secret_display(self):
        """切換API密碼的顯示/隱藏狀態"""
        try:
            current_text = self.api_secret_entry.get()
            if current_text and current_text != "請輸入您的 API Secret":
                if self.show_secret_var.get():
                    self.api_secret_entry.configure(show="")
                else:
                    self.api_secret_entry.configure(show="*")
        except Exception as e:
            logging.error(f"切換密碼顯示狀態時發生錯誤: {str(e)}")

    def clear_log(self):
        """清除交易日誌"""
        try:
            # 清除日誌內容
            self.status_text.delete(1.0, tk.END)

            # 添加清除記錄
            self.add_log("日誌已清除", "system")

        except Exception as e:
            logging.error(f"清除日誌時發生錯誤: {str(e)}")
            self.add_log(f"清除日誌失敗: {str(e)}", "error")
