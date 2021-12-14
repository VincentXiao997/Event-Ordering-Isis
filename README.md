# Isis Algorithm for Total Ordering

It is often useful to ensure that we can have a global ordering of events across processes to perform consistent actions across all processes. In this project, events are transactions that move money between accounts. Each node used TCP connections to communicate to other nodes. It used **Isis** algorithm to maintain the total ordering of transactions in each server account balance, and use order to decide which of the transactions are successful.

Note that in an asynchronous system, it is impossible to know for sure which of two events happened first. Therefore, we used a totally ordered multicast to ensure the ordering. We also detected and handled the potential failure of any of the nodes in the system.

## Usage

### Start nodes

To start node, simple type:
```sh
./node {node id} {port} {config file}
```

The total number of nodes and all other nodes info should be registered into the config file:

```sh
2
node2 IP_ADDRESS PORT
node3 IP_ADDRESS PORT
```

### Operations

We support three operations:

```sh
DEPOSIT wqkby 10
DEPOSIT yxpqg 75
TRANSFER yxpqg -> wqkby 13
```

**DEPOSIT** would add the amount of money into the account. If the account doesn't exist, the account would be created automatically.

"**TRANSFER** ACCOUNT_A -> ACCOUNT_B" would delete the amount of money from the ACCOUNT_A and add it to ACCOUNT_B. 

After each operation, it will print out the balance for each account. 

There may be a delay in the execution of the operation, depending on the delay of the transmission and the amount of concurrency of the message. An operation will be executed only when all nodes admit it as the latest operation. This is achieved by the Isis algorithm.