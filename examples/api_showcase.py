from pybricks.hubs import PrimeHub
from pybricks.tools import wait
from azdeck import AzDeck

hub = PrimeHub()
deck = AzDeck(
    timeout_ms=350,
    max_channels=32,
    max_telemetry=8,
    telemetry_interval_ms=100,
    rx_budget=256,
    tx_budget=64,
)

print('AZDECK_API_READY')

try:
    while True:
        deck.update()

        live = deck.active()
        raw = deck.value('throttle')
        axis = deck.axis('throttle')
        slider = deck.slider('turn')
        pressed = deck.button('stop')
        up = deck.dpad('up')
        right = deck.dpad('right')
        down = deck.dpad('down')
        left = deck.dpad('left')

        deck.send('live', 1 if live else 0)
        deck.send('throttle', axis)
        deck.send('turn', slider)
        deck.send('stop', 1 if pressed else 0)
        deck.send('pad', '{0}{1}{2}{3}'.format(
            'U' if up else '-',
            'R' if right else '-',
            'D' if down else '-',
            'L' if left else '-',
        ))
        deck.send('raw', raw)
        deck.send('battery_mv', hub.battery.voltage())

        wait(5)
finally:
    deck.close()
