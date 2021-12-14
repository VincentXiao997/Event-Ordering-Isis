#!/usr/bin/python3

import sys
import socket
import threading
import pickle
import total_ordering
import struct
import time
import hashlib
import math
import matplotlib.pyplot as plt


IN_CHANNELS = {}
OUT_CHANNELS = {}
IS_CONNECTED_TO_ALL_NODES = False
IS_LISTENING_TO_ALL_NODES = False
NODE_ID = None
NODE_INT_ID = None
PORT = None
LOCAL_HOST_NAME = '0.0.0.0'
MAX_NODE_COUNT = 50
timestamp = 0
message_ID_set = []
TotalOrdering = None
HEADER_SIZE = 5

IS_RECORDING = True
LOG_RECORDING_TIME = 200
LOGGER_START_TIME = None

graph_data = {"bandwidthInfo": [], "delayInfo": []}
node_lock = threading.Lock()

def start_node():
    global NODE_ID, NODE_NUMBER_ID, PORT, TotalOrdering, LOGGER_START_TIME
    NODE_ID, PORT, config_file = check_cl_args()
    NODE_NUMBER_ID = str(hash(NODE_ID) % (10 ** 8))
    nodeNumber, nodeInfos = read_config_file(config_file)
    lock = threading.Lock()
    TotalOrdering = total_ordering.TotalOrdering(unicast, multicast_message, NODE_ID, NODE_NUMBER_ID, nodeNumber, lock, record_message_time)
    LOGGER_START_TIME = time.time()
    threading.Thread(target=listen_to_nodes, args=(nodeNumber,)).start()
    threading.Thread(target=connect_to_nodes, args=(nodeInfos,)).start()
    while time.time() - LOGGER_START_TIME < LOG_RECORDING_TIME and IS_RECORDING:
        continue
    IS_RECORDING = False
    draw_graph()

def draw_graph():
    band_width_data = [0 for i in range(LOG_RECORDING_TIME)]
    delay_data = []
    graph_data["bandwidthInfo"].sort()
    for data in graph_data["bandwidthInfo"]:
        second_for_this_data = math.floor(data[0] - LOGGER_START_TIME)
        if second_for_this_data < len(band_width_data):
            band_width_data[second_for_this_data] += data[1]
    for i in range(LOG_RECORDING_TIME):
        band_width_data[i] = (band_width_data[i] * 8)
        print(band_width_data[i])

    fig1 = plt.figure(1)  # for bandwidth
    plt.title("Average Bandwidth Per Second")
    plt.xlabel("Second Since Start")
    plt.ylabel("Bandwidth/Bits Per Second")
    plt.plot(range(1, LOG_RECORDING_TIME + 1), band_width_data)
    figure = plt.gcf()
    figure.set_size_inches(12, 10)
    fig1.savefig('band_width_' + str(NODE_ID) + '_second.png')

    f = open("timeFile-"+NODE_ID+".txt", "w")
    for data in graph_data["delayInfo"]:
        text = str(data) + "\n"
        f.write(text)
    f.close()

def record_message_time(messageId, timeInterval):
    if IS_RECORDING:
        graph_data["delayInfo"].append((messageId, timeInterval))



def check_cl_args():
    if len(sys.argv) != 4:
        print("3 arguments needed: Node_Name Address Port")
        sys.exit()
    return sys.argv[1:]

def read_config_file(config_file):
    f = open(config_file, "r")
    nodeNumber = int(f.readline())
    nodeInfos = []
    for _ in range(nodeNumber):
        configInfo = f.readline().split(" ")
        configInfo[2] = configInfo[2].strip()
        nodeInfos.append(configInfo)
    return nodeNumber, nodeInfos

def connect_to_nodes(nodeInfos):
    for nodeInfo in nodeInfos:
        threading.Thread(target=connect_to_node, args=(nodeInfo,)).start()

    while len(OUT_CHANNELS) != len(nodeInfos):
        continue
    global IS_CONNECTED_TO_ALL_NODES
    IS_CONNECTED_TO_ALL_NODES = True
    while not IS_CONNECTED_TO_ALL_NODES or not IS_LISTENING_TO_ALL_NODES:
        continue
# all nodes connection setted up
# use isis to send user input messages
    TotalOrdering.ProposeMessages()


def connect_to_node(nodeInfo):
    s = socket.socket()
    while True:
        try:
            s.connect((nodeInfo[1], int(nodeInfo[2])))
            message = {"node_id": NODE_ID,}
            OUT_CHANNELS[nodeInfo[0]] = s
            s.sendall(pickle.dumps(message))
            break
        except Exception:
            pass
    return

def multicast_message(message, isFirstMulticast = True):
    global message_ID_set
    toSendPackage = message
    if isFirstMulticast:
        global timestamp
        toSendPackage = {"node_id": NODE_ID, "node_number_id": int(str(timestamp) + NODE_NUMBER_ID), "content": message}
        timestamp += 1
        message_ID_set.append(toSendPackage["node_number_id"])
    node_lock.acquire()
    for node in OUT_CHANNELS:
        unicast(toSendPackage, node)
    node_lock.release()

def unicast(message, nodeId, isUnicast = False):
    global graph_data
    if isUnicast:
        message["isUnicast"] = True
    toSendData = pickle.dumps(message)
    header = struct.pack('i', len(toSendData))
    try:
        OUT_CHANNELS[nodeId].sendall(header + toSendData)
        graph_data["bandwidthInfo"].append((time.time(), len(header) + len(toSendData)))
    except Exception:
        pass

def receive_message(client_data):
    global message_ID_set
    message = pickle.loads(client_data) 
    info = None
    if "node_number_id" not in message:
        info = message
    elif "isUnicast" in message:
        info = message["content"]
    elif message["node_number_id"] in message_ID_set:
        info = None
    else:
        message_ID_set.append(message["node_number_id"])
        multicast_message(message, False)
        info = message["content"]
    return info

def listen_to_nodes(expectedNodeNumber):
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 32*1024)
    s.bind((LOCAL_HOST_NAME, int(PORT)))
    s.listen(MAX_NODE_COUNT)
    for i in range(expectedNodeNumber):
        connection, address = s.accept()
        client_data = connection.recv(1024)
        if IS_RECORDING:
            graph_data["bandwidthInfo"].append((time.time(), len(client_data)))
        message = receive_message(client_data)
        IN_CHANNELS[message["node_id"]] = connection
    global IS_LISTENING_TO_ALL_NODES
    IS_LISTENING_TO_ALL_NODES = True
    while not IS_LISTENING_TO_ALL_NODES or not IS_CONNECTED_TO_ALL_NODES:
        continue
    for nodeId in IN_CHANNELS:
        threading.Thread(target=node_listening_handler, args=(IN_CHANNELS[nodeId], nodeId)).start()

def node_listening_handler(connection, nodeID):
    while True:
        received_time = time.time()
        header_struct = connection.recv(4) 
        if len(header_struct) < 1:
            print(received_time, "-", nodeID, "disconnected")
            TotalOrdering.nodeFailed(nodeID)
            OUT_CHANNELS.pop(nodeID)
            return
        unpack_res = struct.unpack('i',header_struct)
        size = unpack_res[0] 
        recv_size = 0
        total_data = b''
        while recv_size < size:
            recv_data = connection.recv(size - recv_size)
            if len(recv_data) < 1:
                print(received_time, "-", nodeID, "disconnected")
                TotalOrdering.nodeFailed(nodeID)
                OUT_CHANNELS.pop(nodeID)
                return 
            recv_size += len(recv_data)
            total_data += recv_data
        if IS_RECORDING:
            graph_data["bandwidthInfo"].append((time.time(), recv_size + 4))
        message = receive_message(total_data)
        if message:
            TotalOrdering.ReceiveMessage(message)

if __name__ == "__main__":
    start_node()
