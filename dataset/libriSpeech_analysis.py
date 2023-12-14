import torch
from pprint import pprint
import os 

libri_speech_path = "dataset/datasets/LibriSpeech/test-clean"

SAMPLING_RATE = 16000

torch.set_num_threads(1)
model, utils = torch.hub.load(repo_or_dir='snakers4/silero-vad',
                              model='silero_vad',
                              force_reload=False,
                              trust_repo=True)

(get_speech_timestamps,
 save_audio,
 read_audio,
 VADIterator,
 collect_chunks) = utils

#get all the utterances
utterances = []
speakers = os.scandir(libri_speech_path)
for speaker in speakers:
    if speaker.is_file():
        continue
    chapters = os.scandir(speaker)
    for chapter in chapters:
        if chapter.is_file():
            continue
        audio_files = os.scandir(chapter)
        for audio_file in audio_files:
            if ".flac" in audio_file.path:
                utterances.append(audio_file.path)

inter_speech_intervals = []

for utterance in utterances:
    wav = read_audio(utterance, sampling_rate=SAMPLING_RATE)
    # get speech timestamps from full audio file
    speech_timestamps = get_speech_timestamps(wav, model, sampling_rate=SAMPLING_RATE, min_silence_duration_ms=1, window_size_samples=512)
    if(len(speech_timestamps) > 1):
        for i, speech_chunk in enumerate(speech_timestamps):
            if i == len(speech_timestamps) - 1:
                break
            interval_samples = speech_timestamps[i+1]['start'] - speech_timestamps[i]['end']
            interval_ms = interval_samples / SAMPLING_RATE
            if interval_ms == 0:
                print('zero')
            print(interval_ms)
            inter_speech_intervals.append(interval_ms)

mean_inter_speech_interval = sum(inter_speech_intervals) / len(inter_speech_intervals)
print(f'The mean inter speech interval is: {mean_inter_speech_interval}')