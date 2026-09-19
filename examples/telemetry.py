from pybricks.hubs import PrimeHub
from pybricks.tools import wait, StopWatch
from azdeck import AzDeck

hub = PrimeHub()
deck = AzDeck()
clock = StopWatch()
last_sample = -1000

try:
    while True:
        deck.update()
        now = clock.time()
        if now - last_sample >= 500:
            deck.send('battery_mv', hub.battery.voltage())
            deck.send('state', 'active' if deck.active() else 'idle')
            last_sample = now
        wait(5)
finally:
    deck.close()
