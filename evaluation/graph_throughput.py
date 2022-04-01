"""
    This script will graph the experiments
"""
import os
from os import listdir
from os.path import isfile, join
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

experiment_indepedent_variables = {
    "experiment_1": "Peers",
    "experiment_2": "Miners",
    "experiment_3": "Contracts",
    "experiment_4": "Contracts"
}

experiment_extra_variables = {
    "experiment_4": "Miners"
}

experiment_x_axis = {
    "experiment_1": [x for x in range(2, 21, 2)],
    "experiment_2": [x for x in range(1, 11)],
    "experiment_4": [x for x in range(500, 2501, 500)]
}

experiment_y_axis = {
    "experiment_1": [y for y in range(0, 201, 20)],
    "experiment_2": [y for y in range(0, 251, 25)],
    "experiment_3": [y for y in range(0, 81, 10)],
    "experiment_4": [y for y in range(0, 131, 10)],
}

experiment_titles = {
    "experiment_1": "Blockchain Throughput per Number of Agents \n (1 Miner, 100 Contracts, '0' Target Hash)",
    "experiment_2": "Blockchain Throughput per Number of Miners \n (16 Agents, 100 Contracts, '0' Target Hash)",
    "experiment_3": "Blockchain Throughput per Number of Contracts \n (16 Agents, 1 Miner, '0' Target Hash)",
    "experiment_4": "Blockchain Throughput against Number of Contracts and Miners \n (6 Agents, '0' Target Hash)"
}

experiment_x_label = {
    "experiment_1": "Agents"
}


def getExperimentFileNames():
    files = [f for f in listdir(os.curdir + "/evaluation")]
    files = filter((lambda f_n: f_n.startswith(
        'experiment') and f_n.endswith('.csv')), files)
    files = [f for f in files]
    return files


def loadExperimentData(filename):
    df = pd.read_csv(os.curdir + "/evaluation/" + filename)
    return df


def calculateThroughput(df):
    df["Throughput"] = df["Transactions"] / df["Time"]


def getIndepedentVariable(file):
    striped_csv = file.replace(".csv", "")
    return experiment_indepedent_variables[striped_csv]


def graphDataframe(file, df):
    indep = getIndepedentVariable(file)
    stripped_file = file.replace(".csv", "")

    if stripped_file in experiment_extra_variables:
        lplot = sns.lineplot(data=df, x=indep, hue=experiment_extra_variables[stripped_file], y="Throughput",
                             err_style='bars', err_kws={"capsize": 4})
    else:
        lplot = sns.lineplot(data=df, x=indep, y="Throughput",
                             err_style='bars', err_kws={"capsize": 4})

    if stripped_file in experiment_x_axis:
        lplot.set_xticks(experiment_x_axis[stripped_file])
        lplot.set_xticklabels(experiment_x_axis[stripped_file])

    if stripped_file in experiment_y_axis:
        lplot.set_yticks(experiment_y_axis[stripped_file])
        lplot.set_yticklabels(experiment_y_axis[stripped_file])

    if stripped_file in experiment_titles:
        lplot.set(title=experiment_titles[stripped_file])

    if stripped_file in experiment_x_label:
        lplot.set(xlabel=experiment_x_label[stripped_file])

    lplot.set(ylabel='Throughput (Transactions/Second)')
    stripped_file = file.replace(".csv", "")
    plt.savefig("evaluation/" + stripped_file + ".png")
    plt.clf()


for file in getExperimentFileNames():
    df = loadExperimentData(file)
    calculateThroughput(df)
    graphDataframe(file, df)
