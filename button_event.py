from machine import Pin, disable_irq, enable_irq
import time
import asyncio

class ButtonHander:
    DOUBLE_CLICK_TIMEOUT = 500  # ダブルクリックの最大間隔（ms）
    LONG_CLICK_THRESHOLD = 1200  # ロングクリックの最大間隔（ms）
    
    def __init__(self, pin_number=9, single=lambda:print("シングル"), double=lambda:print("ダブル"), long=lambda:print("ロング")):
        # ボタンを接続しているピン
        self.button = Pin(pin_number, Pin.IN, Pin.PULL_UP)

        # 状態変数
        self.button_pressed = False
        self.button_type = 0 # ボタン種別
        self.prev_end_ts = 0  # 前回の押下終了時間
        self.current_start_ts = 0 # 現在の押下開始時間

        self.single = single
        self.double = double
        self.long = long

        self.is_active = False

    # 割り込みハンドラ
    def irq_handler(self, pin):
        if pin.value() == 0:
            self.falling_handler()
        else:
            self.rising_handler()

    def falling_handler(self):
        self.current_start_ts = time.ticks_ms()
    
    def rising_handler(self):
        current_time = time.ticks_ms()
        
        # デバウンス（50ms）
        if time.ticks_diff(current_time, self.prev_end_ts) <= 50:
            return
        
        # ロングクリック判定　1回のクリックの間で判定できる（イベントとしては押しはじめと終わりの2回）
        if time.ticks_diff(current_time, self.current_start_ts) >= self.LONG_CLICK_THRESHOLD:
            self.button_type = 3
            self.button_pressed = True
        # ダブルクリック判定 前回の押下（離した）してから、今回の押しはじめが規定以下
        elif time.ticks_diff(self.current_start_ts, self.prev_end_ts) <= self.DOUBLE_CLICK_TIMEOUT:
            self.button_type = 2
            self.button_pressed = True
        # シングルクリック ダブルクリックの規定間隔以上ならシングルクリックである
        else:
            self.button_type = 1

        # 判定を終えてから前回タイムスタンプをセット prevをcurrentで上書きするので判定後である必要がある
        self.prev_end_ts = current_time

    async def start(self):
        # 割り込みを設定
        self.button.irq(trigger=Pin.IRQ_FALLING|Pin.IRQ_RISING, handler=self.irq_handler)

        self.is_active = True
        # メインループ
        while self.is_active:
            # クリティカルセクション：読み取り
            state = disable_irq()
            pressed = self.button_pressed
            type = self.button_type
            prev = self.prev_end_ts
            enable_irq(state)

            if pressed:
                # クリティカルセクション：リセット
                state = disable_irq()
                self.button_pressed = False 
                enable_irq(state)

                # ロングクリック
                if type==3:
                    self.long()
                # ダブルクリック
                elif type==2:
                    self.double()
            # シングルクリック判定 シングルはダブルクリックのタイムアウトの必要がある
            elif type==1 and time.ticks_diff(time.ticks_ms(), prev) > self.DOUBLE_CLICK_TIMEOUT:
                # クリティカルセクション：リセット
                state = disable_irq()
                self.button_type = 0 
                enable_irq(state)
                self.single()

            await asyncio.sleep_ms(10)  # CPU負荷軽減

    def end(self):
        self.is_active = False
        state = disable_irq()
        self.button.irq(handler=None)
        enable_irq(state)
