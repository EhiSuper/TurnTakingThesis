import argparse
from genericpath import isfile
import json
import os

class Session:

    session_counter = 0

    def __init__(self, utterances, speech, noise=None, snr=0, clean_session=None) -> None:
        self.id = Session.session_counter
        Session.session_counter += 1
        self.utterances = utterances
        self.speech = speech
        self.noise = noise
        self.snr = snr
        self.clean_session = clean_session


    def __json__(self):
        return {
            'id': self.id,
            'utterances': self.utterances,
            'speech': self.speech,
            'noise': self.noise,
            'snr' : self.snr,
            'clean_session': self.clean_session
        }


def sessions_from_metadata(metadata):
    sessions = []
    Session.session_counter = 0
    for i, element in enumerate(metadata):
        session = Session(element['utterances'], element['speech'], element['noise'], element['snr'], element['clean_session'])
        sessions.append(session)
    return sessions


def is_in_speech(i, speech):
    for speech_chunk in speech:
        start = int(speech_chunk['start'] * 1000)
        stop = int(speech_chunk['stop'] * 1000)
        if i >= start and i <= stop:
            return True
    return False


def obtain_confusion_matrix(metadata_sessions, results_sessions):
    true_positives = {}
    false_negatives = {}
    false_positives = {}
    true_negatives = {}

    for i in range(len(metadata_sessions)):
        path = metadata_sessions[i].noise.split('/')
        name = path[-2]
        key = name + " - " + str(metadata_sessions[i].snr)
        if key not in true_positives.keys():
            true_positives[key] = 0
            false_negatives[key] = 0
            false_positives[key] = 0
            true_negatives[key] = 0
        true_positive, false_negative, false_positive, true_negative = obtain_confusion_matrix_from_speech(metadata_sessions[i].speech, results_sessions[i])
        true_positives[key] += true_positive
        false_negatives[key] += false_negative
        false_positives[key] += false_positive
        true_negatives[key] += true_negative
    return true_positives, false_negatives, false_positives, true_negatives

def obtain_confusion_matrix_from_speech(metadata_speech, results_speech):
    true_positive = 0
    false_negative = 0
    false_positive = 0
    true_negative = 0
    ground_thruth = False
    prediction = False
    duration = int(metadata_speech[-1]["stop"] * 1000)
    for i in range(duration):
        ground_thruth = is_in_speech(i, metadata_speech)
        prediction = is_in_speech(i, results_speech)
        if ground_thruth and prediction:
            true_positive += 1
        elif ground_thruth and not prediction:
            false_negative +=1
        elif not ground_thruth and prediction:
            false_positive += 1
        else:
            true_negative += 1
    return true_positive, false_negative, false_positive, true_negative


def get_results(results_path):
    # get all the utterances
    results = {}
    models = os.scandir(results_path)
    for model in models:
        if model.is_file() or model.name == "metadata":
            continue
        results[model.name] = {}

        thresholds = os.scandir(model)
        for threshold in thresholds:
            if threshold.is_file():
                continue
            results[model.name][threshold.name] = {}
            
            files = os.scandir(threshold)
            for file in files:
                with open(file.path, "r") as input:
                    result = json.load(input)
                results[model.name][threshold.name][file.name] = result        

    return results


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--metadata')
    parser.add_argument('--results')
    args = parser.parse_args()
    metadata_path = args.metadata
    results_path = args.results

    metadata = {}
    male_metadata = metadata_path + "/male_noisy.json"
    with open(male_metadata, "r") as input:
        metadata_load = json.load(input)
    metadata_sessions = sessions_from_metadata(metadata_load)
    metadata['male'] = metadata_sessions

    female_metadata = metadata_path + "/female_noisy.json"
    with open(female_metadata, "r") as input:
        metadata_load = json.load(input)
    metadata_sessions = sessions_from_metadata(metadata_load)
    metadata['female'] = metadata_sessions

    noisy_metadata = metadata_path + "/noisy_sessions.json"
    with open(noisy_metadata, "r") as input:
        metadata_load = json.load(input)
    metadata_sessions = sessions_from_metadata(metadata_load)
    metadata['noisy'] = metadata_sessions
    
    results = get_results(results_path)
    metrics = {}

    for model in results.keys():
        metrics[model] = {}
        for threshold in results[model]:
            metrics[model][threshold] = {}
            for dataset in results[model][threshold]:
                metrics[model][threshold][dataset] = {}
                sessions = results[model][threshold][dataset]
                dataset_init = dataset.split("_")[0]
                metadata_sessions = metadata[dataset_init]
                true_positive, false_negative, false_positive, true_negative = obtain_confusion_matrix(metadata_sessions, sessions)

                for noise in true_positive.keys():
                    metrics[model][threshold][dataset][noise[0]] = {}

                for noise in true_positive.keys():
                    metrics[model][threshold][dataset][noise[0]][noise] = {}

                    total_milliseconds = true_positive[noise] + false_negative[noise] + false_positive[noise] + true_negative[noise]
                    try:
                        accuracy = (true_negative[noise] + true_positive[noise]) / (true_negative[noise] + true_positive[noise] + false_negative[noise] + false_positive[noise])
                        precision = true_positive[noise] / (true_positive[noise] + false_positive[noise])
                        recall = true_positive[noise] / (true_positive[noise] + false_negative[noise])
                        f1_score = (2 * precision * recall) / (precision + recall) 
                        metrics[model][threshold][dataset][noise[0]][noise]['total_milliseconds'] = total_milliseconds
                        metrics[model][threshold][dataset][noise[0]][noise]['true_positives'] = true_positive[noise]
                        metrics[model][threshold][dataset][noise[0]][noise]['false_negatives'] = false_negative[noise]
                        metrics[model][threshold][dataset][noise[0]][noise]['false_positives'] = false_positive[noise]
                        metrics[model][threshold][dataset][noise[0]][noise]['true_negatives'] = true_negative[noise]  
                        metrics[model][threshold][dataset][noise[0]][noise]['accuracy'] = accuracy
                        metrics[model][threshold][dataset][noise[0]][noise]['precision'] = precision
                        metrics[model][threshold][dataset][noise[0]][noise]['recall'] = recall
                        metrics[model][threshold][dataset][noise[0]][noise]['f1_score'] = f1_score
                    except:
                        metrics[model][threshold][dataset][noise[0]][noise]['total_milliseconds'] = total_milliseconds
                        metrics[model][threshold][dataset][noise[0]][noise]['true_positives'] = true_positive[noise]
                        metrics[model][threshold][dataset][noise[0]][noise]['false_negatives'] = false_negative[noise]
                        metrics[model][threshold][dataset][noise[0]][noise]['false_positives'] = false_positive[noise]
                        metrics[model][threshold][dataset][noise[0]][noise]['true_negatives'] = true_negative[noise] 


    metrics_json = json.dumps(metrics)
    results_file = results_path + "/processed.json"
    with open(results_file, "w") as outfile:
        outfile.write(metrics_json)