transactions = []


def createSumLog(invoker, data, contract_id):
    return lib["Transaction"](contract_id, {
        "logger": invoker,
        "result": data["var_1"] + data["var_2"],
        "contract_id": contract_id,
        "timestamp": timestamp
    })


tx = createSumLog(invoker, data, contract_id)

transactions.append(tx)
