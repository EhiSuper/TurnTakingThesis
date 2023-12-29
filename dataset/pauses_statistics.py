import json
import numpy as np

pauses = []

with open("inter_speech_intervals.json", "r") as input:
    pauses = json.load(input)

max = max(pauses)
print(f'Max: {max}')
mean = np.mean(pauses)
print(f'Mean: {mean}')
quartiles = np.quantile(pauses, [0,0.25,0.5,0.75,1]) 
print(f'Quartiles: {quartiles}')