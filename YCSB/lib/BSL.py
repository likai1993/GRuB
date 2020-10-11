#! /usr/bin/python3.6
import sys
sys.path.insert(0, "./lib")
from utils import process, process_scan, order_by_decision, trim_by_decision
from public_bkc import PublicSmartContract
from private_bkc import PrivateSmartContract
from pymerkletools import MerkleTools 

class BSL(object):
    def __init__(self, logfile, app_type, account_index=0, K=2):
        self.mt = MerkleTools()
        #self.SC = PublicSmartContract(account_index)
        self.SC = PrivateSmartContract(account_index)
        self.TXLogFile = logfile + '_BSL_NeverReplicate'
        self.TXLogFile = logfile + '_BSL_AlwaysReplicate'
        self.Contract_type = 'GRuB_Range_Query'

        if app_type == 'CT':
            #self.SC.get_contract_instance('./contracts/CT/Never_Replicate.sol', self.TXLogFile)
            self.SC.get_contract_instance('./contracts/CT/Always_Replicate.sol', self.TXLogFile)
            self.SC.set_callback_address('./contracts/CT/App_CT.sol')
        elif app_type == 'Token':
            #self.SC.get_contract_instance('./contracts/token/Never_Replicate.sol', self.TXLogFile)
            self.SC.get_contract_instance('./contracts/token/Always_Replicate.sol', self.TXLogFile)
            self.SC.set_callback_address('./contracts/token/App_Token.sol') 
        else:
            print('Unsupported application')
            sys.exit()

    def signature_verify(self, ct):
        return True

    # Interface for CT log
    def CT_log_update(self, domain_names, certs, w_index=0):
        for ct in certs:
            self.signature_verify(ct)
        self.Puts(domain_names, certs, w_index)

    def CT_log_read(self, domain_names, conditions):
        self.GetQ(domain_names, conditions) 

    # Interface for Token 
    def DO_transfer(self, senders, receivers, tokens, transfer_index = 0):
        uniq_senders = list(dict.fromkeys(senders))
        uniq_receivers = list(dict.fromkeys(receivers))
        balances = self.SC.log_parser('balance', self.GetQ(uniq_senders, ''), len(uniq_senders))
        print('Blockchain balance log:', balances)
        balances = {} 
        for key in uniq_senders: 
            balances[key] = self.mt.get_values(key) 
        for key in uniq_receivers: 
            balances[key] = self.mt.get_values(key) 
            
        print(balances)
        for sender in senders:
            balance = balances[sender]
            token = tokens[senders.index(sender)]
            while (balance < token ):
                print('Insufficient balance:', balance, 'transfering amount:', token, 'from:', sender, 'to:', receivers[senders.index(sender)])
                balances[sender] += token
                balance = balances[sender]
                #sys.exit(0) 
            balances[sender] -= token
            balances[receivers[senders.index(sender)]] += token
               
        return self.TokenPuts(senders, receivers, tokens, transfer_index)

    def DU_balanceOf(self, owners):
        return self.SC.log_parser('balance', self.GetQ(owners, ''), len(owners))

    def loading_state(self, addresses, balances):
        self.mt.insert_leaves(addresses, balances, False)

    # OnChain 
    def GetQ(self, keys, conditions):

        values = [self.mt.get_values(key) for key in keys ]
        indices = self.mt.get_indices_by_keys(keys)

        # call off-chain read
        print('Read:', keys)
        return self.SC.send_transactions(self.Contract_type, 2, [keys], len(keys), 'Read')

    def Puts(self, keys, values, w_index=0):
        values = self.mt.hash_leaves(values)
        # update the merkle tree
        self.mt.update_leaves(keys, values)
        indices = self.mt.get_indices_by_keys(keys)

        # upload the merkle root 
        self.SC.send_transactions(self.Contract_type, 4, [indices, values], len(keys), 'Write' + str(w_index))

    def TokenPuts(self, senders, receivers, amounts, transfer_index):
        # retrieve the balance 
        users = list(dict.fromkeys(senders + receivers))
        balances = {} 
        for user in users: 
            balances[user] = self.mt.get_values(user) 
        
        # update the balance 
        for i in range(len(amounts)):
            balances[senders[i]] -= amounts[i]
            balances[receivers[i]] += amounts[i]
        values = [balances[user] for user in users] 
        self.mt.update_leaves(users, values, False)

        # call write 
        return self.SC.send_transactions(self.Contract_type, 1, [users, values], len(users), 'transfer' + str(transfer_index))
'''
    # OffChain 
    def GetQ(self, keys, conditions):
        values = [self.mt.get_values(key) for key in keys ]
        indices = self.mt.get_indices_by_keys(keys)

        # call off-chain read
        print('Read:', indices)
        depth = self.mt.get_depth()
        root = self.mt.get_root()
        proof = self.mt.get_proof(indices)
        self.SC.send_transactions(self.Contract_type, 2, [keys, offChainValues, lastReplicateIndex, offChainKeysIndices, proof, depth], len(keys), 'R')
    
    def Puts(self, keys, values, w_index=0):
        values = self.mt.hash_leaves(values)
        # update the merkle tree
        self.mt.update_leaves(keys, values)
        indices = self.mt.get_indices_by_keys(keys)
        root = self.mt.get_root()
        print('new root:', root)

        # upload the merkle root 
        self.SC.send_transactions(self.Contract_type, 1, [root], len(keys), 'Write' + str(w_index))
'''
