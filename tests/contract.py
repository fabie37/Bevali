"""
    File Logger Smart Contract: 

    Global:

        lib : {
            "Transaction" : Transaction ~ Gives the contract the ability to create a new transaction
            "ContractCreateTransaction" : ContractCreateTransaction ~ Gives the contract the ability to create a contract
            "ContractInvokeTransaction" : ContractInvokeTransaction ~ Gives the contract the ability to invoke another contract
            "ContractUpdateTransaction" : ContractUpdateTransaction ~ Gives the contract the ability to update it's state
        }

        blockchain ~ gives access to the state of blockchain when executed
        state ~ gives the current state of the contract
            {
                "permissions_list" : [...] ~ list of user ids who can log this contract
                "files_in_circulation" : Default 1 updated after a send or delete command
            }

        memory ~ gives the contracts memory defined on creation
        contract_id ~ gives the id of the running contract
        creator ~ gives the id of the user who created the contract
        invoker ~ gives the id of the user who invoked the contract
        timestamp ~ gives the timestamp of the invocation
        data ~ data passed from user to contract


    Attributes:
        id  ~ Defines a file's unique ID (Stored in memory attribute)
        [access] ~ Defines a list of users who are allowed to operate on this file (stored in state attribute)

    Operations (found in data attribute of invocation):
        file_edit ~ Logs that a particular user edited this file
        file_delete ~ Logs that a user deleted this file
        file_send ~ Logs that a user sent this file to another
        update_access ~ Updates who is allowed to access file

    Return:
        LogTransaction::Transaction

            This is a normal transaction that holds the log of a users action.
            This has the format
                data = {
                    "type" : "log"
                    "logger" : invoker
                    "action" : "edit" | "delete" | "send" | "addUser"
                    "to" : invoker | recepient
                    "contract_id" : contract_id
                    "timestamp" : timestamp
                }
        
        StateUpdateTransaction::ContractUpdateTransaction

            This can only be returned by the contract given special permissions
            This has the format
                data = {
                    "permission_list"  = [...] ~ list of user ids
                    "files_in_circulation" = Default: 1  ~ updated after a send or delete command
                }
        
        ViolationTransaction::Transaction

            This transaction is produced when a user tries to log a file they should not
            have access to (see permission_list)
            This has the format
                data = {
                    "type" : "violation log"
                    "logger" : invoker
                    "action" : "edit" | "delete" | "send" | "addUser"
                    "to" : invoker | recepient
                    "contract_id" : contract_id
                    "timestamp" : timestamp
                }

        Inputs:

        Edit Logs:
            Send a Invoke Transaction to:
                contract_id
                data = {
                    "action" : "edit",
                    "to" : invoker ~ the peer seending the transaction
                }
        
        Delete Logs:
            Send a Invoke Transaction to:
                contract_id
                data = {
                    "action" : "delete",
                    "to" : invoker ~ the peer seending the transaction
                }

        Send Logs:
            Send a Invoke Transaction to:
                contract_id
                data = {
                    "action" : "send",
                    "to" : receipent ~ the peer who wishes to get the file
                }
        
        Update State
            Send a Invoke Transaction to:
                contract_id
                data = {
                    "action" : "addUser",
                    "user" : userId ~ the peer who wishes to be able to log file without
                                      altering the system.
                }


"""
transactions = []


def createLog(type, invoker, data, contract_id):
    return lib["Transaction"](contract_id, {
        "type": type,
        "logger": invoker,
        "action": data["action"],
        "to": data["to"],
        "contract_id": contract_id,
        "timestamp": timestamp
    })


def updateState(invoker, contract_id, name_of_state, new_val):
    new_state = {name_of_state: new_val}
    return lib["ContractUpdateTransaction"](invoker, contract_id, new_state)


# 1) First check if logger even have permissions to file
if invoker not in state["permission_list"]:
    violationLog = createLog("violation log", invoker, data, contract_id)
    transactions.append(violationLog)
else:
    if state["files_in_circulation"] >= 1 and data["action"] != "addUser":
        # 2) If logger is just editing a file
        if data["action"] == "edit":
            editLog = createLog("log", invoker, data, contract_id)
            transactions.append(editLog)
        # 3) If logger is deleting a file
        elif data["action"] == "delete":
            deleteLog = createLog("log", invoker, data, contract_id)
            transactions.append(deleteLog)
            updateFilesInCirculation = updateState(
                invoker, contract_id, "files_in_circulation", state["files_in_circulation"] - 1)
            transactions.append(updateFilesInCirculation)
        # 4) if logger is sending a file
        elif data["action"] == "send":
            if data["to"] not in state["permission_list"]:
                violationLog = createLog(
                    "violation log", invoker, data, contract_id)
                transactions.append(violationLog)
            else:
                sendLog = createLog("log", invoker, data, contract_id)
            updateFilesInCirculation = updateState(
                invoker, contract_id, "files_in_circulation", state["files_in_circulation"] + 1)
            transactions.append(updateFilesInCirculation)
    # 5) If user not logging any data, but instead, extending permissions - add them to smart contract
    #    permission list.
    elif data["action"] == "addUser":
        if isinstance(state["permission_list"], list):
            newList = state["permission_list"] + [data["user"]]
        else:
            newList = [state["permission_list"], data["user"]]
        newState = updateState(invoker, contract_id,
                               "permission_list", newList)
        transactions.append(newState)
