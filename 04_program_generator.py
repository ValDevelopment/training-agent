import pandas as pd

template = pd.read_csv("sbd_programming_template.csv")

current_maxes = {
    "squat": 180,
    "bench": 125,
    "deadlift": 220,
}

print(template.head())
print(current_maxes)