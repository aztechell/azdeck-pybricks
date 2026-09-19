from pybricks.hubs import PrimeHub
from pybricks.tools import StopWatch, wait
from azdeck import AzDeck

hub = PrimeHub()
deck = AzDeck(timeout_ms=350)
clock = StopWatch()

x = 2
y = 2
direction = None
last_move = -400
repeat_ms = 400

hub.display.off()
hub.display.pixel(y, x)
print('AZDECK_PIXEL_READY')

try:
    while True:
        deck.update()

        pressed = None
        if deck.active():
            if deck.dpad('up'):
                pressed = 'up'
            elif deck.dpad('right'):
                pressed = 'right'
            elif deck.dpad('down'):
                pressed = 'down'
            elif deck.dpad('left'):
                pressed = 'left'

        now = clock.time()
        if pressed is None:
            direction = None
        elif pressed != direction or now - last_move >= repeat_ms:
            direction = pressed
            last_move = now
            new_x = x
            new_y = y
            if pressed == 'up':
                new_y = max(0, y - 1)
            elif pressed == 'right':
                new_x = min(4, x + 1)
            elif pressed == 'down':
                new_y = min(4, y + 1)
            else:
                new_x = max(0, x - 1)

            if new_x != x or new_y != y:
                hub.display.pixel(y, x, 0)
                x = new_x
                y = new_y
                hub.display.pixel(y, x)

        wait(5)
finally:
    deck.close()
    hub.display.off()
