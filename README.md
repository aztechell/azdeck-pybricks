# AzDeck для Pybricks

Один файл `azdeck.py` — stdin/stdout протокол для программы на штатной прошивке Pybricks.
Приложение [AzDeck](https://github.com/aztechell/azdeck-Source-Code) подключается по BLE напрямую: ПК, мост и перепрошивка не нужны.

---

## Быстрый старт

1. Скопируйте в Pybricks Code `azdeck.py` и один пример из `examples/`.
2. Подправьте класс хаба и порты под свою модель (примеры рассчитаны на SPIKE Prime).
3. Загрузите программу на хаб и **отключите** Pybricks Code.
4. В AzDeck создайте профиль с транспортом **Pybricks**, выберите семью хаба и найдите устройство.
5. Нажмите **Подключить** — AzDeck запустит сохранённую программу по GATT.

Пока программа на хабе работает, хаб может не находиться в поиске. Перед повторным сканом остановите программу кнопкой хаба.

---

## Примеры

| Файл | Назначение |
| --- | --- |
| [`examples/api_showcase.py`](examples/api_showcase.py) | Все публичные методы `AzDeck` |
| [`examples/two_motors.py`](examples/two_motors.py) | Дифф-привод: `y1` / `x1` / `b1` |
| [`examples/prime_pixel_dpad.py`](examples/prime_pixel_dpad.py) | Пиксель на матрице 5×5 по D-Pad |
| [`examples/telemetry.py`](examples/telemetry.py) | Только телеметрия батареи |

Имена каналов в профиле AzDeck должны совпадать с именами в программе.
Короткие имена по умолчанию: кнопки `b1`…, D-Pad `u1`/`d1`/`l1`/`r1`, стик `x1`/`y1`, слайдер `sp1`.

---

## API `AzDeck`

```python
from azdeck import AzDeck

deck = AzDeck(
    timeout_ms=350,            # failsafe, если нет свежего control
    max_channels=32,           # максимум каналов в одном кадре
    max_telemetry=8,           # ключей телеметрии в очереди
    telemetry_interval_ms=100, # пауза между telemetry-строками
    rx_budget=256,             # байт stdin за один update()
    tx_budget=64,              # байт stdout за один update()
)
```

| Метод | Что делает |
| --- | --- |
| `deck.update()` | Читает stdin, пишет stdout. Вызывать каждые **5–10 мс**. |
| `deck.active()` | `True`, пока приходят валидные control-кадры (таймер `timeout_ms`). |
| `deck.value(name)` | Сырое число канала (по умолчанию `0`). |
| `deck.axis(name)` | То же, для осей джойстика. |
| `deck.slider(name)` | То же, для слайдеров. |
| `deck.button(name)` | `True`, если значение ≠ 0. |
| `deck.dpad(name)` | То же, для направлений D-Pad. |
| `deck.send(name, value)` | Очередь телеметрии: число или строка (не `bool`). |
| `deck.close()` | Failsafe и отписка от poll. Вызывать в `finally`. |

Библиотека **не** останавливает моторы сама — при `not deck.active()` делайте это в своей программе.

---

## Хабы и размер чанка

BLE profile ≥ **1.3**. Нужны `ujson` / `usys` / `uselect` в прошивке.

| Семья в AzDeck | Хабы | Stdin на 4.x |
| --- | --- | --- |
| Large | Prime, Inventor, Essential | ~63 байта |
| Small | City, Technic, Move | ~19 байт |

На 3.x лимит обычно выше (до ~160). Реальный размер пишет AzDeck после MTU / capabilities.

---

## Протокол (кратко)

- **Control** — JSON-объект без `type`, например `{"y1":0.5,"x1":0}`.
- **Ping** — `AZDECK_PING:…` → ответ `AZDECK_PONG:…` (таймер управления не продлевает).
- **Telemetry** — JSON с `"type":"telemetry"` и вашими ключами из `send()`.

Ограничения: строка stdin ≤ 1024 байт; пауза между фрагментами ≤ 400 мс; telemetry-строка ≤ 512 байт; имя канала ≤ 32 байт UTF-8; строковое значение ≤ 80 байт.

Пропущенный в кадре канал сохраняет прошлое значение до failsafe. Для кнопок и движения в профиле оставляйте `includeWhenZero=true`.

---

## Проверка на ПК

```bash
python -m unittest discover -s tests -v
```

При штатном disconnect AzDeck останавливает программу на хабе перед разрывом GATT, чтобы хаб снова появился в поиске.
