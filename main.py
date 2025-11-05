from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
import random

n = 8
alice_bits = [random.randint(0, 1) for _ in range(n)]
alice_bases = [random.randint(0, 1) for _ in range(n)]

bob_bases = [random.randint(0, 1) for _ in range(n)]

qubits = []
for bit, basis in zip(alice_bits, alice_bases):
    qc = QuantumCircuit(1, 1)
    
    # Encode bit
    if bit == 1:
        qc.x(0)
        
    # Encode basis
    if basis == '1':
        qc.h(0)
        
    # Store for transmission
    qubits.append(qc)

simulator = AerSimulator()
bob_results = []

for i in range(n):
    qc = qubits[i].copy()
    
    if bob_bases[i] == '1':
        qc.h(0)
    
    qc.measure(0, 0)
    
    # Run simulation
    result = simulator.run(qc).result()
    counts = result.get_counts()
    measured_bit = int(max(counts, key=counts.get))
    bob_results.append(measured_bit)

key = [a for a, ab, bb, b in zip(alice_bits, alice_bases, bob_bases, bob_results) if ab == bb]

print("Alice bits:   ", alice_bits)
print("Alice bases:  ", alice_bases)
print("Bob bases:    ", bob_bases)
print("Bob results:  ", bob_results)
print("Final key:    ", key)