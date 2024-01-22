import json
from matplotlib import table
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
labels = {
            'N': 'Nature',
            'D': 'Domestic',
            'O': 'Office',
            'P': 'Public',
            'S': 'Street',
            'T': 'Transportation',
            'Total': 'Total'
        }
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

tables_path = "test/tables.txt"
with open(tables_path, "w") as output:
    for model in models:
        for confidence_threshold in confidence_thresholds[model]:
            table_content = None
            table_content = "\\begin{table}[H]\n"
            table_content += "\centering\n"
            table_content += "\small\n"
            table_content += "\\begin{tabular}{ |c|c|c|c|c|c|c|c|c| }\n"
            table_content += "\hline\n"
            table_content += " &"
            table_content += "\multicolumn{2}{|c|}{Accuracy}&"
            table_content += "\multicolumn{2}{|c|}{Precision}&"
            table_content += "\multicolumn{2}{|c|}{Recall}&"
            table_content += "\multicolumn{2}{|c|}{F1-score} \\\ \n"
            table_content += "\hline\n"
            table_content += "Noise category & M & F & M & F & M & F & M & F \\\ \n"
            table_content += "\hline\n"

            for category, values in results_json[model][confidence_threshold][datasets[0]].items():
                accuracy_m = round(results[model][confidence_threshold][datasets[0]][category]['accuracy'], 2)
                accuracy_f = round(results[model][confidence_threshold][datasets[1]][category]['accuracy'], 2)
                precision_m = round(results[model][confidence_threshold][datasets[0]][category]['precision'], 2)
                precision_f = round(results[model][confidence_threshold][datasets[1]][category]['precision'], 2)
                recall_m = round(results[model][confidence_threshold][datasets[0]][category]['recall'], 2)
                recall_f = round(results[model][confidence_threshold][datasets[1]][category]['recall'], 2)
                f1_score_m = round(results[model][confidence_threshold][datasets[0]][category]['f1_score'], 2)
                f1_score_f = round(results[model][confidence_threshold][datasets[1]][category]['f1_score'], 2)
                table_content += f'{labels[category]} & {accuracy_m} & {accuracy_f} & {precision_m} & {precision_f} & {recall_m} & {recall_f} & {f1_score_m} & {f1_score_f} \\\ \n'
            
            accuracy_m = round(results[model][confidence_threshold][datasets[0]]['Total']['accuracy'], 2)
            accuracy_f = round(results[model][confidence_threshold][datasets[1]]['Total']['accuracy'], 2)
            precision_m = round(results[model][confidence_threshold][datasets[0]]['Total']['precision'], 2)
            precision_f = round(results[model][confidence_threshold][datasets[1]]['Total']['precision'], 2)
            recall_m = round(results[model][confidence_threshold][datasets[0]]['Total']['recall'], 2)
            recall_f = round(results[model][confidence_threshold][datasets[1]]['Total']['recall'], 2)
            f1_score_m = round(results[model][confidence_threshold][datasets[0]]['Total']['f1_score'], 2)
            f1_score_f = round(results[model][confidence_threshold][datasets[1]]['Total']['f1_score'], 2)
            table_content += f'Total & {accuracy_m} & {accuracy_f} & {precision_m} & {precision_f} & {recall_m} & {recall_f} & {f1_score_m} & {f1_score_f} \\\ \n'

            table_content += "\hline\n"
            table_content += "\end{tabular}\n"
            table_content += '\caption{' + f'Model: {model}, confidence threshold: {confidence_threshold}' + '}\n'
            table_content += "\end{table}\n"
            table_content += "\n"
            output.write(table_content)

#noisy_sessions with different snr levels
chosen_metric = 'f1_score'
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
                accuracy = results[model][threshold][dataset][category][snr_level]['accuracy']
                accuracies[model][threshold][dataset][category].append(accuracy)

tables_path = "test/tables.txt"
with open(tables_path, "a") as output:
    for model in models:
        table_content = None
        table_content = "\\begin{table}[H]\n"
        table_content += "\centering\n"
        table_content += "\small\n"

        table_content += "\\begin{tabular}{ |c|c|c|c|c|c|c|c|c|c|c| }\n"
        table_content += "\hline\n"
        table_content += " & \multicolumn{5}{|c|}{Accuracy} & \multicolumn{5}{|c|}{Precision} \\\ \n"
        table_content += "\hline\n"
        table_content += "Threshold & 20 & 10 & 0 & -10 & -20 & 20 & 10 & 0 & -10 & -20 \\\ \n"
        table_content += "\hline\n"

        for confidence_threshold in confidence_thresholds[model]:
            table_content += f'{confidence_threshold}'
            for snr_level in snr_levels:
                accuracy = round(results[model][confidence_threshold][datasets[0]]['Total'][snr_level]['accuracy'], 2)
                table_content += f'& {accuracy}'
            
            for snr_level in snr_levels:
                try:
                    precision = round(results[model][confidence_threshold][datasets[0]]['Total'][snr_level]['precision'], 2)
                    table_content += f'& {precision}'
                except:
                    table_content += f'& '
            table_content += ' \\\ \n'
           
        table_content += "\hline\n"
        table_content += "\end{tabular}\n"


        table_content += "\\begin{tabular}{ |c|c|c|c|c|c|c|c|c|c|c| }\n"
        table_content += "\hline\n"
        table_content += " & \multicolumn{5}{|c|}{Recall} & \multicolumn{5}{|c|}{F1-Score} \\\ \n"
        table_content += "\hline\n"
        table_content += "Threshold & 20 & 10 & 0 & -10 & -20 & 20 & 10 & 0 & -10 & -20 \\\ \n"
        table_content += "\hline\n"
        
        for confidence_threshold in confidence_thresholds[model]:
            table_content += f'{confidence_threshold}'
            for snr_level in snr_levels:
                recall = round(results[model][confidence_threshold][datasets[0]]['Total'][snr_level]['recall'], 2)
                table_content += f'& {recall}'
            
            for snr_level in snr_levels:
                f1_score = round(results[model][confidence_threshold][datasets[0]]['Total'][snr_level]['f1_score'], 2)
                table_content += f'& {f1_score}'
            table_content += ' \\\ \n'
           
        table_content += "\hline\n"
        table_content += "\end{tabular}\n"
        table_content += '\caption{Performance metrics of the "Total" category for the model: ' + f'{model}' + '} \n'
        table_content += "\end{table}\n"
        table_content += "\n"
        output.write(table_content)
