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
    "experiment_3": "Contracts"
}

experiment_x_axis = {
    "experiment_1": [x for x in range(2, 21, 2)]
}


def getExperimentFileNames():
    files = [f for f in listdir(os.curdir + "/evaluation")]
    files = filter((lambda f_n: f_n.startswith('experiment')), files)
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
    lplot = sns.lineplot(data=df, x=indep, y="Throughput", )
    stripped_file = file.replace(".csv", "")
    if stripped_file in experiment_x_axis:
        lplot.set_xticks(experiment_x_axis[stripped_file])
        lplot.set_xticklabels(experiment_x_axis[stripped_file])
    stripped_file = file.replace(".csv", "")
    plt.savefig(stripped_file + ".png")
    plt.clf()


for file in getExperimentFileNames():
    df = loadExperimentData(file)
    calculateThroughput(df)
    graphDataframe(file, df)
