#!/usr/bin/env python

import sys


class Assembler(object):

    comp_table = {
        "0":   "0101010", "1":   "0111111", "-1":  "0111010",
        "D":   "0001100", "A":   "0110000", "M":   "1110000",
        "!D":  "0001101", "!A":  "0110001", "!M":  "1110001",
        "-D":  "0001111", "-A":  "0110011", "-M":  "1110011",
        "D+1": "0011111", "A+1": "0110111", "M+1": "1110111",
        "D-1": "0001110", "A-1": "0110010", "M-1": "1110010",
        "D+A": "0000010", "D+M": "1000010", "D-A": "0010011",
        "D-M": "1010011", "A-D": "0000111", "M-D": "1000111",
        "D&A": "0000000", "D&M": "1000000", "D|A": "0010101",
        "D|M": "1010101", None:  "0000000",
    }

    jump_table = {
        None:  "000", "JGT": "001", "JEQ": "010", "JGE": "011",
        "JLT": "100", "JNE": "101", "JLE": "110", "JMP": "111",
    }

    dest_table = {
        None:  "000", "M":   "001", "D":   "010", "MD":  "011",
        "A":   "100", "AM":  "101", "AD":  "110", "ADM": "111",
    }

    predefined_symbols = {
        "R0":  "0", "R1":  "1", "R2":  "2", "R3":  "3", "R4":  "4",
        "R5":  "5", "R6":  "6", "R7":  "7", "R8":  "8", "R9":  "9",
        "R10": "10", "R11": "11", "R12": "12", "R13": "13", "R14": "14",
        "R15": "15", "SCREEN": "16384", "KBD": "24576", "SP": "0",
        "LCL": "1", "ARG": "2", "THIS": "3", "THAT": "4",
    }

    # -----------------------------------------------------------------------
    # init
    # -----------------------------------------------------------------------

    def __init__(self, code):
        self.assembly_code = code
        self.intermediary_code = []
        self.machine_code = []

        self.labels = {}
        self.variables = Assembler.predefined_symbols.copy()

        self.remove_unnecessary()
        self.find_labels()
        self.find_variables()
        self.build_intermediary()
        self.assemble()

    # -----------------------------------------------------------------------
    # removes whitespace and comments
    # -----------------------------------------------------------------------

    def remove_unnecessary(self):
        assembly = []
        for line in self.assembly_code:
            stripped = "".join(line.split())

            comment_start = stripped.find("//")
            if comment_start != -1:
                stripped = stripped[0:comment_start]

            if stripped != "":
                assembly.append(stripped)

        self.assembly_code = assembly

    # -----------------------------------------------------------------------
    # finds our label declaration, stores the reference, and removes them
    # -----------------------------------------------------------------------
    # for labels definitions we want to store the symbol in our table and
    # delete the definition line from our code. we don't inc the current
    # instruction here since these lines don't contribute to the instruction
    # count

    def find_labels(self):
        cur_instruction = 0
        label_indexes = []

        for index, line in enumerate(self.assembly_code):

            if line.startswith("("):
                jmp_symbol = line[1:-1]
                self.labels[jmp_symbol] = cur_instruction
                label_indexes.append(index)
                continue

            cur_instruction += 1

        # delete the label declaration from the source
        for i in sorted(label_indexes, reverse=True):
            del self.assembly_code[i]

    # -----------------------------------------------------------------------
    # replaces labels/variables with their actual instruction
    # -----------------------------------------------------------------------

    def find_variables(self):
        next_address = 16

        for line in self.assembly_code:
            if not line.startswith("@"):
                continue

            symbol = line[1:]

            if symbol.isdigit():
                continue

            if symbol not in self.variables and symbol not in self.labels:
                self.variables[symbol] = next_address
                next_address += 1

    # -----------------------------------------------------------------------
    # builds an intermediary representation
    # -----------------------------------------------------------------------

    def build_intermediary(self):
        intermediary = []
        for line in self.assembly_code:

            # handle type A instructions and dereference vars/lables
            if line.startswith("@"):
                address = line[1:]
                if address in self.variables:
                    address = self.variables[address]
                elif address in self.labels:
                    address = self.labels[address]
                intermediary.append({"type": "A", "address": int(address)})
                continue

            dest_idx = line.find("=")
            jump_idx = line.find(";")

            # comp
            if dest_idx == -1 and jump_idx == -1:
                intermediary.append({
                    "type": "C",
                    "dest": None,
                    "comp": line,
                    "jump": None,
                })
                continue

            # dest=comp
            if dest_idx != -1 and jump_idx == -1:
                intermediary.append({
                    "type": "C",
                    "dest": line[0:dest_idx],
                    "comp": line[dest_idx + 1:],
                    "jump": None,
                })
                continue

            # comp;jump
            if dest_idx == -1 and jump_idx != -1:
                intermediary.append({
                    "type": "C",
                    "dest": None,
                    "comp": line[0:jump_idx],
                    "jump": line[jump_idx + 1:],
                })
                continue

            # dest=comp;jump
            if dest_idx != -1 and jump_idx != -1:
                intermediary.append({
                    "type": "C",
                    "dest": line[0:dest_idx],
                    "comp": line[dest_idx + 1:jump_idx],
                    "jump": line[jump_idx + 1:],
                })
                continue

        self.intermediary_code = intermediary

    # -----------------------------------------------------------------------
    # assembles the intermediary into machine code
    # -----------------------------------------------------------------------

    def assemble(self):
        assembled = []
        for ins in self.intermediary_code:

            if ins["type"] == "A":
                line = "0" + self.get_binary_string(ins["address"], 15)
                assembled.append(line)
                continue

            dest = Assembler.dest_table[ins["dest"]]
            comp = Assembler.comp_table[ins["comp"]]
            jump = Assembler.jump_table[ins["jump"]]

            line = "111" + comp + dest + jump

            assembled.append(line)

        self.machine_code = assembled

    # -----------------------------------------------------------------------
    # converts integer to n-bit binary string
    # -----------------------------------------------------------------------

    def get_binary_string(self, i, n):
        fmt = "#0" + str(n + 2) + "b"
        s = format(i, fmt)
        return s[2:]

    # -----------------------------------------------------------------------
    # returns the machine language as a string
    # -----------------------------------------------------------------------

    def get_machine_code(self):
        return "\n".join(self.machine_code)

asm = Assembler(sys.stdin.readlines())
print(asm.get_machine_code())
