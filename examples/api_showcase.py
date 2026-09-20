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
        raw = deck.value('y1')
        axis = deck.axis('y1')
        slider = deck.slider('x1')
        pressed = deck.button('b1')
        up = deck.dpad('u1')
        right = deck.dpad('r1')
        down = deck.dpad('d1')
        left = deck.dpad('l1')

        deck.send('live', 1 if live else 0)
        deck.send('y1', axis)
        deck.send('x1', slider)
        deck.send('b1', 1 if pressed else 0)
        deck.send('pad', '{0}{1}{2}{3}'.format(
            'U' if up else '-',
            'R' if right else '-',
            'D' if down else '-',
            'L' if left else '-',
        ))
        deck.send('raw', raw)
        deck.send('bat', hub.battery.voltage())

        wait(5)
finally:
    deck.close()
