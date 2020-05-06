from Tempo import Tempo

import time
import rtmidi

midiout = rtmidi.MidiOut()
available_ports = midiout.get_ports()
print(available_ports)
if available_ports:
    midiout.open_port(0)
else:
    midiout.open_virtual_port("My virtual output")


class Sequencer:
    on = []
    velocity = 50
    noteOn = 144
    noteOff = 128

    steps = 16
    notes = 16
    scales = ['minor']
    minor = list(range(40, 70))
    minor.reverse()
    # major = [60,62,64, 66]
    t = None
    currentStep = 0

    noteTable = []

    def __init__(self, tempo):
        self.t = Tempo(tempo)
        self.currentStep = 0

    def getCurrentStep(self):
        return self.currentStep

    def updateSequence(self):
        if self.t.gate():
            t = self.noteTable
            for setoffNote in self.on:
                midiout.send_message(setoffNote)
            self.on=[]
            for i in t:
                step, note = i
                note = int(note)


                print(step)
                if step == self.currentStep:
                    # print("s!!!")
                    # print([self.noteOn, self.minor[int(note)], self.velocity])

                    midiout.send_message([self.noteOn, self.minor[note], self.velocity])
                    self.on.append([self.noteOff, self.minor[note], self.velocity])

            if self.currentStep + 1 < self.steps:
                self.currentStep += 1
            else:
                self.currentStep = 0

            self.t.trigger()

    def setSteps(self, steps):
        self.steps = steps

    def setNotes(self, notes):
        self.notes = notes

    def setTempo(self, tempo):
        self.currentStep = 0
        self.t.setTempo(tempo)

    def setSequenceTable(self, lst):
        self.noteTable = lst
        pass

        # print(t.getSeconds())
        # print(t.getBarLength())
        # print(t.getphaseLength())
        # print(t.getCurrentTime()())
        # print(t.trigger())

        # while True:
