import datetime
from enum import Enum

import av
import numpy as np
import torch
from av import AudioResampler, AudioFifo

torch.set_num_threads(1)

vad_model, utils = torch.hub.load(repo_or_dir='snakers4/silero-vad',
                                  model='silero_vad',
                                  force_reload=False,
                                  trust_repo=True)

(get_speech_timestamps,
 save_audio,
 read_audio,
 VADIterator,
 collect_chunks) = utils

resampler = AudioResampler(format='s16', layout='mono', rate=16000)
audio_fifo = AudioFifo()

# Detection parameters
SILENCE_THRESHOLD = 0.5  # s
CONFIRMED_SILENCE_THRESHOLD = 2.0  # s
CONFIDENCE_THRESHOLD = 0.5  #
START_CONVERSATION_THRESHOLD = 10.0  # s
CONVERSATION_NOT_STARTED_THRESHOLD = 5.0  # s

FRAME_DURATION = 0.05  # s


class State(Enum):
    NOT_STARTED = 0
    STARTED = 1
    POTENTIAL_TURN_CHANGE = 2
    CONVERSATION_NOT_STARTED = 3


state = State.NOT_STARTED
cumulative_silence = 0.0

processed = datetime.datetime.now()
previous_processed = datetime.datetime.now()


def int2float(sound):
    abs_max = np.abs(sound).max()
    sound = sound.astype('float32')
    if abs_max > 0:
        sound *= 1 / 32768
    sound = sound.squeeze()  # depends on the use case
    return sound


def analyze(audio_queue, latencies_queue):
    while True:
        frame = audio_queue.get()
        frame = av.AudioFrame.from_ndarray(frame, format='s16', layout='stereo')
        frame.sample_rate = 16000
        frame = resampler.resample(frame)[0]
        audio_fifo.write(frame)
        frame = audio_fifo.read(800, False)
        if frame is not None:
            # get the confidences
            tensor = torch.from_numpy(int2float(frame.to_ndarray()))
            new_confidence = vad_model(tensor, 16000).item()
            end = datetime.datetime.now()
            start = latencies_queue.get()
            latency = end - start
            # print(f"Latency: {latency.total_seconds()} seconds")
            global processed
            global previous_processed
            processed = datetime.datetime.now()
            new_latency = processed - previous_processed
            print(f"Latency: {new_latency.total_seconds()} seconds")
            previous_processed = processed

            global state
            global cumulative_silence

            # check if the new frame has voice
            if new_confidence <= CONFIDENCE_THRESHOLD:
                cumulative_silence += FRAME_DURATION
                # print(cumulative_silence)
                if state == State.STARTED and cumulative_silence >= SILENCE_THRESHOLD:
                    state = State.POTENTIAL_TURN_CHANGE
                    print("Potential turn change")
                    # queue.put("Potential turn change")

                elif state == State.POTENTIAL_TURN_CHANGE and cumulative_silence >= CONFIRMED_SILENCE_THRESHOLD:
                    state = State.NOT_STARTED  # we need to go back to the NOT_STARTED state to initiate a new turn
                    print("Turn change confirmed")
                    print(" ")
                    # queue.put("Turn change confirmed")

                # if for more than CONVERSATION_NOT_STARTED_THRESHOLD there is silence
                # the user may have not understood the response and we should repeat it
                elif state == State.NOT_STARTED and (cumulative_silence >= CONVERSATION_NOT_STARTED_THRESHOLD):
                    state = State.CONVERSATION_NOT_STARTED
                    print("Conversation not started")
                    print(" ")
                    #  queue.put("Conversation not started")

                # if the user stay silent for more than START_CONVERSATION_THRESHOLD
                # the robot may want to start the conversation
                elif state == State.CONVERSATION_NOT_STARTED and cumulative_silence >= START_CONVERSATION_THRESHOLD:
                    cumulative_silence = 0
                    state = state.NOT_STARTED
                    print("Start conversation")
                    print(" ")
                    # queue.put("Start conversation")

            else:
                cumulative_silence = 0
                if state == State.NOT_STARTED or state == State.CONVERSATION_NOT_STARTED:
                    state = State.STARTED
                    print("Conversation started")
                    # queue.put("Conversation started")

                elif state == State.POTENTIAL_TURN_CHANGE:
                    # if it was detected a potential turn change we need to send a message to
                    # interrupt the pipeline
                    state = State.STARTED
                    print("Potential turn change aborted")
                    # queue.put("Potential turn change aborted")
