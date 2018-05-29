import hashlib
import json
import time
import uuid
from urllib.parse import urlparse

from flask import json, Flask, jsonify, request


class Blockchain:

    def __init__(self):
        self.chain = []
        self.current_transactions = []
        self.nodes = set()
        # genesis block
        self.new_block(1, '1')

    def new_block(self, proof, previous_hash=None):
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time.time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.last_block)
        }
        self.current_transactions = []
        self.chain.append(block)
        return block

    def new_transaction(self, sender, recipient, amount):
        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount
        })
        return self.last_block['index'] + 1

    @staticmethod
    def hash(block):
        block_bytes = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_bytes).hexdigest()

    @property
    def last_block(self):
        return self.chain[-1]

    def proof_of_work(self, last_proof):
        proof = 0
        while not self.valid_proof(last_proof, proof):
            proof += 1
        return proof

    @staticmethod
    def valid_proof(last_proof, proof):
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash.startswith('0000')

    def register_node(self, address):
        self.nodes.add(urlparse(address).netloc)


app = Flask(__name__)
blockchain = Blockchain()
node_id = str(uuid.uuid4()).replace('-', '')


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    data = request.get_json()
    required = ['sender', 'recipient', 'amount']
    if not request or not all(key in data for key in required):
        return 'require: ' + ', '.join(required), 400
    index = blockchain.new_transaction(data['sender'], data['recipient'], data['amount'])
    return jsonify({'message': f'Your transaction will be added to block {index}'})


@app.route('/mine')
def mine():
    last_block = blockchain.last_block
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work(last_proof)
    blockchain.new_transaction('0', node_id, 1)
    block = blockchain.new_block(proof)
    res = {
        'message': 'New Block Forged',
        'index': block['index'],
        'transactions': block['transactions'],
        'previous_hash': block['previous_hash'],
        'proof': block['proof'],
    }
    return jsonify(res)


@app.route('/chain')
def full_chain():
    res = {'chain': blockchain.chain, 'length': len(blockchain.chain)}
    return jsonify(res)


@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    data = request.get_json()
    nodes = data.get('nodes')
    if not nodes:
        return 'Nodes not found!', 400
    for node in nodes:
        blockchain.register_node(node)
    res = {'message': 'New node added', 'total_nodes': list(blockchain.nodes)}
    return jsonify(res), 201


if __name__ == '__main__':
    app.run()
