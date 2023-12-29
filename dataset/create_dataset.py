import json
from pydub import AudioSegment
from create_metadata import Session
import numpy as np
import wave
import array

SAMPLING_RATE = 16000

male_metadata_clean = "dataset/datasets/libri_demand/male_clean.json"
female_metadata_clean = "dataset/datasets/libri_demand/female_clean.json"
male_metadata_noisy = "dataset/datasets/libri_demand/male_noisy.json"
female_metadata_noisy = "dataset/datasets/libri_demand/female_noisy.json"
noisy_sessions_metadata = "dataset/datasets/libri_demand/noisy_sessions.json"

male_dataset_clean_output_path = "dataset/datasets/libri_demand/male_clean/"
female_dataset_clean_output_path = "dataset/datasets/libri_demand/female_clean/"
male_dataset_noisy_output_path = "dataset/datasets/libri_demand/male_noisy/"
female_dataset_noisy_output_path = "dataset/datasets/libri_demand/female_noisy/"
noisy_sessions_output_path_clean = "dataset/datasets/libri_demand/noisy_sessions/clean/"
noisy_sessions_output_path_noise = "dataset/datasets/libri_demand/noisy_sessions/noise/"

snr_levels = [20, 10, 0, -10, -20]

def create_clean_dataset(output_path, sessions):
    for session in sessions:
        output_file = output_path + "session_" + str(session.id) + ".wav"
        audio_session = AudioSegment.silent(0, SAMPLING_RATE)

        for j, utterance in enumerate(session.utterances):
            audio_session += AudioSegment.from_file(utterance, "flac")
            if j+1 != len(session.utterances):
                silence_duration = session.speech[j+1]['start'] - session.speech[j]['stop']
                silence_audio = AudioSegment.silent(duration=silence_duration * 1000, frame_rate=SAMPLING_RATE)
                audio_session += silence_audio
        
        audio_session.export(output_file, format="wav")
                 

def sessions_from_metadata(metadata):
    sessions = []
    Session.session_counter = 0
    for i, element in enumerate(metadata):
        session = Session(element['utterances'], element['speech'], element['noise'], element['snr'], element['clean_session'])
        sessions.append(session)
    return sessions


def join_audio(clean, noise, output, snr=0):
    clean_wav = wave.open(clean, "r")
    noise_wav = wave.open(noise, "r")

    clean_amp = cal_amp(clean_wav)
    noise_amp = cal_amp(noise_wav)

    if len(clean_amp) > len(noise_amp):
        clean_amp = clean_amp[:len(noise_amp)]
    else:
        noise_amp = noise_amp[:len(clean_amp)]

    
    clean_rms = cal_rms(clean_amp)
    noise_rms = cal_rms(noise_amp)

    adjusted_noise_rms = cal_adjusted_rms(clean_rms, snr)

    adjusted_noise_amp = noise_amp * (adjusted_noise_rms / noise_rms) 
    mixed_amp = (clean_amp + adjusted_noise_amp)

    #Avoid clipping noise
    max_int16 = np.iinfo(np.int16).max
    min_int16 = np.iinfo(np.int16).min
    if mixed_amp.max(axis=0) > max_int16 or mixed_amp.min(axis=0) < min_int16:
        if mixed_amp.max(axis=0) >= abs(mixed_amp.min(axis=0)): 
            reduction_rate = max_int16 / mixed_amp.max(axis=0)
        else :
            reduction_rate = min_int16 / mixed_amp.min(axis=0)
        mixed_amp = mixed_amp * (reduction_rate)
        clean_amp = clean_amp * (reduction_rate)
    
    save_waveform(output, clean_wav.getparams(), mixed_amp)

def save_waveform(output_path, params, amp):
    output_file = wave.Wave_write(output_path)
    output_file.setparams(params) #nchannels, sampwidth, framerate, nframes, comptype, compname
    output_file.writeframes(array.array('h', amp.astype(np.int16)).tobytes() )
    output_file.close()

def cal_adjusted_rms(clean_rms, snr):
    a = float(snr) / 20
    noise_rms = clean_rms / (10**a) 
    return noise_rms

def cal_amp(wf):
    buffer = wf.readframes(wf.getnframes())
    # The dtype depends on the value of pulse-code modulation. The int16 is set for 16-bit PCM.
    amptitude = (np.frombuffer(buffer, dtype="int16")).astype(np.float64)
    return amptitude

def cal_rms(amp):
    return np.sqrt(np.mean(np.square(amp), axis=-1))


def create_noisy_dataset(input_path, output_path, sessions):
    for session in sessions:
        clean_session_path =  input_path + "session_" + str(session.clean_session) + ".wav"
        output_file = output_path + "session_" + str(session.id) + ".wav"
        join_audio(clean_session_path, session.noise, output_file, session.snr)   
  

if __name__ == '__main__':
    with open(male_metadata_clean, "r") as input:
        metadata = json.load(input)
    sessions = sessions_from_metadata(metadata)
    create_clean_dataset(male_dataset_clean_output_path, sessions)
    print("Male clean done")
    with open(female_metadata_clean, "r") as input:
        metadata = json.load(input)
    sessions = sessions_from_metadata(metadata)
    create_clean_dataset(female_dataset_clean_output_path, sessions)
    print("Female clean done")

    #noisy dataset
    with open(male_metadata_noisy, "r") as input:
        metadata = json.load(input)
    sessions = sessions_from_metadata(metadata)
    create_noisy_dataset(male_dataset_clean_output_path, male_dataset_noisy_output_path, sessions)
    print("Male noisy done")
    with open(female_metadata_noisy, "r") as input:
        metadata = json.load(input)
    sessions = sessions_from_metadata(metadata)
    create_noisy_dataset(female_dataset_clean_output_path, female_dataset_noisy_output_path, sessions)
    print("Female noisy done")

    #noisy dataset with different snr levels
    with open(noisy_sessions_metadata, "r") as input:
        metadata = json.load(input)
    sessions = sessions_from_metadata(metadata)
    create_clean_dataset(noisy_sessions_output_path_clean, [sessions[0]])
    create_noisy_dataset(noisy_sessions_output_path_clean, noisy_sessions_output_path_noise, sessions)
    print("Noisy sessions done")
    


