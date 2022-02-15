transactions = []
try:
    if state["updated"] == True:
        transactions.append(lib["Transaction"](invoker))
except:
    pass
