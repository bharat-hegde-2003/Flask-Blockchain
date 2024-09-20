import hashlib
import time
import json

class Blockchain:
    def __init__(self, difficulty=4):
        self.chain = []
        self.current_transactions = []
        self.difficulty = difficulty

        # Create the genesis block
        self.new_block(proof=100, previous_hash=self.hash({'genesis': True}))

    def new_transaction(self, name, method, amount, card_num, date, action):
        transaction = {
            'name': name,
            'method': method,
            'amount': amount,
            'card_num': card_num,
            'date': date,
            'action': action,
        }
        self.current_transactions.append(transaction)
        return self.last_block['index'] + 1 if self.last_block else 1

    def new_block(self, proof, previous_hash=None):
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time.time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }
        self.chain.append(block)
        self.current_transactions = []  # Clear current transactions
        return block

    def proof_of_work(self, last_proof):
        proof = 0
        while not self.valid_proof(last_proof, proof):
            proof += 1
        return proof

    def valid_proof(self, last_proof, proof):
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:self.difficulty] == "0" * self.difficulty

    def hash(self, block):
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self):
        return self.chain[-1] if self.chain else None

    def is_valid_chain(self, chain):
        for i in range(1, len(chain)):
            last_block = chain[i - 1]
            current_block = chain[i]

            if current_block['previous_hash'] != self.hash(last_block):
                return False

            if not self.valid_proof(last_block['proof'], current_block['proof']):
                return False
        return True

    def get_all_blocks(self):
        return self.chain

    @staticmethod
    def get_peers():
        return []

    def get_last_block(self):
        return self.last_block
