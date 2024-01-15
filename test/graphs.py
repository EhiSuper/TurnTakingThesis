import json
import matplotlib.pyplot as plt
import numpy as np
from regex import F

processed_path = "test/results/processed.json"
with open(processed_path, "r") as input:
    results_json = json.load(input)


results = {
}

for model, thresholds in results_json.items():
    results[model] = {}
    for threshold, datasets in thresholds.items():
        results[model][threshold] = {}
        for dataset, categories in datasets.items():
            if dataset == "noisy_sessions_results.json":
                break
            results[model][threshold][dataset] = {}
            results[model][threshold][dataset]['Total'] = {}
            results[model][threshold][dataset]['Total']['total_milliseconds'] = 0.0
            results[model][threshold][dataset]['Total']['true_positives'] = 0.0
            results[model][threshold][dataset]['Total']['true_negatives'] = 0.0
            results[model][threshold][dataset]['Total']['false_positives'] = 0.0
            results[model][threshold][dataset]['Total']['false_negatives'] = 0.0
            results[model][threshold][dataset]['Total']['accuracy'] = 0.0
            results[model][threshold][dataset]['Total']['precision'] = 0.0
            results[model][threshold][dataset]['Total']['recall'] = 0.0
            results[model][threshold][dataset]['Total']['f1_score'] = 0.0

            for category, subcategories in categories.items():
                results[model][threshold][dataset][category] = {}
                for subcategory, values in subcategories.items():
                    for key in values.keys():
                        results[model][threshold][dataset][category][key] = 0.0
                    for key, value in values.items():
                        results[model][threshold][dataset][category][key] += value
                        results[model][threshold][dataset]['Total'][key] += value
                
                true_positives = results[model][threshold][dataset][category]['true_positives']
                true_negatives = results[model][threshold][dataset][category]['true_negatives']
                false_positives = results[model][threshold][dataset][category]['false_positives']
                false_negatives = results[model][threshold][dataset][category]['false_negatives']
                results[model][threshold][dataset][category]['accuracy'] = (true_positives + true_negatives) / (false_negatives + false_positives + true_negatives + true_positives)
                precision = true_positives / (true_positives + false_positives)
                results[model][threshold][dataset][category]['precision'] = precision
                recall = true_positives / (true_positives + false_negatives)
                results[model][threshold][dataset][category]['recall'] = recall
                results[model][threshold][dataset][category]['f1_score'] = (2 * precision * recall) / (precision + recall)

            true_positives = results[model][threshold][dataset]['Total']['true_positives']
            true_negatives = results[model][threshold][dataset]['Total']['true_negatives']
            false_positives = results[model][threshold][dataset]['Total']['false_positives']
            false_negatives = results[model][threshold][dataset]['Total']['false_negatives']
            results[model][threshold][dataset]['Total']['accuracy'] = (true_positives + true_negatives) / (false_negatives + false_positives + true_negatives + true_positives)
            precision = true_positives / (true_positives + false_positives)
            results[model][threshold][dataset]['Total']['precision'] = precision
            recall = true_positives / (true_positives + false_negatives)
            results[model][threshold][dataset]['Total']['recall'] = recall
            results[model][threshold][dataset]['Total']['f1_score'] = (2 * precision * recall) / (precision + recall)



choosen_metric = 'accuracy'
max_metric_male = 0.0
max_metric_female = 0.0
chosen_threshold = {
    'silero' : {
        'female_noisy_results.json' : 0,
        'male_noisy_results.json' : 0
    },
    'webrtc-vad' : {
        'female_noisy_results.json' : 0,
        'male_noisy_results.json' : 0
    }
}
for model, thresholds in results.items():
    max_metric_male = 0.0
    max_metric_female = 0.0
    for threshold, datasets in thresholds.items():
        for dataset, categories in datasets.items():
            if dataset == "male_noisy_results.json":
                if results[model][threshold][dataset]['Total'][choosen_metric] > max_metric_male:
                    max_metric_male = results[model][threshold][dataset]['Total'][choosen_metric]
                    chosen_threshold[model][dataset] = threshold

            else:
                if results[model][threshold][dataset]['Total'][choosen_metric] > max_metric_female:
                    max_metric_female = results[model][threshold][dataset]['Total'][choosen_metric]
                    chosen_threshold[model][dataset] = threshold


models = ['silero', 'webrtc-vad']
datasets = ['male_noisy_results.json', 'female_noisy_results.json']
#metrics graph
for model in models:
    for dataset in datasets:
        metrics = ['accuracy', 'precision', 'recall', 'f1_score']
        threshold = chosen_threshold[model][dataset]
        values = {
            'Nature': [],
            'Domestic': [],
            'Office': [],
            'Public': [],
            'Street': [],
            'Transportation': [],
            'Total': []
        }

        for value in values:
            for metric in metrics:
                if value == 'Total':
                    values[value].append(round(results[model][threshold][dataset][value][metric], 2)) 
                else:          
                    values[value].append(round(results[model][threshold][dataset][value[0]][metric], 2))


        x = np.arange(len(metrics))  # the label locations
        width = 0.10  # the width of the bars
        multiplier = 0

        fig, ax = plt.subplots(layout='constrained')

        for category, measurement in values.items():
            offset = width * multiplier
            rects = ax.bar(x + offset, measurement, width, label=category)
            ax.bar_label(rects, padding=3)
            multiplier += 1

        # Add some text for labels, title and custom x-axis tick labels, etc.
        ax.set_ylabel('Values')
        ax.set_title(f'{model} {dataset} {threshold}')
        ax.set_xticks(x + width, metrics)
        ax.legend(loc='upper left', ncols=4)
        ax.set_ylim(0, 1.5)

#metrics graph recap
groups = ['Silero-male', 'Silero-female', 'Webrtc-male', 'Webrtc-female']
values = {
    'Accuracy': [],
    'Precision': [],
    'Recall': [],
    'F1-score': []
}

for model in models:
    for dataset in datasets:
        threshold = chosen_threshold[model][dataset]
        values['Accuracy'].append(round(results[model][threshold][dataset]['Total']['accuracy'], 2))
        values['Precision'].append(round(results[model][threshold][dataset]['Total']['precision'], 2))
        values['Recall'].append(round(results[model][threshold][dataset]['Total']['recall'], 2))
        values['F1-score'].append(round(results[model][threshold][dataset]['Total']['f1_score'], 2))


x = np.arange(len(groups))  # the label locations
width = 0.10  # the width of the bars
multiplier = 0

fig, ax = plt.subplots(layout='constrained')

for metric, measurement in values.items():
    offset = width * multiplier
    rects = ax.bar(x + offset, measurement, width, label=metric)
    ax.bar_label(rects, padding=3)
    multiplier += 1

# Add some text for labels, title and custom x-axis tick labels, etc.
ax.set_ylabel('Values')
ax.set_title(f'Metrics recap')
ax.set_xticks(x + width, groups)
ax.legend(loc='upper left', ncols=4)
ax.set_ylim(0, 1.5)

#Roc-Auc score
true_postive_rates = {
    'silero' : {
        'female_noisy_results.json' : [1],
        'male_noisy_results.json' : [1]
    },
    'webrtc-vad' : {
        'female_noisy_results.json' : [1],
        'male_noisy_results.json' : [1]
    }
}
false_positive_rates = {
    'silero' : {
        'female_noisy_results.json' : [1],
        'male_noisy_results.json' : [1]
    },
    'webrtc-vad' : {
        'female_noisy_results.json' : [1],
        'male_noisy_results.json' : [1]
    }
}

thresholds = {
    'silero': [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9],
    'webrtc-vad' : [0, 1, 2, 3]
}

for model in models:
    for dataset in datasets:
        for threshold in thresholds[model]:
            recall = results[model][str(threshold)][dataset]['Total']['recall']
            true_postive_rates[model][dataset].append(recall)
            true_negatives = results[model][str(threshold)][dataset]['Total']['true_negatives']
            false_positives = results[model][str(threshold)][dataset]['Total']['false_positives']
            false_positive_rate = false_positives / (false_positives + true_negatives)
            false_positive_rates[model][dataset].append(false_positive_rate)
        
        true_postive_rates[model][dataset].append(0)
        false_positive_rates[model][dataset].append(0)

for dataset in datasets:
    fig, ax = plt.subplots()

    ax.plot(false_positive_rates[models[0]][dataset], true_postive_rates[models[0]][dataset], label=f'{models[0]}')
    ax.plot(false_positive_rates[models[1]][dataset], true_postive_rates[models[1]][dataset], label=f'{models[1]}')
    ax.plot([0,1], [0,1], linestyle='dashed')
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set(xlabel='False postive rate', ylabel='True positive rate', title=f'ROC curve {dataset}')
    ax.legend()
    ax.grid()


#noisy_sessions with different snr levels
results_snr = {}
models = ['silero', 'webrtc-vad']
dataset = 'noisy_sessions_results.json'
snr_levels = [20, 10, 0, -10, -20]
labels = {
            'N': 'Nature',
            'D': 'Domestic',
            'O': 'Office',
            'P': 'Public',
            'S': 'Street',
            'T': 'Transportation',
            'Total': 'Total'
        }
chosen_threshold_snr = {
    'silero': '0.6',
    'webrtc-vad': '2'
}
category_accuracy = {}
for model in models:
    category_accuracy[model] = {}
    threshold = chosen_threshold_snr[model]
    category_accuracy[model]['Total'] = {}
    category_total_true_positives = {}
    category_total_true_negatives = {}
    category_total_false_positives = {}
    category_total_false_negatives = {}
    for snr_level in snr_levels:
        category_accuracy[model]['Total'][snr_level] = 0
        category_total_true_positives[snr_level] = 0
        category_total_true_negatives[snr_level] = 0
        category_total_false_positives[snr_level] = 0
        category_total_false_negatives[snr_level] = 0

    for category, subcategories in results_json[model][threshold][dataset].items():
        category_accuracy[model][category] = {}
        category_true_positives = {}
        category_true_negatives = {}
        category_false_positives = {}
        category_false_negatives = {}
        for snr_level in snr_levels:
            category_accuracy[model][category][snr_level] = 0
            category_true_positives[snr_level] = 0
            category_true_negatives[snr_level] = 0
            category_false_positives[snr_level] = 0
            category_false_negatives[snr_level] = 0
        
        for subcategory, metrics in subcategories.items():
            subcategory_snr_level = int(subcategory.split(" ")[2])

            for snr_level in snr_levels:
                if snr_level == subcategory_snr_level:
                    category_true_positives[snr_level] += metrics['true_positives']
                    category_true_negatives[snr_level] += metrics['true_negatives']
                    category_false_positives[snr_level] += metrics['false_positives']
                    category_false_negatives[snr_level] += metrics['false_negatives']
        
        for snr_level in snr_levels:
            true_positives = category_true_positives[snr_level]
            true_negatives = category_true_negatives[snr_level]
            false_positives = category_false_positives[snr_level]
            false_negatives = category_false_negatives[snr_level]
            category_accuracy[model][category][snr_level] = (true_positives + true_negatives) / (false_negatives + false_positives + true_negatives + true_positives)
        
        for snr_level in snr_levels:
            category_total_true_positives[snr_level] += category_true_positives[snr_level]
            category_total_true_negatives[snr_level] += category_true_negatives[snr_level]
            category_total_false_positives[snr_level] += category_false_positives[snr_level]
            category_total_false_negatives[snr_level] += category_false_negatives[snr_level]

    for snr_level in snr_levels:
        true_positives = category_total_true_positives[snr_level]
        true_negatives = category_total_true_negatives[snr_level]
        false_positives = category_total_false_positives[snr_level]
        false_negatives = category_total_false_negatives[snr_level]
        category_accuracy[model]['Total'][snr_level] = (true_positives + true_negatives) / (false_negatives + false_positives + true_negatives + true_positives)

for model in models:
    fig, ax = plt.subplots()
    for category, levels in category_accuracy[model].items():
        y = levels.values()
        ax.plot(snr_levels, y, label=labels[category])

    ax.set(xlabel='SNR levels', ylabel='Accuracy', title=f'Accuracy {model}')
    ax.legend()
    ax.grid()

fig, ax = plt.subplots()
for model in models:
    y = category_accuracy[model]['Total'].values()
    ax.plot(snr_levels, y, label=model)

ax.set(xlabel='SNR levels', ylabel='Accuracy', title=f'Accuracy between models')
ax.legend()
ax.grid()

plt.show()

