import json
import matplotlib.pyplot as plt
import numpy as np


processed_path = "test/results/processed.json"
with open(processed_path, "r") as input:
    results_json = json.load(input)

models = ['silero', 'webrtc-vad']
datasets = ['male_noisy_results.json', 'female_noisy_results.json']
confidence_thresholds = {
    'silero': ['0.1', '0.2', '0.3', '0.4', '0.5', '0.6', '0.7', '0.8', '0.9'],
    'webrtc-vad': ['0', '1', '2', '3']
}
metrics = ['total_milliseconds', 'true_positives', 'true_negatives', 'false_positives', 'false_negatives']
categories = ['N', 'D', 'O', 'P', 'S', 'T']
results = {}

for model in models:
    results[model] = {}
    for threshold in confidence_thresholds[model]:
        results[model][threshold] = {}
        for dataset in datasets:
            results[model][threshold][dataset] = {}
            for category in categories:
                results[model][threshold][dataset][category] = {}
                for metric in metrics:
                    results[model][threshold][dataset][category][metric] = 0
                
                for subcategory in results_json[model][threshold][dataset][category].keys():
                    for metric in metrics:
                        results[model][threshold][dataset][category][metric] += results_json[model][threshold][dataset][category][subcategory][metric]

for model in models:
    for threshold in confidence_thresholds[model]:
        for dataset in datasets:
            results[model][threshold][dataset]['Total'] = {}
            for metric in metrics:
                results[model][threshold][dataset]['Total'][metric] = 0
            for category in categories:   
                for metric in metrics:     
                    results[model][threshold][dataset]['Total'][metric] += results[model][threshold][dataset][category][metric]

for model in models:
    for threshold in confidence_thresholds[model]:
        for dataset in datasets:
            for category in results[model][threshold][dataset].keys():
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
                

chosen_metric = 'f1_score'
max_metric = 0
chosen_threshold = {}

for model in models:
    chosen_threshold[model] = {}
    for dataset in datasets:
        max_metric = 0
        for threshold in confidence_thresholds[model]:
            metric = results[model][threshold][dataset]['Total'][chosen_metric]
            if metric > max_metric:
                max_metric = results[model][threshold][dataset]['Total'][chosen_metric]
                chosen_threshold[model][dataset] = threshold
            

metrics = ['accuracy', 'precision', 'recall', 'f1_score']
metrics_labels = ['Accuracy','Precision','Recall','F1-Score']
#metrics graph
for model in models:
    for dataset in datasets:
        
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


        x = np.arange(0, 4*len(metrics), 4)  # the label locations
        width = 0.50  # the width of the bars
        multiplier = 0

        fig, ax = plt.subplots(figsize=(20, 10), layout='constrained')

        for category, measurement in values.items():
            offset = width * multiplier
            rects = ax.bar(x + offset, measurement, width, label=category)
            ax.bar_label(rects, padding=3)
            multiplier += 1

        # Add some text for labels, title and custom x-axis tick labels, etc.
        ax.set_ylabel('Values')
        ax.set_title(f'Performance metrics of model: {model} on: {dataset} with threshold:{threshold}', pad=20)
        ax.set_xticks(x + 3*width, metrics_labels)
        ax.legend(loc='upper left', ncols=4)
        ax.set_ylim(0, 1.3)
        #plt.savefig(f'test/graphs_images/Performance metrics of model: {model} on: {dataset} with threshold:{threshold}.png', format='png', dpi=1200)

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


x = np.arange(0, 2.5*len(groups), 2.5)  # the label locations
width = 0.50  # the width of the bars
multiplier = 0

fig, ax = plt.subplots(figsize=(20, 10), layout='constrained')

for metric, measurement in values.items():
    offset = width * multiplier
    rects = ax.bar(x + offset, measurement, width, label=metric)
    ax.bar_label(rects, padding=3)
    multiplier += 1

# Add some text for labels, title and custom x-axis tick labels, etc.
ax.set_ylabel('Values')
ax.set_title(f'Metrics summary', pad=20)
ax.set_xticks(x + 1.5*width, groups)
ax.legend(loc='upper left', ncols=4)
ax.set_ylim(0, 1.3)
#plt.savefig('test/graphs_images/Metrics summary.png', format='png', dpi=1200)

#Roc curve
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


for model in models:
    for dataset in datasets:
        for threshold in confidence_thresholds[model]:
            recall = results[model][threshold][dataset]['Total']['recall']
            true_postive_rates[model][dataset].append(recall)
            true_negatives = results[model][threshold][dataset]['Total']['true_negatives']
            false_positives = results[model][threshold][dataset]['Total']['false_positives']
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
    dataset = dataset.split('_')[0]
    ax.set(xlabel='False positive rate', ylabel='True positive rate', title=f'ROC curve for the {dataset} dataset')
    ax.legend()
    ax.grid()
    #plt.savefig(f'test/graphs_images/ROC curve for the {dataset} dataset.png', format='png', dpi=1200)


#noisy_sessions with different snr levels
results = {}
models = ['silero', 'webrtc-vad']
datasets = ['noisy_sessions_results.json']
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

metrics = ['total_milliseconds', 'true_positives', 'true_negatives', 'false_positives', 'false_negatives']

for model in models:
    results[model] = {}
    for threshold in confidence_thresholds[model]:
        results[model][threshold] = {}
        for dataset in datasets:
            results[model][threshold][dataset] = {}
            for category in categories:
                results[model][threshold][dataset][category] = {}
                for snr_level in snr_levels:
                    results[model][threshold][dataset][category][snr_level] = {}
                    for metric in metrics:
                        results[model][threshold][dataset][category][snr_level][metric] = 0
                
                for subcategory in results_json[model][threshold][dataset][category].keys():
                    level = int(subcategory.split(' ')[2])
                    for metric in metrics:
                        results[model][threshold][dataset][category][level][metric] += results_json[model][threshold][dataset][category][subcategory][metric]

for model in models:
    for threshold in confidence_thresholds[model]:
        for dataset in datasets:
            results[model][threshold][dataset]['Total'] = {}
            for snr_level in snr_levels:
                    results[model][threshold][dataset]['Total'][snr_level] = {}
                    for metric in metrics:
                        results[model][threshold][dataset]['Total'][snr_level][metric] = 0
            for category in categories: 
                for snr_level in snr_levels:  
                    for metric in metrics:     
                        results[model][threshold][dataset]['Total'][snr_level][metric] += results[model][threshold][dataset][category][snr_level][metric]

for model in models:
    for threshold in confidence_thresholds[model]:
        for dataset in datasets:
            for category in results[model][threshold][dataset].keys():
                for snr_level in snr_levels:
                    true_positives = results[model][threshold][dataset][category][snr_level]['true_positives']
                    true_negatives = results[model][threshold][dataset][category][snr_level]['true_negatives']
                    false_positives = results[model][threshold][dataset][category][snr_level]['false_positives']
                    false_negatives = results[model][threshold][dataset][category][snr_level]['false_negatives']
                    results[model][threshold][dataset][category][snr_level]['accuracy'] = (true_positives + true_negatives) / (false_negatives + false_positives + true_negatives + true_positives)
                    recall = true_positives / (true_positives + false_negatives)
                    results[model][threshold][dataset][category][snr_level]['recall'] = recall
                    if (true_positives + false_positives) != 0:
                        
                        precision = true_positives / (true_positives + false_positives)
                        results[model][threshold][dataset][category][snr_level]['precision'] = precision
                        results[model][threshold][dataset][category][snr_level]['f1_score'] = (2 * precision * recall) / (precision + recall)
                    else:
                        print(model, threshold, category, snr_level)

accuracies = {}

for model in models:
    accuracies[model] = {}
    threshold = chosen_threshold[model]['male_noisy_results.json']
    accuracies[model][threshold] = {}
    for dataset in datasets:
        accuracies[model][threshold][dataset] = {}
        for category in results[model][threshold][dataset].keys():
            accuracies[model][threshold][dataset][category] = []
            for snr_level in snr_levels:
                if 'accuracy' in results[model][threshold][dataset][category][snr_level]:
                    accuracy = results[model][threshold][dataset][category][snr_level]['accuracy']
                    accuracies[model][threshold][dataset][category].append(accuracy)
        
#graph of accuracies for category with different SNR levels
for model in models:
    fig, ax = plt.subplots()
    threshold = chosen_threshold[model]['male_noisy_results.json']
    
    for category, accuracy_list in accuracies[model][threshold][datasets[0]].items():
        ax.plot(snr_levels, accuracy_list, label=labels[category])
            

    ax.set(xlabel='SNR levels', ylabel='Accuracy', title=f'Accuracy {model}')
    ax.legend()
    ax.grid()
    plt.savefig(f'test/graphs_images/Accuracy {model}.png', format='png', dpi=1200)

#graph of accuracies of category 'Total' from the models
fig, ax = plt.subplots()
for model in models:
    threshold = chosen_threshold[model]['male_noisy_results.json']
    y = accuracies[model][threshold][datasets[0]]['Total']
    ax.plot(snr_levels, y, label=model)

ax.set(xlabel='SNR levels', ylabel='Accuracy', title=f'Accuracy between models')
ax.legend()
ax.grid()
plt.savefig('test/graphs_images/Accuracy between models.png', format='png', dpi=1200)


f1_scores = {}

for model in models:
    f1_scores[model] = {}
    threshold = chosen_threshold[model]['male_noisy_results.json']
    f1_scores[model][threshold] = {}
    for dataset in datasets:
        f1_scores[model][threshold][dataset] = {}
        for category in results[model][threshold][dataset].keys():
            f1_scores[model][threshold][dataset][category] = []
            for snr_level in snr_levels:
                if 'f1_score' in results[model][threshold][dataset][category][snr_level]:
                    f1_score = results[model][threshold][dataset][category][snr_level]['f1_score']
                    f1_scores[model][threshold][dataset][category].append(f1_score)
        
#graph of f1-score for category with different SNR levels
for model in models:
    fig, ax = plt.subplots()
    threshold = chosen_threshold[model]['male_noisy_results.json']
    
    for category, accuracy_list in f1_scores[model][threshold][datasets[0]].items():
        ax.plot(snr_levels, accuracy_list, label=labels[category])
            

    ax.set(xlabel='SNR levels', ylabel='F1-Score', title=f'F1-Score {model}')
    ax.legend()
    ax.grid()
    plt.savefig(f'test/graphs_images/F1-Score {model}.png', format='png', dpi=1200)

#graph of f1-score of category 'Total' from the models
fig, ax = plt.subplots()
for model in models:
    threshold = chosen_threshold[model]['male_noisy_results.json']
    y = f1_scores[model][threshold][datasets[0]]['Total']
    ax.plot(snr_levels, y, label=model)

ax.set(xlabel='SNR levels', ylabel='F1-Score', title=f'F1-Score between models')
ax.legend()
ax.grid()
plt.savefig('test/graphs_images/F1-Score between models.png', format='png', dpi=1200)
plt.show()



