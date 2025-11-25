from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
import random


class BB84:
    def __init__(self, n_qubits=32, eve_present=False, eve_probability=0.5):
        self.n = n_qubits
        self.eve_present = eve_present
        self.eve_probability = eve_probability
        self.sim = AerSimulator()

        # Generate random bits and bases
        self.alice_bits = [random.randint(0, 1) for _ in range(self.n)]
        self.alice_bases = [random.randint(0, 1) for _ in range(self.n)]
        self.bob_bases = [random.randint(0, 1) for _ in range(self.n)]

    def encode_qubits(self):
        """Alice is preparing qubits based on random bits and bases."""
        qubits = []

        for bit, basis in zip(self.alice_bits, self.alice_bases):
            qc = QuantumCircuit(1, 1)

            if bit == 1:
                qc.x(0)

            if basis == 1:
                qc.h(0)

            qubits.append(qc)

        return qubits

    def eve_intercept(self, qubit):
        """Eve optionally intercepts and measures the qubit."""
        if not self.eve_present or random.random() > self.eve_probability:
            return qubit, False

        eve_basis = random.randint(0, 1)
        qc = qubit.copy()

        if eve_basis == 1:
            qc.h(0)

        qc.measure(0, 0)
        result = self.sim.run(qc).result()
        measured_bit = int(max(result.get_counts(), key=result.get_counts().get))

        resend = QuantumCircuit(1, 1)
        if measured_bit == 1:
            resend.x(0)
        if eve_basis == 1:
            resend.h(0)

        return resend, True

    def bob_measure(self, qubit, basis):
        qc = qubit.copy()

        if basis == 1:
            qc.h(0)

        qc.measure(0, 0)
        result = self.sim.run(qc).result()
        counts = result.get_counts()
        return int(max(counts, key=counts.get))

    def run(self):
        prepared_qubits = self.encode_qubits()
        transmitted_qubits = []
        eve_flags = []

        for q in prepared_qubits:
            new_q, intercepted = self.eve_intercept(q)
            transmitted_qubits.append(new_q)
            eve_flags.append(intercepted)

        bob_results = [
            self.bob_measure(q, basis)
            for q, basis in zip(transmitted_qubits, self.bob_bases)
        ]

        sifted_key = [
            a for a, ab, bb in zip(self.alice_bits, self.alice_bases, self.bob_bases)
            if ab == bb
        ]
        sifted_bob = [
            b for ab, bb, b in zip(self.alice_bases, self.bob_bases, bob_results)
            if ab == bb
        ]

        errors = sum(a != b for a, b in zip(sifted_key, sifted_bob))
        qber = errors / max(len(sifted_key), 1)
        transcript = self.build_transcript(transmitted_qubits, bob_results, eve_flags)

        return {
            "alice_bits": self.alice_bits,
            "alice_bases": self.alice_bases,
            "bob_bases": self.bob_bases,
            "bob_results": bob_results,
            "key_alice": sifted_key,
            "key_bob": sifted_bob,
            "qber": qber,
            "transcript": transcript
        }
    
    def build_transcript(self, transmitted_qubits, bob_results, eve_flags):
        transcript = []
        for i in range(self.n):
            entry = {
                "index": i,
                "alice_bit": self.alice_bits[i],
                "alice_basis": self.alice_bases[i],
                "bob_basis": self.bob_bases[i],
                "bob_bit": bob_results[i],
                "eve_intercepted": eve_flags[i],
                "bases_match": self.alice_bases[i] == self.bob_bases[i],
                "error": (self.alice_bits[i] != bob_results[i]) and (self.alice_bases[i] == self.bob_bases[i])
            }
            transcript.append(entry)
        return transcript

if __name__ == "__main__":
    protocol = BB84(n_qubits=32, eve_present=True, eve_probability=0.6)
    result = protocol.run()

    print("\n--- BB84 Simulation ---")
    print("QBER:", result["qber"])
    print("Final Alice Key:", result["key_alice"])
    print("Final Bob Key:  ", result["key_bob"])
    for t in result["transcript"]:
        print(
            f"{t['index']:02d} | A_bit={t['alice_bit']} A_basis={t['alice_basis']} | "
            f"B_basis={t['bob_basis']} B_bit={t['bob_bit']} | "
            f"Eve={'YES' if t['eve_intercepted'] else 'NO '} | "
            f"Match={t['bases_match']} | Error={t['error']}"
        )