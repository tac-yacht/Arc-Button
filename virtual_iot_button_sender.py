import struct
from socket import socket, AF_INET, SOCK_DGRAM

class ValueType:
    def __init__(self, value):
        self.value = value

    def __eq__(self, other):
        return type(self) == type(other) and self.value == other.value

    def __hash__(self):
        return hash((type(self), self.value))

    def __repr__(self):
        return f"{self.__class__.__name__}({self.value})"
    
class ClickType(ValueType):
    @staticmethod
    def from_int(value:int):
        for ct in (ClickType.SINGLE, ClickType.DOUBLE, ClickType.LONG):
            if ct.value == value:
                return ct
        raise ValueError("invalid value. SINGLE, DOUBLE, LONG only")

ClickType.SINGLE = ClickType(1)
ClickType.DOUBLE = ClickType(2)
ClickType.LONG = ClickType(3)

class BatteryLevel(ValueType):
    def __init__(self, value):
        if not (0 <= value <= 3):
            raise ValueError(f"invalid value for BatteryLevel: {value}. Must be 0, 1, 2, or 3 (representing 1/4～4/4).")
        super().__init__(value)

    @staticmethod
    def n_of_4(value:int):
        return BatteryLevel(value-1) #binary is 0-3

def serialize_button_data(click_type: ClickType|int, battery_level:BatteryLevel|int):
    fixed_byte = 0x4d

    if isinstance(click_type, int):
        click_type = ClickType.from_int(click_type)
    elif not isinstance(click_type, ClickType):
        raise TypeError("click_type must be ClickType or int")

    if isinstance(battery_level, int):
        battery_level = BatteryLevel.n_of_4(battery_level)
    elif not isinstance(battery_level, BatteryLevel):
        raise TypeError("battery_level must be BatteryLevel or int")

    click_type_raw_value = click_type.value
    battery_level_raw_value = battery_level.value

    checksum = (fixed_byte + click_type_raw_value + battery_level_raw_value) & 0xFF

    binary = struct.pack('BBBB', fixed_byte, click_type_raw_value, battery_level_raw_value, checksum)
    return binary

def send_button(click_type: ClickType|int, battery_level: BatteryLevel|int = BatteryLevel.n_of_4(4)):
    data = serialize_button_data(click_type, battery_level)
    sock = socket(AF_INET, SOCK_DGRAM) #UDP
    
    try:
        sock.connect(('uni.soracom.io', 23080))
        sock.send(data)
    finally:
        sock.close()
