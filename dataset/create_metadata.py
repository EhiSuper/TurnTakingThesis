import os
import random
import librosa
import numpy as np
import json

N_SESSIONS = 10
SAMPLE_RATE = 16000
SESSION_DURATION = 180  # s
SESSION_SAMPLES = SESSION_DURATION * SAMPLE_RATE
SEED = 0
MIN_SILENCE = 1.0
MAX_SILENCE = 3.0
snr_levels = [25, 20, 15, 10, 5, 0, -5, -10, -15, -20]
libri_speech_path = "datasets/LibriSpeech"
noise_path = "datasets/DEMAND"

class Session:

    session_counter = 0

    def __init__(self, utterances, speech, noise=None, snr=0) -> None:
        self.id = Session.session_counter
        Session.session_counter += 1
        self.utterances = utterances
        self.speech = speech
        self.noise = noise
        self.snr = 0


    def __json__(self):
        return {
            'id': self.id,
            'utterances': self.utterances,
            'speech': self.speech,
            'noise': self.noise,
            'snr' : self.snr
        }

def get_speakers_ids(file):
    male_speakers = []
    female_speakers = []

    with open(file, "r") as file:
        # Skip the header lines
        for _ in range(12):
            next(file)

        # Process data lines
        for line in file:
            data = line.strip().split("|")
            speaker_id = data[0].strip()
            gender = data[1].strip()
            subset = data[2].strip()

            if subset == "test-clean":
                if gender == "M":
                    male_speakers.append(speaker_id)
                elif gender == "F":
                    female_speakers.append(speaker_id)

    return male_speakers, female_speakers


def get_utterances(libri_speech_path):
    # get all the utterances
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
    
    return utterances


def separate_utterances_by_gender(utterances, male_speakers, female_speakers):
    male_utterances = []
    female_utterances = []

    for i, utterance in enumerate(utterances):
        file = utterance.split('/')
        file_name = file[-1]
        speaker_id = file_name.strip().split('-')[0]
        if speaker_id in male_speakers:
            male_utterances.append(utterance)
        else:
            female_utterances.append(utterance)

    return male_utterances, female_utterances


def create_clean_sessions(utterances):
    sessions = []
    used_utterances = []
    pick = None
    for i in range(N_SESSIONS):
        length = 0
        session_utterances = []
        speech = []

        while length < SESSION_DURATION:
            label = {}
            label['start'] = length
            while pick == None or pick in used_utterances:
                pick = random.randint(0, len(utterances) - 1)
            utterance_picked = utterances[pick]
            session_utterances.append(utterance_picked)
            duration = librosa.get_duration(filename=utterance_picked)
            length += duration
            label['stop'] = length
            speech.append(label)
            used_utterances.append(pick)
            #adding silence
            silence_duration = random.uniform(MIN_SILENCE, MAX_SILENCE)
            length += silence_duration

        session = Session(session_utterances, speech)
        sessions.append(session)
    return sessions


def get_noises(noise_path):
    noises = []
    recordings = os.scandir(noise_path)
    for recording in recordings:
        if recording.is_file() or '48' in recording.name:
            continue
        enviroments = os.scandir(recording)
        for environment in enviroments:
            if environment.is_file():
                continue
            audio_files = os.scandir(environment)
            for audio_file in audio_files:
                if '01.wav' in audio_file.name:
                    noises.append(audio_file.path)

    return noises



def create_noisy_sessions(sessions, noises):
    picks = []
    pick = None
    noisy_sessions = []
    Session.session_counter = 0
    for i in range(3):       
        while pick == None or pick in picks:
            pick = random.randint(0, len(sessions) - 1)
        picks.append(pick)
        session = sessions[pick]
        for noise in noises:
            noisy_session = Session(session.utterances, session.speech, noise)
            noisy_sessions.append(noisy_session)
        
    return noisy_sessions    


if __name__ == "__main__":
    np.random.seed(SEED)
    random.seed(SEED)
    speakers_file_path = libri_speech_path + "/SPEAKERS.TXT"
    male_speakers, female_speakers = get_speakers_ids(speakers_file_path)
    utterances_path = libri_speech_path + "/test-clean"
    utterances = get_utterances(utterances_path)
    male_utterances, female_utterances = separate_utterances_by_gender(utterances, male_speakers, female_speakers)

    #clean sessions
    male_sessions = create_clean_sessions(male_utterances)
    female_sessions = create_clean_sessions(female_utterances)
    male_json = json.dumps(male_sessions, default=lambda obj: obj.__json__(), indent=2)
    female_json = json.dumps(female_sessions, default=lambda obj: obj.__json__(), indent=2)
    with open("male_clean.json", "w") as outfile:
        outfile.write(male_json)
    with open("female_clean.json", "w") as outfile:
        outfile.write(female_json)
    
    #noisy sessions
    noises = get_noises(noise_path)
    male_noisy_sessions = create_noisy_sessions(male_sessions, noises)
    female_noisy_sessions = create_noisy_sessions(female_sessions, noises)
    male_json = json.dumps(male_noisy_sessions, default=lambda obj: obj.__json__(), indent=2)
    female_json = json.dumps(female_noisy_sessions, default=lambda obj: obj.__json__(), indent=2)
    with open("male_noisy.json", "w") as outfile:
        outfile.write(male_json)
    with open("female_noisy.json", "w") as outfile:
        outfile.write(female_json)

    
    

