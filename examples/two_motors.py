from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor
from pybricks.parameters import Port
from pybricks.tools import wait
from azdeck import AzDeck

hub = PrimeHub()
left = Motor(Port.A)
right = Motor(Port.B)
deck = AzDeck()

try:
    while True:
        deck.update()
        if not deck.active() or deck.button('stop'):
            left.stop()
            right.stop()
        else:
            throttle = deck.axis('throttle')
            turn = deck.axis('turn')
            left.dc(max(-100, min(100, (throttle + turn) * 100)))
            right.dc(max(-100, min(100, (throttle - turn) * 100)))
        wait(5)
finally:
    left.stop()
    right.stop()
    deck.close()
