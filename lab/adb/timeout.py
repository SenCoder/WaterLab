import time


class Timeout(object):
    def __init__(self, duration):
        self.TIME = time.time
        self.duration = duration
        if duration is not None:
            self.deadline = self.TIME() + duration
        else:
            self.deadline = None

    def expired(self):
        return self.deadline is not None and self.time_left() <= 0

    def time_left(self):
        delta = self.deadline - self.TIME()
        if delta > self.duration:
            # clock jumped, recalculate
            self.deadline = self.TIME() + self.duration
            return self.duration
        else:
            return max(0, delta)