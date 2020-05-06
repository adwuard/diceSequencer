import time


class Tempo:
    tempo = 0
    duration = 0.25
    prev_time = 0
    # gateStatus = False

    def __init__(self, setTempo, duration=0.25):
        self.tempo = setTempo
        self.duration = duration

    def setTempo(self, BPM):
        self.tempo = BPM

    def setDuration(self, duration):
        self.duration = duration

    def getCurrentTime(self):
        current_milli_time = lambda: int(round(time.time() * 1000))
        return current_milli_time

    def getSeconds(self, duration=duration):
        return 1.0 / self.tempo * 60 * duration

    def getBarLength(self):
        return self.getSeconds(1)

    def getphaseLength(self):
        return self.getSeconds(4)

    def gate(self):
        # print(self.getCurrentTime()() - self.prev_time)
        if (self.getCurrentTime()() - self.prev_time) / 1000 > self.getSeconds():
            # print("Trigger!")
            return True
        else:
            return False

    def trigger(self):
        self.prev_time = self.getCurrentTime()()

    # def getGateState(self):
    #     return self.gateStatus


#
# if __name__ == '__main__':
#     t = Tempo(130)
#
#     print(t.getSeconds())
#     print(t.getBarLength())
#     print(t.getphaseLength())
#     print(t.getCurrentTime()())
#     print(t.trigger())
#
#     while True:
#         if t.gate():
#             t.trigger()
#         time.sleep(0.01)
#     pass
