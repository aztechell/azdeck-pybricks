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
        if not deck.active() or deck.button('b1'):
            left.stop()
            right.stop()
        else:
            throttle = deck.axis('y1')
            turn = deck.axis('x1')
            left.dc(max(-100, min(100, (throttle + turn) * 100)))
            right.dc(max(-100, min(100, (throttle - turn) * 100)))
        wait(5)
finally:
    left.stop()
    right.stop()
    deck.close()
