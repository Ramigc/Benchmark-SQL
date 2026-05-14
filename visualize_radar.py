import matplotlib
matplotlib.use("TkAgg")

import json
import numpy as np
import matplotlib.pyplot as plt

print("Start plotting...")

with open("benchmark_results.json", "r", encoding="utf-8") as f:
    data = json.load(f)

summary = data["summary"]

metrics = {
    "Accuracy": summary["accuracy"],
    "Completeness": summary["result_completeness"],
    "Query Efficiency": summary["query_efficiency"],
    "Latency Efficiency": summary["latency_efficiency"],
    "Token Efficiency": summary["token_efficiency"],
    "Robustness": summary["robust_accuracy"]
}

labels = list(metrics.keys())
values = list(metrics.values())

values += values[:1]

angles = np.linspace(0, 2*np.pi, len(labels), endpoint=False).tolist()
angles += angles[:1]

fig = plt.figure(figsize=(6,6))
ax = plt.subplot(111, polar=True)

ax.plot(angles, values, linewidth=2)
ax.fill(angles, values, alpha=0.25)

ax.set_thetagrids(np.degrees(angles[:-1]), labels)
ax.set_ylim(0,1)

plt.title("SQL Agent Benchmark Radar")

plt.show(block=True)