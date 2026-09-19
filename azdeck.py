"""AzDeck stdin/stdout protocol for Pybricks 3.6+ hubs.

Copy this single file beside the hub program. Call update() frequently; the
program owns motors and must stop them when active() becomes false.
"""

try:
    import ujson as json
    if json.dumps({'probe': 1}) is None:
        import json
except ImportError:
    import json
try:
    import usys as sys
except ImportError:
    import sys
try:
    import uselect as select
except ImportError:
    import select
try:
    from pybricks.tools import StopWatch
except ImportError:
    # CPython tests have a monotonic clock but no Pybricks module.
    import time
    def _milliseconds():
        return int(time.monotonic() * 1000)
else:
    _watch = StopWatch()
    def _milliseconds():
        return _watch.time()


def _finite_number(value):
    return type(value) in (int, float) and value == value and value != float('inf') and value != -float('inf')


def _elapsed(now, then):
    return now - then


class AzDeck:
    def __init__(self, timeout_ms=350, *, stdin=None, stdout=None, clock=None,
                 max_channels=32, max_telemetry=8, telemetry_interval_ms=100,
                 rx_budget=256, tx_budget=64):
        if timeout_ms < 0 or max_channels < 1 or max_telemetry < 1 or rx_budget < 1 or tx_budget < 1:
            raise ValueError('AzDeck limits must be positive')
        self._input_stream = stdin if stdin is not None else sys.stdin
        self._input = stdin if stdin is not None else sys.stdin.buffer
        self._output = stdout if stdout is not None else sys.stdout.buffer
        self._clock = clock or _milliseconds
        self._timeout = timeout_ms or 350
        self._max_channels = min(max_channels, 32)
        self._max_telemetry = min(max_telemetry, 32)
        self._telemetry_interval = telemetry_interval_ms
        self._rx_budget = rx_budget
        self._tx_budget = tx_budget
        self._values = {}
        self._last_control = None
        self._buffer = bytearray()
        self._line_started = None
        self._last_input_byte = None
        self._discard = False
        self._pending_telemetry = {}
        self._pong = []
        self._tx = None
        self._tx_pos = 0
        self._tx_keys = None
        self._last_telemetry = None
        self._closed = False
        self._read_poll = select.poll()
        self._read_poll.register(self._input_stream, select.POLLIN)
        self._fragment_gap_ms = 400
        self._line_limit_ms = 2000

    def value(self, channel):
        return self._values.get(channel, 0)

    def axis(self, channel):
        return self.value(channel)

    def slider(self, channel):
        return self.value(channel)

    def button(self, channel):
        return self.value(channel) != 0

    def dpad(self, channel):
        return self.button(channel)

    def active(self):
        if self._last_control is None:
            return False
        if _elapsed(self._clock(), self._last_control) > self._timeout:
            self._failsafe()
            return False
        return True

    def send(self, channel, value):
        if self._closed or not isinstance(channel, str) or channel == 'type' or not channel or len(bytes(channel, 'utf-8')) > 32:
            return False
        if isinstance(value, str):
            if len(bytes(value, 'utf-8')) > 80:
                return False
        elif not _finite_number(value):
            return False
        if channel not in self._pending_telemetry and len(self._pending_telemetry) >= self._max_telemetry:
            return False
        self._pending_telemetry[channel] = value
        return True

    def update(self):
        if self._closed:
            return
        now = self._clock()
        self.active()
        if self._line_started is not None and (
                _elapsed(now, self._last_input_byte) > self._fragment_gap_ms or
                _elapsed(now, self._line_started) > self._line_limit_ms):
            self._failsafe()
            self._buffer = bytearray()
            self._line_started = None
            self._last_input_byte = None
            self._discard = True
        frames = 0
        pending_control = None
        reject_control = False
        for _ in range(self._rx_budget):
            if not self._read_poll.poll(0):
                break
            try:
                data = self._input.read(1)
            except OSError:
                self._failsafe()
                break
            if not data:
                break
            byte = data[0] if isinstance(data, (bytes, bytearray)) else ord(data)
            if byte == 10:
                if not self._discard and self._buffer:
                    line = bytes(self._buffer)
                    if line.endswith(b'\r'):
                        line = line[:-1]
                    if line:
                        result = self._process(line)
                        if result is False:
                            pending_control = None
                            reject_control = True
                        elif result is not None and not reject_control:
                            pending_control = result
                        frames += 1
                self._buffer = bytearray()
                self._line_started = None
                self._last_input_byte = None
                self._discard = False
                if frames >= 4:
                    break
            elif not self._discard:
                if self._line_started is None:
                    self._line_started = now
                if len(self._buffer) >= 1024:
                    self._failsafe()
                    self._buffer = bytearray()
                    self._discard = True
                    self._line_started = None
                    self._last_input_byte = None
                else:
                    self._buffer.append(byte)
                    self._last_input_byte = now
        if pending_control is not None:
            for key, value in pending_control:
                if key in self._values or len(self._values) < self._max_channels:
                    self._values[key] = value
            self._last_control = self._clock()
        self.active()
        self._flush(now)

    def _process(self, line):
        """Validate one complete line.

        Returns a list of (key, value) for a valid control frame (apply later so
        the last control in one update() wins), False after failsafe, or None
        for ping / telemetry / empty.
        """
        try:
            message = str(line, 'utf-8')
        except UnicodeError:
            self._failsafe()
            return False
        if message.startswith('AZDECK_PING:'):
            if len(line) <= 128 and len(self._pong) < 4:
                self._pong.append(bytes('AZDECK_PONG:' + message[12:] + '\n', 'utf-8'))
            return None
        try:
            payload = json.loads(message)
        except (ValueError, TypeError):
            self._failsafe()
            return False
        if not isinstance(payload, dict):
            self._failsafe()
            return False
        if 'type' in payload or not payload:
            return None
        entries = []
        for key, value in payload.items():
            if not isinstance(key, str) or not _finite_number(value):
                self._failsafe()
                return False
            if len(bytes(key, 'utf-8')) <= 32 and len(entries) < self._max_channels:
                entries.append((key, value))
        return entries

    def _failsafe(self):
        for key in self._values:
            self._values[key] = 0
        self._last_control = None

    def _flush(self, now):
        budget = self._tx_budget
        while budget > 0:
            if self._tx is None:
                if self._pong:
                    self._tx = self._pong.pop(0)
                    self._tx_keys = None
                elif self._pending_telemetry and (self._last_telemetry is None or _elapsed(now, self._last_telemetry) >= self._telemetry_interval):
                    keys = []
                    data = {'type': 'telemetry'}
                    for key, value in list(self._pending_telemetry.items()):
                        trial = dict(data)
                        trial[key] = value
                        encoded = bytes(json.dumps(trial) + '\n', 'utf-8')
                        if len(encoded) > 512:
                            if not keys:
                                del self._pending_telemetry[key]
                            break
                        data = trial
                        keys.append(key)
                    if not keys:
                        return
                    self._tx = bytes(json.dumps(data) + '\n', 'utf-8')
                    self._tx_keys = [(key, self._pending_telemetry[key]) for key in keys]
                else:
                    return
                self._tx_pos = 0
            # Pybricks stdout.buffer.write() works without polling stdout.
            # Some firmware accepts POLLOUT registration but never reports
            # it ready, leaving PONG and telemetry queued forever.
            chunk = self._tx[self._tx_pos:self._tx_pos + min(budget, 20)]
            try:
                count = self._output.write(chunk)
            except OSError:
                self._tx = None
                self._tx_keys = None
                return
            if count is None or count <= 0:
                return
            self._tx_pos += count
            budget -= count
            if self._tx_pos >= len(self._tx):
                if self._tx_keys is not None:
                    for key, value in self._tx_keys:
                        if self._pending_telemetry.get(key) == value:
                            del self._pending_telemetry[key]
                    self._last_telemetry = now
                self._tx = None
                self._tx_keys = None

    def close(self):
        if self._closed:
            return
        self._closed = True
        self._failsafe()
        self._read_poll.unregister(self._input_stream)
        self._buffer = bytearray()
        self._pending_telemetry.clear()
        self._pong = []
        self._tx = None
