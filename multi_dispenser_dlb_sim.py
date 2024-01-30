import time
import random
from paho.mqtt import client as mqtt_client
import logging


mode = 2                        # 0 - Equal mode, 1 - FIFO mode, 2 - Fast Lane mode
totoalNumberOfModules = 12
balanceNumberOfModules = 12
totalNumberOfDispensers = 4
fastLaneNumber = 2
numberOfModulesForFastLane = 8

priorityList = [] * totalNumberOfDispensers
assignedList = [0] * totalNumberOfDispensers
dedicatedList = [0] * totalNumberOfDispensers
# print(dedicatedList)

# demandVoltageList = [0, 0, 0, 0, 0, 0]
# demandCurrentList = [0, 0, 0, 0, 0, 0]
dispenserDemandList = [0] * totalNumberOfDispensers

broker = 'localhost'
port = 1883
pubTopicAssigned = "topicAssignedList"
pubTopicPriority = "topicPriorityList"
pubTopicMode = "topicMode"
topicD0 = "topicD0"
topicD1 = "topicD1"
topicD2 = "topicD2"
topicD3 = "topicD3"
topicD4 = "topicD4"
topicD5 = "topicD5"
client_id = f'publish-{random.randint(0, 1000)}'

################################################################################################################################ MQTT CONNECT
def connect_mqtt():
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)

    client = mqtt_client.Client(client_id)
    # client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client
################################################################################################################################

FIRST_RECONNECT_DELAY = 1
RECONNECT_RATE = 2
MAX_RECONNECT_COUNT = 12
MAX_RECONNECT_DELAY = 60

################################################################################################################################ MQTT ON DISCONNECT
def on_disconnect(client, userdata, rc):
    logging.info("Disconnected with result code: %s", rc)
    reconnect_count, reconnect_delay = 0, FIRST_RECONNECT_DELAY
    while reconnect_count < MAX_RECONNECT_COUNT:
        logging.info("Reconnecting in %d seconds...", reconnect_delay)
        time.sleep(reconnect_delay)

        try:
            client.reconnect()
            logging.info("Reconnected successfully!")
            return
        except Exception as err:
            logging.error("%s. Reconnect failed. Retrying...", err)

        reconnect_delay *= RECONNECT_RATE
        reconnect_delay = min(reconnect_delay, MAX_RECONNECT_DELAY)
        reconnect_count += 1
        logging.info("Reconnect failed after %s attempts. Exiting...", reconnect_count)
################################################################################################################################

################################################################################################################################ MQTT PUBLISH
def publish(client, msg, topic):
    result = client.publish(topic, msg)
    # result: [0, 1]
    status = result[0]
    if status == 0:
        print(f"Send `{msg}` to topic `{topic}`")
    else:
        print(f"Failed to send message to topic {topic}")
################################################################################################################################

################################################################################################################################ MQTT SUBSCRIBE
def subscribe(client: mqtt_client):
    def on_message(client, userdata, msg):
        print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")
        if msg.topic == "topicD0":
            dispenserDemandList[0] = int(msg.payload.decode())
        elif msg.topic == "topicD1":
            dispenserDemandList[1] = int(msg.payload.decode())
        elif msg.topic == "topicD2":
            dispenserDemandList[2] = int(msg.payload.decode())
        elif msg.topic == "topicD3":
            dispenserDemandList[3] = int(msg.payload.decode())
        elif msg.topic == "topicD4":
            dispenserDemandList[4] = int(msg.payload.decode())
        elif msg.topic == "topicD5":
            dispenserDemandList[5] = int(msg.payload.decode())

    client.subscribe(topicD0)
    client.subscribe(topicD1)
    client.subscribe(topicD2)
    client.subscribe(topicD3)
    client.subscribe(topicD4)
    client.subscribe(topicD5)

    client.on_message = on_message
################################################################################################################################

client = connect_mqtt()
client.on_disconnect = on_disconnect
subscribe(client)
client.loop_start()

while 1:

    ################################################################################################################################ GET THE DEMAND
    # dispenserDemandList[0] = input("Demand at dispenser 0: ")
    # dispenserDemandList[0] = int(dispenserDemandList[0])
    # dispenserDemandList[1] = input("Demand at dispenser 1: ")
    # dispenserDemandList[1] = int(dispenserDemandList[1])
    # dispenserDemandList[2] = input("Demand at dispenser 2: ")
    # dispenserDemandList[2] = int(dispenserDemandList[2])
    # dispenserDemandList[3] = input("Demand at dispenser 3: ")
    # dispenserDemandList[3] = int(dispenserDemandList[3])
    # dispenserDemandList[4] = input("Demand at dispenser 4: ")
    # dispenserDemandList[4] = int(dispenserDemandList[4])
    # dispenserDemandList[5] = input("Demand at dispenser 5: ")
    # dispenserDemandList[5] = int(dispenserDemandList[5])
    ################################################################################################################################

    ################################################################################################################################ CREATE PRIORITY LIST
    for i in range(totalNumberOfDispensers):
        if dispenserDemandList[i] != 0:
            if i in priorityList:
                pass
            else:
                priorityList.append(i)
        elif dispenserDemandList[i] == 0:
            if i in priorityList:
                priorityList.remove(i)
    ################################################################################################################################

    ################################################################################################################################ EDIT DEDICATED LIST
    if mode == 0: # Equal mode
        if (len(priorityList)):
            dedicatedList = [0] * totalNumberOfDispensers
            for dispenserNumber in priorityList:
                dedicatedList[dispenserNumber] = int(totoalNumberOfModules/len(priorityList))
    elif mode == 1: # FIFO
        dedicatedList = [1] * totalNumberOfDispensers
    elif mode == 2: # Fast Lane
        if (len(priorityList)):
            dedicatedList = [0] * totalNumberOfDispensers
            for dispenserNumber in priorityList:
                if dispenserNumber == fastLaneNumber:
                    dedicatedList[dispenserNumber] = numberOfModulesForFastLane
                elif fastLaneNumber in priorityList:
                    dedicatedList[dispenserNumber] = int((totoalNumberOfModules - numberOfModulesForFastLane) / (len(priorityList) - 1))
                else:
                    dedicatedList[dispenserNumber] = int((totoalNumberOfModules - numberOfModulesForFastLane) / len(priorityList))
    ################################################################################################################################

    balanceNumberOfModules = 12
    assignedList = [0] * totalNumberOfDispensers

    ################################################################################################################################ ASSIGN LESS THAN DEDICATED
    for dispenserNumber in priorityList:
        if dispenserDemandList[dispenserNumber] <= dedicatedList[dispenserNumber]:
            assignedList[dispenserNumber] = dispenserDemandList[dispenserNumber]
            balanceNumberOfModules = balanceNumberOfModules - assignedList[dispenserNumber]
    ################################################################################################################################

    ################################################################################################################################ ASSIGN DEDICATED 
    for dispenserNumber in priorityList:
        if dispenserDemandList[dispenserNumber] > dedicatedList[dispenserNumber]:
            assignedList[dispenserNumber] = dedicatedList[dispenserNumber]
            balanceNumberOfModules = balanceNumberOfModules - assignedList[dispenserNumber]
    ################################################################################################################################

    ################################################################################################################################ ASSIGN EXTRA
    if ((mode == 0 or mode == 2) and len(priorityList)): # Equal mode and Fast Lane

        if (mode == 2):
            if fastLaneNumber in priorityList:
                priorityList.remove(fastLaneNumber)
                priorityList.append(fastLaneNumber)

        numberOfDispensersThatRequireExtraModules = 0
        for dispenserNumber in priorityList:
            if dispenserDemandList[dispenserNumber] > dedicatedList[dispenserNumber]:
                numberOfDispensersThatRequireExtraModules = numberOfDispensersThatRequireExtraModules + 1

        n = 0
        tempPriorityList = priorityList.copy()
        dispenserNumber = tempPriorityList[n]
        numberOfDispensersThatGotExtraModules = 0
        while (balanceNumberOfModules > 0):
            if dispenserDemandList[dispenserNumber] > dedicatedList[dispenserNumber]:
                if dispenserDemandList[dispenserNumber] > assignedList[dispenserNumber]:
                    assignedList[dispenserNumber] = assignedList[dispenserNumber] + 1
                    balanceNumberOfModules = balanceNumberOfModules - 1
                elif dispenserDemandList[dispenserNumber] == assignedList[dispenserNumber]:
                    numberOfDispensersThatGotExtraModules = numberOfDispensersThatGotExtraModules + 1
                    tempPriorityList.remove(dispenserNumber)

            if numberOfDispensersThatRequireExtraModules == numberOfDispensersThatGotExtraModules:
                break

            n = n + 1
            if n >= len(tempPriorityList):
                n = 0
            dispenserNumber = tempPriorityList[n]
    ################################################################################################################################
    elif mode == 1: # FIFO
        for dispenserNumber in priorityList:
            if dispenserDemandList[dispenserNumber] > dedicatedList[dispenserNumber]:
                if balanceNumberOfModules > 0:
                    if balanceNumberOfModules >= (dispenserDemandList[dispenserNumber] - dedicatedList[dispenserNumber]):
                        assignedList[dispenserNumber] = assignedList[dispenserNumber] + (dispenserDemandList[dispenserNumber] - dedicatedList[dispenserNumber])
                        balanceNumberOfModules = balanceNumberOfModules - (dispenserDemandList[dispenserNumber] - dedicatedList[dispenserNumber])

                    elif balanceNumberOfModules < (dispenserDemandList[dispenserNumber] - dedicatedList[dispenserNumber]):
                        assignedList[dispenserNumber] = assignedList[dispenserNumber] + balanceNumberOfModules
                        balanceNumberOfModules = 0
    ################################################################################################################################

    ################################################################################################################################

    publish(client, ",".join(map(str, assignedList)), pubTopicAssigned)  # converted to string
    publish(client, ",".join(map(str, priorityList)), pubTopicPriority)
    if mode == 0:
        publish(client, "Equal Mode", pubTopicMode)
    elif mode == 1:
        publish(client, "FIFO Mode", pubTopicMode)
    elif mode == 2:
        txt = "Fast Lane Mode at Dispenser " + str(fastLaneNumber)
        publish(client, txt, pubTopicMode)

    print("Dedicated List: ", dedicatedList)
    print("Priority List: ", priorityList)
    print("Assigned List: ", assignedList)
    print("Balance Number Of Modules: ", balanceNumberOfModules)
    print()

    time.sleep(0.3)