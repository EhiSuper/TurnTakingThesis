import argparse
import json

from matplotlib.rcsetup import non_interactive_bk

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
        key = metadata_sessions[i].noise + " - " + str(metadata_sessions[i].snr)
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



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--metadata')
    parser.add_argument('--results')
    args = parser.parse_args()
    metadata_file = args.metadata
    results_file = args.results
    #metadata_file = "test/male_noisy.json"
    #results_file = "test/male_noisy_results.json"
    with open(metadata_file, "r") as input:
        metadata = json.load(input)
    metadata_sessions = sessions_from_metadata(metadata)
    with open(results_file, "r") as input:
        results = json.load(input)

    true_positive, false_negative, false_positive, true_negative = obtain_confusion_matrix(metadata_sessions, results)
    
    accuracy = {}
    precision = {}
    recall = {}
    f1_score = {}

    for noise in true_positive.keys():
        total_milliseconds = true_positive[noise] + false_negative[noise] + false_positive[noise] + true_negative[noise]
        try:
            accuracy[noise] = (true_negative[noise] + true_positive[noise]) / (true_negative[noise] + true_positive[noise] + false_negative[noise] + false_positive[noise])
            precision[noise] = true_positive[noise] / (true_positive[noise] + false_positive[noise])
            recall[noise] = true_positive[noise] / (true_positive[noise] + false_negative[noise])
            f1_score[noise] = (2 * precision[noise] * recall[noise]) / (precision[noise] + recall[noise])   
            print(f'Noise: {noise}')
            print(f'Total milliseconds: {total_milliseconds}')
            print(f'True positives: {true_positive[noise]}')
            print(f'False negatives: {false_negative[noise]}')
            print(f'False positives: {false_positive[noise]}')
            print(f'True negatives: {true_negative[noise]}')
            print(f'Accuracy: {accuracy[noise]}')
            print(f'Precision: {precision[noise]}')
            print(f'Recall: {recall[noise]}')
            print(f'F1 score: {f1_score[noise]}')
            print('')
        except:
            print(f'Noise: {noise}')
            print(f'Total milliseconds: {total_milliseconds}')
            print(f'True positives: {true_positive[noise]}')
            print(f'False negatives: {false_negative[noise]}')
            print(f'False positives: {false_positive[noise]}')
            print(f'True negatives: {true_negative[noise]}')
            print('')

    total_true_positive = 0
    total_false_negative = 0
    total_false_positive = 0
    total_true_negative = 0

    for noise in true_positive.keys():
        total_true_positive += true_positive[noise]
        total_false_negative += false_negative[noise]
        total_false_positive += false_positive[noise]
        total_true_negative += true_negative[noise]

    total_milliseconds = total_true_positive + total_false_negative + total_false_positive + total_false_negative
    print(f'Total milliseconds: {total_milliseconds}')
    print(f'Total true positives: {total_true_positive}')
    print(f'Total false negatives: {total_false_negative}')
    print(f'Total false positives: {total_false_positive}')
    print(f'Total true negatives: {total_true_negative}')

    total_accuracy = (total_true_negative + total_true_positive) / (total_true_negative + total_true_positive + total_false_negative + total_false_positive)
    print(f'Total accuracy: {total_accuracy}')

    total_precision = total_true_positive / (total_true_positive + total_false_positive)
    print(f'Total precision: {total_precision}')

    total_recall = total_true_positive / (total_true_positive + total_false_negative)
    print(f'Total recall: {total_recall}')

    total_f1_score = (2 * total_precision * total_recall) / (total_precision + total_recall)
    print(f'Total F1 score: {total_f1_score}')