import json
from os import error
import time
import torch
import numpy as np
from av import AudioResampler, AudioFifo
from enum import Enum
from websockets.sync.client import connect
import socket

class Analyzer:
    """
    Analyzer class for the AudioFrames
    """

    class State(Enum):
        NOT_STARTED = 0
        STARTED = 1
        POTENTIAL_TURN_CHANGE = 2
        CONVERSATION_NOT_STARTED = 3

    def __init__(self):
        """
        Constructor of the analyzer. It loads the model from PyTorch Hub and load the parameters from the
        configuration.json file.
        """
        self.state = Analyzer.State.NOT_STARTED
        self.cumulative_silence = 0.0
        torch.set_num_threads(1)
        self.vad_model, utils = torch.hub.load(
            repo_or_dir="snakers4/silero-vad",
            model="silero_vad",
            force_reload=False,
            trust_repo=True,
        )

        with open("configuration.json", "r") as configuration:
            self.parameters = json.load(configuration)

        self.silence_threshold = self.parameters["silence_threshold"]
        self.confirmed_silence_threshold = self.parameters[
            "confirmed_silence_threshold"
        ]
        self.confidence_threshold = self.parameters["confidence_threshold"]
        self.start_conversation_threshold = self.parameters[
            "start_conversation_threshold"
        ]
        self.conversation_not_started_threshold = self.parameters[
            "conversation_not_started_threshold"
        ]
        self.sampling_rate = self.parameters["sampling_rate"]
        self.frame_duration = self.parameters["frame_duration"]
        self.websocket_port = self.parameters["websocket_port"]
        # host = socket.gethostbyname('host.docker.internal')
        # uri = f"ws://{host}:{self.websocket_port}"
        uri = "ws://localhost:8765"
        self.websocket = connect(uri)
        self.resampler = AudioResampler(
            format="s16", layout="mono", rate=self.sampling_rate
        )
        self.audio_fifo = AudioFifo()

        # latencies variables
        # end of turn detection latency
        self.end_of_turn_timestamp = 0
        self.end_of_turn_detection_latencies = []

        # inference latency
        self.inference_latencies = []

        #throughput
        self.old_end_analyze = 0
        self.analyze_gaps = []

    def int2float(self, sound):
        """
        Function to normalize between 0 and 1 an array of int values to float32 values.

        Args:
            sound (ndarray): Array to normalize
        Returns:
            ndarray: normalized between 0 and 1 array with float32 values
        """
        abs_max = np.abs(sound).max()
        sound = sound.astype("float32")
        if abs_max > 0:
            sound *= 1 / 32768
            sound = sound.squeeze()  # depends on the use case
        return sound

    def analyze(self, frame):
        """
        Function to analyze the input frame.

        Args:
            frame (AudioFrame): frame to analyze
        """
        frame = self.resampler.resample(frame)[0]  # resample the audio frame with the selected sampling_rate
        self.audio_fifo.write(frame)  # write the frame samples to the AudioFifo
        samples = (self.frame_duration * self.sampling_rate)  # computes to samples to read needed for the specified frame duration
        frame = self.audio_fifo.read(samples, False)  # reads the correct number of samples from the fifo
        # if there are enough sample to analyze the desired frame duration
        if frame is not None:
            # get the confidences
            tensor = torch.from_numpy(self.int2float(frame.to_ndarray()))
            start_inference = time.time()
            new_confidence = self.vad_model(tensor, self.sampling_rate).item()
            end_inference = time.time()
            inference_latency = end_inference - start_inference
            self.inference_latencies.append(inference_latency)
            
            # every 100 inferences the average inference latency is updated
            if(len(self.inference_latencies) % 200 == 0):
                average_inference_latency = sum(self.inference_latencies) / len(self.inference_latencies)
                #print(f'Average inference latency is {average_inference_latency} computed over {len(self.inference_latencies)} measurements')

            self.set_state(new_confidence)

            new_end_analyze = time.time()
            gap = new_end_analyze - self.old_end_analyze
            if self.old_end_analyze != 0:
                self.analyze_gaps.append(gap)
                # print(f'Analyze gap: {gap}')
            self.old_end_analyze = new_end_analyze
            if(len(self.analyze_gaps) > 0 and len(self.analyze_gaps) % 100 == 0):
                average_analyze_gap = sum(self.analyze_gaps) / len(self.analyze_gaps)
                # print(f'Average analyze gap: {average_analyze_gap}')


    def set_state(self, speaking_probability):
        """
        Function that handles the current status of the turn

        Args:
        speaking_probability (float): Probability detected that the input frame contains voice
        """
        # check if the new frame has voice
        if speaking_probability <= self.confidence_threshold:
            self.cumulative_silence += self.frame_duration
            # if there is silence for more than the specifiend threshold there could be a turn change
            if (
                self.state == Analyzer.State.STARTED
                and self.cumulative_silence >= self.silence_threshold
            ):
                self.state = Analyzer.State.POTENTIAL_TURN_CHANGE
                print("Potential turn change")
                try:
                    self.websocket.send("Potential turn change")
                except error:
                    print(error.errno)

            # if there is silence for more than the specified threshold there is an actual turn change
            elif (
                self.state == Analyzer.State.POTENTIAL_TURN_CHANGE
                and self.cumulative_silence >= self.confirmed_silence_threshold
            ):
                # we need to go back to the NOT_STARTED state to initiate a new turn
                self.state = Analyzer.State.NOT_STARTED
                print("Turn change confirmed")
                print(" ")
                
                end_of_turn_detected_timestamp = time.time() * 1000 # * 1000 because in Javascript the timestamp is in milliseconds while
                # in Python it is is seconds
                end_of_turn_detection_latency = end_of_turn_detected_timestamp - self.end_of_turn_timestamp

                # print(f'End of turn detection latency: {end_of_turn_detection_latency} meaurement {len(self.end_of_turn_detection_latencies)}')
                print('')
                self.end_of_turn_detection_latencies.append(end_of_turn_detection_latency)
                if(len(self.end_of_turn_detection_latencies) % 30 == 0):
                    average_end_of_turn_detection_latency = sum(self.end_of_turn_detection_latencies) / len(self.end_of_turn_detection_latencies)
                    # print(f'The average end of turn detection latency is {average_end_of_turn_detection_latency}')
                
                try:
                    self.websocket.send("Turn change confirmed")
                except error:
                    print(error.errno)

            # if for more than CONVERSATION_NOT_STARTED_THRESHOLD there is silence
            # the user may have not understood the response and we should repeat it
            elif self.state == Analyzer.State.NOT_STARTED and (
                self.cumulative_silence >= self.conversation_not_started_threshold
            ):
                self.state = Analyzer.State.CONVERSATION_NOT_STARTED
                print("Conversation not started")
                print(" ")
                try:
                    self.websocket.send("Conversation not started")
                except error:
                    print(error.errno)

            # if the user stay silent for more than START_CONVERSATION_THRESHOLD
            # the robot may want to start the conversation
            elif (
                self.state == Analyzer.State.CONVERSATION_NOT_STARTED
                and self.cumulative_silence >= self.start_conversation_threshold
            ):
                self.cumulative_silence = 0
                self.state = Analyzer.State.NOT_STARTED
                print("Start conversation")
                print(" ")
                try:
                    self.websocket.send("Start conversation")
                except error:
                    print(error.errno)

        # if in the frame there is voice
        else:
            self.cumulative_silence = 0
            if (
                self.state == Analyzer.State.NOT_STARTED
                or self.state == Analyzer.State.CONVERSATION_NOT_STARTED
            ):
                self.state = Analyzer.State.STARTED
                print("Conversation started")
                try:
                    self.websocket.send("Conversation started")
                except error:
                    print(error.errno)

            elif self.state == Analyzer.State.POTENTIAL_TURN_CHANGE:
                # if it was detected a potential turn change we need to send a message to
                # interrupt the pipeline
                self.state = Analyzer.State.STARTED
                print("Potential turn change aborted")
                try:
                    self.websocket.send("Potential turn change aborted")
                except error:
                    print(error.errno)
