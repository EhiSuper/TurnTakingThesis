import json
from os import error
import torch
import numpy as np
from av import AudioResampler, AudioFifo
from enum import Enum
from websockets.sync.client import connect

class State(Enum):
    NOT_STARTED = 0
    STARTED = 1
    POTENTIAL_TURN_CHANGE = 2
    CONVERSATION_NOT_STARTED = 3

class Analyzer:
    
    def __init__(self):
        self.state = State.NOT_STARTED
        self.cumulative_silence = 0.0
        torch.set_num_threads(1)
        self.vad_model, utils = torch.hub.load(repo_or_dir='snakers4/silero-vad',
                                      model='silero_vad',
                                      force_reload=False,
                                      trust_repo=True)
        
        with open("configuration.json", "r") as configuration:
            self.parameters = json.load(configuration)

        self.websocket = connect(self.parameters["uri"])
        self.resampler = AudioResampler(format='s16', layout='mono', rate=self.parameters["sampling_rate"])
        self.audio_fifo = AudioFifo()
    
    def int2float(self, sound):
        abs_max = np.abs(sound).max()
        sound = sound.astype('float32')
        if abs_max > 0:
            sound *= 1 / 32768
            sound = sound.squeeze()  # depends on the use case
        return sound
    
    def analyze(self, frame):
        frame = self.resampler.resample(frame)[0]
        self.audio_fifo.write(frame)
        frame = self.audio_fifo.read(800, False)
        if frame is not None:
            # get the confidences
            tensor = torch.from_numpy(self.int2float(frame.to_ndarray()))
            new_confidence = self.vad_model(tensor, self.parameters["sampling_rate"]).item()
            self.set_state(new_confidence)
    
    def set_state(self, speaking_probability):
        # check if the new frame has voice
            if speaking_probability <= self.parameters["confidence_threshold"]:
                self.cumulative_silence += self.parameters["frame_duration"]
                if self.state == State.STARTED and self.cumulative_silence >= self.parameters["silence_threshold"]:
                    self.state = State.POTENTIAL_TURN_CHANGE
                    print("Potential turn change")
                    try:
                        self.websocket.send("Potential turn change")
                    except error:
                        print(error.errno)
                    # queue.put("Potential turn change")
                    

                elif self.state == State.POTENTIAL_TURN_CHANGE and self.cumulative_silence >= self.parameters["confirmed_silence_threshold"]:
                    self.state = State.NOT_STARTED  # we need to go back to the NOT_STARTED state to initiate a new turn
                    print("Turn change confirmed")
                    print(" ")
                    try:
                        self.websocket.send("Turn change confirmed")
                    except error:
                        print(error.errno)
                    # queue.put("Turn change confirmed")
                    

                # if for more than CONVERSATION_NOT_STARTED_THRESHOLD there is silence
                # the user may have not understood the response and we should repeat it
                elif self.state == State.NOT_STARTED and (self.cumulative_silence >= self.parameters["conversation_not_started_threshold"]):
                    self.state = State.CONVERSATION_NOT_STARTED
                    print("Conversation not started")
                    print(" ")
                    try:
                        self.websocket.send("Conversation not started")
                    except error:
                        print(error.errno)
                    # queue.put("Conversation not started")

                # if the user stay silent for more than START_CONVERSATION_THRESHOLD
                # the robot may want to start the conversation
                elif self.state == State.CONVERSATION_NOT_STARTED and self.cumulative_silence >= self.parameters["start_conversation_threshold"]:
                    self.cumulative_silence = 0
                    self.state = State.NOT_STARTED
                    print("Start conversation")
                    print(" ")
                    try:
                        self.websocket.send("Start conversation")
                    except error:
                        print(error.errno)
                    # queue.put("Start conversation")

            else:
                self.cumulative_silence = 0
                if self.state == State.NOT_STARTED or self.state == State.CONVERSATION_NOT_STARTED:
                    self.state = State.STARTED
                    print("Conversation started")
                    try:
                        self.websocket.send("Conversation started")
                    except error:
                        print(error.errno)
                    # queue.put("Conversation started")

                elif self.state == State.POTENTIAL_TURN_CHANGE:
                    # if it was detected a potential turn change we need to send a message to
                    # interrupt the pipeline
                    self.state = State.STARTED
                    print("Potential turn change aborted")
                    try:
                        self.websocket.send("Potential turn change aborted")
                    except error:
                        print(error.errno)
                    # queue.put("Potential turn change aborted")


    


