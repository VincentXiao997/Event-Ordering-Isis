import bank_executor
import time

MESSAGE_TYPE = "MESSAGE_TYPE"
MESSAGE = "MESSAGE"
SUGGESTED_ID = "SUGGESTED_ID"
DELIVERABLE = "DELIVERABLE"
TIMEOUT_THRASHOLD = 5

DEBUG = False

class Message:
	def __init__(self, content, messageId, nodeId):
		self.content = content
		self.messageId = messageId
		self.nodeId = nodeId
		self.queue = []
		self.repliedNodes = []
		self.isDeliverable = False
		self.queue.append(messageId)

class TotalOrdering:
	def __init__(self, unicast, multicast, nodeId, nodeIntId, nodeNumber, lock, recordMessagetTime):
		self.f = open(nodeId + ".txt", "a")
		self.multicast = multicast
		self.unicast = unicast
		self.nodeId = nodeId
		self.nodeIntId = str(nodeIntId)
		self.timestamp = 1
		self.nodeNumber = nodeNumber
		self.messageList = {}
		self.messageQueue = []
		self.executor = bank_executor.BankExecutor()
		self.failedNodes = {}
		self.lock = lock
		self.recordMessagetTime = recordMessagetTime
		self.executedMessageIds = []
		self.existedMessageIds = []

	def nodeFailed(self, nodeId):
		self.failedNodes[nodeId] = time.time()

	def ProposeMessages(self):
		while True:
			userInput = input()
			messageId = self.__getMessageId()
			self.timestamp += 1
			message = { MESSAGE_TYPE: MESSAGE,
					   "message_id": messageId,
					   "content": userInput,
					   "node_id": self.nodeId}
			self.lock.acquire()
			if DEBUG:
				print(self.nodeId, "propose", messageId)
			self.multicast(message)
			self.messageList[messageId] = Message(message["content"], messageId, self.nodeId)
			self.messageQueue.append((messageId, messageId))
			self.messageQueue.sort()
			self.existedMessageIds.append(messageId)
			if len(self.messageList) != len(self.messageQueue):
				print("line 56")
				print(len(self.messageList))
				print(len(self.messageQueue))
			self.lock.release()

	def __checkTimeoutMessages(self):

		timestamp = time.time()
		removableMessageIds = []
		removableMessagesQueueInfo = []
		removableNodeIds = []
		self.lock.acquire()
		for nodeId in self.failedNodes:
			if timestamp - self.failedNodes[nodeId] > TIMEOUT_THRASHOLD:
				for messageId in self.messageList:
					if self.messageList[messageId].nodeId == nodeId and \
					   not self.messageList[messageId].isDeliverable:
						removableMessageIds.append(messageId)
				for messageInfo in self.messageQueue:
					if messageInfo[1] in removableMessageIds:
						removableMessagesQueueInfo.append(messageInfo)
						# print("remove", messageInfo[1])
						self.messageList.pop(messageInfo[1])
				for messageInfo in removableMessagesQueueInfo:
					self.messageQueue.remove(messageInfo)
				removableNodeIds.append(nodeId)
				self.nodeNumber -= 1
		isRemovedNode = False
		for nodeId in removableNodeIds:
			self.failedNodes.pop(nodeId)
			isRemovedNode = True
		self.lock.release()
		if isRemovedNode:
			deliverableMessageIds = []
			for messageId in self.messageList:
				if len(self.messageList[messageId].repliedNodes) == self.nodeNumber and \
				   not self.messageList[messageId].isDeliverable:
					deliverableMessageIds.append(messageId)
			for messageId in deliverableMessageIds:
				self.__sendDeliverableMessage(messageId)

	def ReceiveMessage(self, message):
		
		self.__checkTimeoutMessages()
		
		if message[MESSAGE_TYPE] == MESSAGE:
			# send suggested id
			self.__receiveProposedMessage(message)
		elif message[MESSAGE_TYPE] == SUGGESTED_ID:
			# add to message queue, send deliverable message when all processes replyed
			self.__receiveSuggestedId(message)
		elif message[MESSAGE_TYPE] == DELIVERABLE:
			# add message to queue, exceuate it when it is the first message			
			self.__receiveDeliverableMessage(message)
		else:
			print("*****************************")
			print(message)
			print("*****************************")

	def __getMessageId(self):
		return float(str(self.timestamp) + "." + self.nodeIntId)

	def __receiveProposedMessage(self, message):
		self.lock.acquire()
		messageId = self.__getMessageId()
		self.timestamp += 1
		if message["message_id"] in self.existedMessageIds:
			self.lock.release()
			return
		if message["message_id"] in self.executedMessageIds:
			self.lock.release()
			return
		if message["message_id"] not in self.messageList:
			newMessage = { MESSAGE_TYPE: SUGGESTED_ID,
						"message_id": message["message_id"],
						"content": messageId,
						"node_id": message["node_id"],
						"from_node": self.nodeId}
			self.unicast(newMessage, message["node_id"], True)
			if DEBUG:
				print("send suggest", message["message_id"], messageId, message["node_id"])
			self.messageList[message["message_id"]] = Message(message["content"], message["message_id"], message["node_id"])
			if message["message_id"] not in self.messageList:
				print("132 ERROR &&&&&&&&&& ", message["message_id"], "not in self.messageList")
			self.messageQueue.append((messageId, message["message_id"]))
			self.messageQueue.sort()
			
			if len(self.messageList) != len(self.messageQueue):
				print("line 130")
				print(len(self.messageList))
				print(len(self.messageQueue))
				print(message)
				toRemove = None
				for info in self.messageQueue:
					if info[1] == message["message_id"]:
						print(info)
						toRemove = info
				if info:
					self.messageQueue.remove(info) 
		self.lock.release()

	def __receiveSuggestedId(self, message):
		messageId = message["message_id"]
		suggestedId = message["content"]
		fromNodeId = message['from_node']
		if messageId not in self.messageList:
			return
		self.lock.acquire()
		if DEBUG:
			print(fromNodeId, "suggested", messageId, suggestedId)
		self.messageList[messageId].queue.append(suggestedId)
		self.messageList[messageId].queue.sort()
		self.messageList[messageId].repliedNodes.append(fromNodeId)
		if len(self.messageList) != len(self.messageQueue):
			print("line 55")
			print(len(self.messageList))
			print(len(self.messageQueue))
		failedNodeNumber = len(self.failedNodes)
		for failedNodeId in self.failedNodes:
			if failedNodeId in self.messageList[messageId].repliedNodes:
				failedNodeNumber -= 1
		self.lock.release()
		if len(self.messageList[messageId].queue) >= (self.nodeNumber + 1 - failedNodeNumber):
			# print(messageId, len(self.messageList[messageId].queue), self.nodeNumber + 1, failedNodeNumber)
			self.__sendDeliverableMessage(messageId)

	def __sendDeliverableMessage(self, messageId):
		messageObject = self.messageList[messageId]
		deliverableId = messageObject.queue.pop()
		message = {
			MESSAGE_TYPE: DELIVERABLE,
			"message_id": messageId,
			"content": deliverableId,
			"node_id": self.nodeId
		}
		self.lock.acquire()
		self.recordMessagetTime(deliverableId, time.time())
		self.multicast(message)
		if DEBUG:
			print("send deliverableId", messageId, deliverableId)
		messageObject.isDeliverable = True
		deliveredMessageIdInfo = None
		for messageIdInfo in self.messageQueue:
			if messageIdInfo[1] == messageId:
				deliveredMessageIdInfo = messageIdInfo
				break
		if deliveredMessageIdInfo == None:
			print("line 204")
			print(messageId)
			print(message)
			return

		self.messageQueue.remove(deliveredMessageIdInfo)
		self.messageQueue.append((deliverableId, messageId))
		self.messageQueue.sort()
		if len(self.messageList) != len(self.messageQueue):
			print("line 189")
			print(len(self.messageList))
			print(len(self.messageQueue))
		self.lock.release()
		self.__checkDeliverableMessages()

	def __checkDeliverableMessages(self):
		# print("check deliverable id")
		# print(self.messageQueue[0])
		# testid = self.messageQueue[0][1]
		# print(self.messageList[testid].nodeId, self.messageList[testid].repliedNodes)
		self.lock.acquire()
		self.messageQueue.sort()

		while len(self.messageQueue) > 0 and self.messageList[self.messageQueue[0][1]].isDeliverable:

			if DEBUG:
				print("213", "len check", len(self.messageList), len(self.messageQueue))

			message = self.messageList.pop(self.messageQueue[0][1])

			if DEBUG:
				print("*********************execute ", self.messageQueue[0][1])
			self.messageQueue.pop(0)
			self.executedMessageIds.append(message.messageId)
			if len(self.messageList) != len(self.messageQueue):
				print("line 207")
				print(len(self.messageList))
				print(len(self.messageQueue))
			self.__execuateCommand(message.content)
		self.lock.release()

	def __execuateCommand(self, command):
		if not DEBUG:
			self.executor.execuateCommand(command)

	def __receiveDeliverableMessage(self, message):
		messageId = message["message_id"]
		deliverableId = message["content"]

		self.lock.acquire()
		if messageId not in self.messageList:
			self.lock.release()
			return
		self.messageList[messageId].isDeliverable = True
		deliveredMessageIdInfo = None
		for messageIdInfo in self.messageQueue:
			if messageIdInfo[1] == messageId:
				deliveredMessageIdInfo = messageIdInfo
				break
		self.recordMessagetTime(messageId, time.time())
		# if len(self.messageList) != len(self.messageQueue) or deliveredMessageIdInfo == None:
		# print("line 229")
		# print(len(self.messageList))
		# print(len(self.messageQueue))
		# print(messageId, deliveredMessageIdInfo)
		self.messageQueue.remove(deliveredMessageIdInfo)
		self.messageQueue.append((deliverableId, messageId))
		self.messageQueue.sort()
		if len(self.messageList) != len(self.messageQueue):
			print("line 232")
			print(len(self.messageList))
			print(len(self.messageQueue))
		self.lock.release()
		self.__checkDeliverableMessages()





