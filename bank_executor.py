COMMAND_DEPOSIT = "DEPOSIT"
COMMAND_TRANSFER = "TRANSFER"
BALANCES = "BALANCES"

class BankAccount:
	def __init__(self, name, deposit):
		self.deposit = deposit
		self.name = name

	def deposit(self, deposit):
		self.deposit += deposit

	def transfer(self, amount):
		if amount <= self.deposit:
			self.deposit -= amount

class BankExecutor:
	def __init__(self):
		self.accounts = {}

	def execuateCommand(self, command):
		print(command)
		command = command.split(" ")
		if command[0] == COMMAND_DEPOSIT:
			if command[1] in self.accounts:
				self.accounts[command[1]].deposit += int(command[2])
			else:
				self.accounts[command[1]] = BankAccount(command[1], int(command[2]))
		elif command[0] == COMMAND_TRANSFER:
			if command[1] not in self.accounts:
				return
			elif self.accounts[command[1]].deposit < int(command[4]):
				return
			else:
				self.makeDeposit(command[1], -1 * int(command[4]))
				self.makeDeposit(command[3], int(command[4]))
				self.__printAccountsInfo()

	def makeDeposit(self, name, amount):
		if name in self.accounts:
			self.accounts[name].deposit += amount
		else:
			self.accounts[name] = BankAccount(name, amount)


	def __printAccountsInfo(self):
		accountInfoStr = BALANCES
		accountNames = list(self.accounts.keys())
		accountNames.sort()
		for accountName in accountNames:
			accountInfoStr += " {}:{}".format(accountName, self.accounts[accountName].deposit)
		print(accountInfoStr) 