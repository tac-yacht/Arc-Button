#必須
import network
import ntptime
import time
import wireguard
import asyncio,_thread

from virtual_iot_button_sender import send_button,ClickType
from button_event import ButtonHander

#状態表示など任意
import machine
import neopixel

import requests

def statusLED(r, g, b):
    statusLED = neopixel.NeoPixel(machine.Pin(2), 1)
    statusLED[0] = (r, g, b)
    statusLED.write()

def readlines(file):
    with open(file) as f:
        return f.read().splitlines()

def metadata():
    res = None
    try:
        res = requests.get("http://metadata.soracom.io/v1/subscriber")
        print(res.status_code)
        print(res.text)
    finally:
        if res is not None:
            res.close()

led_flag = False
def send(type:ClickType):
    global led_flag
    print(f'click type: {type.value}')
    send_button(click_type=type)
    if led_flag:
        statusLED(0, 2, 0)
        led_flag = False
    else:
        statusLED(0, 0, 2)
        led_flag = True

statusLED(2, 0, 0)

# wifi接続
wifi_credential = readlines('wifi_credential.txt')
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(wifi_credential[0], wifi_credential[1])

while not wlan.isconnected():
    time.sleep(1)

ip = wlan.ifconfig()[0]
print(f'Connected on {ip}')

# 時間設定
ntptime.server = 'ntp.soracom.io'
ntptime.settime()
print(time.localtime())

statusLED(1, 1, 0)

# Arc接続
wg_c = readlines('wireguard_credential.txt')
wireguard.begin(local_ip=wg_c[0], private_key=wg_c[1], remote_peer_address=wg_c[2], remote_peer_public_key=wg_c[3], remote_peer_port=int(wg_c[4]))

# ボタンイベントと送信を紐付け
handler = ButtonHander(pin_number=9, single=lambda:send(ClickType.SINGLE), double=lambda:send(ClickType.DOUBLE), long=lambda:send(ClickType.LONG))
def background():
    asyncio.run(handler.start())
_thread.start_new_thread(background,())

statusLED(0, 0, 2)
