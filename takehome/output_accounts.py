import json
from AccountsController import AccountsController

#Initialize AccountsController

accounts_controller = AccountsController()

#Read input.txt file into program

input_file = open('input.txt', 'r')
json_lines = input_file.readlines()


#Initialize a load_id checker for customer deposits
load_id_json = {}

#Create a write to file output_amar.txt
with open('output_amar.txt', 'w') as outfile:
    for line in json_lines:
        customer_json = json.loads(line)
        customer_id = customer_json['customer_id']
        load_id = customer_json['id']
        if customer_id not in load_id_json:
            load_id_json[customer_id] = []
        #Do a check if load_id already exists for that specific customer
        if load_id in load_id_json[customer_id]:         
            continue
        else:
            json.dump(accounts_controller.processUserLoad(customer_json), outfile)
            outfile.write('\n')
            load_id_json[customer_id].append(load_id)



