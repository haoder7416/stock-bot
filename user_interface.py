import tkinter as tk
from tkinter import ttk, messagebox, font
import json
from PIL import Image, ImageTk
from datetime import datetime


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
        self.window.grid_columnconfigure(1, weight=1)
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

        self.create_api_section(left_panel)
        self.create_investment_section(left_panel)
        self.create_risk_section(left_panel)
        self.create_popular_pairs_section(left_panel)

        # 右側面板 (交易和監控)
        right_panel = self.create_panel("交易", 1)
        right_panel.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)
        right_panel.grid_columnconfigure(0, weight=1)

        self.create_strategy_section(right_panel)
        self.create_account_status_section(right_panel)
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
                except FileNotFoundError:
                    pass

                # 保存新設置
                with open('user_settings.json', 'w') as f:
                    json.dump(settings, f, indent=4)

                # 記錄變更到日誌
                self.update_status("設置已保存，更新內容：")

                # 比較並記錄變更
                for key, new_value in settings.items():
                    old_value = old_settings.get(key)
                    if old_value != new_value:
                        if key in ['api_key', 'api_secret']:
                            # 敏感資訊不顯示具體內容
                            self.update_status(f"- {key}: 已更新")
                        else:
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
            investment_amount = self.investment_amount.get().strip()
            leverage = float(self.leverage.get())  # 直接轉換為浮點數

            # 驗證投資金額
            if not investment_amount:
                raise ValueError("請輸入投資金額")
            investment_amount = float(investment_amount)

            # 驗證槓桿倍數
            if not 1 <= leverage <= 20:
                raise ValueError("槓桿倍數必須在 1-20 倍之間")

            return {
                'api_key': self.api_key.get(),
                'api_secret': self.api_secret.get(),
                'investment_amount': investment_amount,
                'leverage': int(leverage),  # 轉換為整數
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

    def create_api_section(self, parent):
        """創建 API 設置區域"""
        api_frame = ttk.LabelFrame(
            parent,
            text="API 設置",
            style='Card.TLabelframe'
        )
        api_frame.pack(fill="x", padx=15, pady=10)

        # API Key 輸入框
        key_frame = ttk.Frame(api_frame)
        key_frame.pack(fill="x", pady=5)

        ttk.Label(
            key_frame,
            text="API Key",
            style='FieldLabel.TLabel'
        ).pack(anchor="w")

        self.api_key = ttk.Entry(
            key_frame,
            style='Input.TEntry',
            width=40
        )
        self.api_key.pack(fill="x", pady=(5, 0))
        self.api_key.insert(0, "請輸入您的 API Key")
        self.api_key.bind(
            '<FocusIn>', lambda e: self.on_entry_focus_in(e, "請輸入您的 API Key"))
        self.api_key.bind(
            '<FocusOut>', lambda e: self.on_entry_focus_out(e, "請輸入您的 API Key"))
        self.api_key.bind('<KeyRelease>', self.on_api_input_change)

        # API Secret 輸入框
        secret_frame = ttk.Frame(api_frame)
        secret_frame.pack(fill="x", pady=10)

        ttk.Label(
            secret_frame,
            text="API Secret",
            style='FieldLabel.TLabel'
        ).pack(anchor="w")

        self.api_secret = ttk.Entry(
            secret_frame,
            style='Input.TEntry',
            width=40,
            show="•"
        )
        self.api_secret.pack(fill="x", pady=(5, 0))
        self.api_secret.bind('<KeyRelease>', self.on_api_input_change)

        # 顯示/隱藏密碼按鈕
        show_secret_frame = ttk.Frame(secret_frame)
        show_secret_frame.pack(fill="x", pady=(5, 0))

        self.show_secret = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            show_secret_frame,
            text="顯示",
            variable=self.show_secret,
            command=self.toggle_secret_visibility,
            style='Small.TCheckbutton'
        ).pack(side="left")

        # API 連線狀態指示
        self.api_status_label = ttk.Label(
            show_secret_frame,
            text="⚪ 未連接",  # 使用圓形指示燈
            style='StatusError.TLabel'
        )
        self.api_status_label.pack(side="right")

        # 添加連線按鈕
        button_frame = ttk.Frame(api_frame)
        button_frame.pack(fill="x", pady=(10, 0))

        self.connect_button = ttk.Button(
            button_frame,
            text="連線交易所",
            style='Primary.TButton',
            command=self.test_api_connection
        )
        self.connect_button.pack(side="right", padx=5)

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
            to=0,  # 初始設為0，等待總資產更新後再設定
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
        self.leverage_buttons = ttk.Frame(inv_frame)  # 保存為類的屬性
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
        headers = ["排名", "交易對", "24h交易量", "價格", "漲跌幅"]
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
        for i, (pair_data, row) in enumerate(zip(pairs_data, self.pair_rows)):
            # 更新排名
            row[0].configure(text=f"#{i+1}")
            # 更新交易對
            row[1].configure(text=pair_data['symbol'])
            # 更新交易量
            volume = pair_data['volume']
            volume_text = f"{
                volume/1000000:.1f}M" if volume > 1000000 else f"{volume/1000:.1f}K"
            row[2].configure(text=f"{volume_text} USDT")
            # 更新價格
            row[3].configure(text=f"${pair_data['price']:.4f}")
            # 更新漲跌幅
            change = pair_data['price_change']
            color = 'Success' if change >= 0 else 'Error'
            row[4].configure(
                text=f"{'+' if change >= 0 else ''}{change:.2f}%",
                style=f'Value{color}.TLabel'
            )

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
        self.status_text.tag_remove("hidden", "1.0", tk.END)

        if filter_type != "全部":
            # 隱藏不符合過濾條件的行
            start = "1.0"
            while True:
                # 找到下一個標籤位置
                tag_range = self.status_text.tag_nextrange(
                    filter_type.lower(), start)
                if not tag_range:
                    break
                # 隱藏這一行
                line_start = self.status_text.index(
                    f"{tag_range[0]} linestart")
                line_end = self.status_text.index(
                    f"{tag_range[0]} lineend + 1c")
                self.status_text.tag_add("hidden", line_start, line_end)
                start = line_end

    def add_log(self, message, log_type="system"):
        """添加日誌訊息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"

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
