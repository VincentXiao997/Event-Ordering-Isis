import matplotlib.pyplot as plt
import sys

PATH = "/home/vince/8nodeF/"

def draw():
    node_names = ["node1", "node2","node3" ,"node4","node5"] #,"node6","node7","node8"]
    timeLists = []
    for node_name in node_names:
        fileName = PATH + "timeFile-" + node_name + ".txt"
        timeLists.append(read_file(fileName))

    maxLen = sys.maxsize
    result = []
    for times in timeLists:
        if len(times) < maxLen:
            maxLen = len(times)

    for i in range(maxLen):
        temp = []
        for times in timeLists:
            temp.append(times[i])
        result.append(max(temp) - min(temp))

    fig1 = plt.figure(1)  # for bandwidth
    plt.title("Time interval between the first node and the last node")
    plt.xlabel("Message Number")
    plt.ylabel("Time/Second")
    plt.plot(range(1, len(result) + 1), result)
    figure = plt.gcf()
    figure.set_size_inches(12, 10)
    fig1.savefig('time_' + "8_node_F" + '.png')






def read_file(config_file):
    f = open(config_file, "r")
    times = []
    configInfo = f.readline()
    while configInfo:
        configInfo = configInfo.split(", ")
        timestr = configInfo[1]
        time = float(timestr[:-2])
        times.append(time)
        configInfo = f.readline()
    times.sort()
    f.close()
    return times




if __name__ == "__main__":
    draw()