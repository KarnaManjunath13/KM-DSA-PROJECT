#!/usr/bin/env python3
"""
===============================================================================
                     JAVA BYTECODE SIMULATOR IN PYTHON
===============================================================================
Simulates a subset of Java Virtual Machine (JVM) integer bytecode instructions
along with custom I/O, matrix, and sorting operations.

Supported Instructions:
  - Base JVM:
      ldc <val>       : Push integer constant onto operand stack
      iload <reg>     : Push value from local variable register onto operand stack
      istore <reg>    : Pop value from stack and store into register
      iadd            : Pop b, pop a -> push a + b
      isub            : Pop b, pop a -> push a - b
      imul            : Pop b, pop a -> push a * b
      idiv            : Pop b, pop a -> push a // b (truncate toward zero)
      ifeq <target>   : Pop v -> jump if v == 0
      iflt <target>   : Pop v -> jump if v < 0
      ifgt <target>   : Pop v -> jump if v > 0
      goto <target>   : Unconditional branch to target
      ifne, ifle, ifge: Conditional branches (!= 0, <= 0, >= 0)

  - Special I/O:
      read            : Read integer from user input and push onto stack
      print           : Pop integer from stack and print to console

  - Extended Matrix & Sort Instructions:
      read2m          : Read 2x2 matrix (a11, a12, a21, a22) -> push to stack
      read2sm         : Read 2x2 matrix (order a11, a21, a12, a22) -> push to stack
      print2m         : Pop 4 elements and print in 2x2 matrix format
      trans2m         : Pop 2x2 matrix, push transpose matrix
      det2m           : Pop 2x2 matrix, push determinant (a11*a22 - a12*a21)
      mul2m           : Pop matrix B and matrix A, push matrix product A x B
      compl2m         : Pop matrix A, push complement matrix w.r.t max element
      sort3up         : Pop 3 elements, sort ascending (smallest at bottom)
      sort3down       : Pop 3 elements, sort descending (largest at bottom)
===============================================================================
"""

import sys
import os

class JVMSimulator:
    def __init__(self, stack_size=100, register_size=100, input_stream=None, interactive=True):
        self.max_stack_size = stack_size
        self.max_register_size = register_size
        self.stack = []
        self.registers = [0] * register_size
        self.instructions = []
        self.labels = {}
        self.line_to_idx = {}
        self.pc = 0
        self.is_halted = False
        self.input_tokens = []
        self.input_stream = input_stream
        self.interactive = interactive
        self.output_log = []

    def reset(self):
        """Resets the simulator registers, stack, program counter, and buffers."""
        self.stack.clear()
        self.registers = [0] * self.max_register_size
        self.pc = 0
        self.is_halted = False
        self.input_tokens.clear()
        self.output_log.clear()

    def set_input(self, input_data):
        """Pre-loads inputs for automated testing or non-interactive execution."""
        self.interactive = False
        if isinstance(input_data, str):
            self.input_tokens = input_data.strip().split()
        elif isinstance(input_data, (list, tuple)):
            self.input_tokens = [str(x) for x in input_data]

    def _read_next_int(self, prompt="Enter integer: "):
        """Reads the next integer from token buffer or directly prompts the user."""
        while not self.input_tokens:
            if self.input_stream is not None:
                line = self.input_stream.readline()
            else:
                try:
                    if self.interactive:
                        print(prompt, end="", flush=True)
                    line = sys.stdin.readline()
                except (EOFError, KeyboardInterrupt):
                    raise RuntimeError("Input interrupted.")
            
            if not line:
                raise RuntimeError("End of input reached.")

            tokens = line.strip().split()
            if tokens:
                self.input_tokens.extend(tokens)

        token = self.input_tokens.pop(0)
        try:
            return int(token)
        except ValueError:
            raise ValueError(f"Invalid integer: '{token}'. Please enter numbers only.")

    def load_program(self, text_or_lines):
        """Parses bytecode text into executable instructions and resolves labels."""
        self.instructions = []
        self.labels = {}
        self.line_to_idx = {}
        self.reset()

        if isinstance(text_or_lines, str):
            raw_lines = text_or_lines.splitlines()
        else:
            raw_lines = list(text_or_lines)

        for line_num, raw_line in enumerate(raw_lines, start=1):
            line = raw_line.strip()
            
            # Remove comments (//, #, ;)
            for comment_char in ('//', '#', ';'):
                if comment_char in line:
                    line = line.split(comment_char, 1)[0].strip()

            if not line:
                continue

            # Parse label prefixes like "loop:" or "0:"
            while True:
                parts = line.split(None, 1)
                if not parts:
                    break
                first_token = parts[0]
                if first_token.endswith(':'):
                    label_name = first_token[:-1].strip()
                    if label_name.isdigit():
                        self.line_to_idx[int(label_name)] = len(self.instructions)
                    else:
                        self.labels[label_name] = len(self.instructions)
                    line = parts[1].strip() if len(parts) > 1 else ""
                else:
                    break

            if not line:
                continue

            tokens = line.split()
            opcode = tokens[0].lower()
            operand = tokens[1] if len(tokens) > 1 else None

            self.line_to_idx[line_num] = len(self.instructions)
            self.instructions.append({
                'opcode': opcode,
                'operand': operand,
                'line_num': line_num,
                'raw': raw_line.strip()
            })

    def _resolve_file_path(self, filepath):
        """Resolve a .txt program path from the current directory, script folder, or TXT folder."""
        if not filepath:
            return filepath

        if os.path.isabs(filepath) and os.path.exists(filepath):
            return filepath

        candidates = []
        raw_name = os.path.basename(filepath)

        if os.path.exists(filepath):
            candidates.append(filepath)

        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        txt_dir = os.path.join(project_root, "TXT file")

        candidates.extend([
            os.path.join(os.getcwd(), filepath),
            os.path.join(script_dir, filepath),
            os.path.join(txt_dir, raw_name),
            os.path.join(script_dir, "..", "TXT file", raw_name),
            os.path.join(project_root, filepath),
        ])

        for candidate in candidates:
            if os.path.isfile(candidate):
                return candidate

        return filepath

    def load_file(self, filepath):
        """Loads and parses a bytecode program from a .txt file."""
        resolved_path = self._resolve_file_path(filepath)
        if not os.path.exists(resolved_path):
            raise FileNotFoundError(f"Bytecode file not found: {filepath}")
        with open(resolved_path, 'r', encoding='utf-8') as f:
            self.load_program(f.readlines())

    def _resolve_target(self, target_str):
        """Resolves jump label names or line numbers to instruction indices."""
        if target_str in self.labels:
            return self.labels[target_str]
        try:
            num = int(target_str)
            if num in self.line_to_idx:
                return self.line_to_idx[num]
            if 0 <= num < len(self.instructions):
                return num
            if 1 <= num <= len(self.instructions):
                return num - 1
        except ValueError:
            pass
        raise RuntimeError(f"Undefined branch target: '{target_str}'")

    def _push(self, value):
        if len(self.stack) >= self.max_stack_size:
            raise RuntimeError(f"Stack overflow (limit: {self.max_stack_size})")
        self.stack.append(int(value))

    def _pop(self):
        if not self.stack:
            raise RuntimeError("Stack underflow: Attempted to pop from empty stack")
        return self.stack.pop()

    def step(self, debug=False):
        """Executes a single instruction."""
        if self.pc < 0 or self.pc >= len(self.instructions):
            self.is_halted = True
            return False

        instr = self.instructions[self.pc]
        op = instr['opcode']
        arg = instr['operand']
        current_pc = self.pc
        next_pc = self.pc + 1

        if debug:
            print(f"[{current_pc:03d}] (Line {instr['line_num']:02d}) {instr['raw']:<25} | Stack: {self.stack} | Regs: {self.registers[:8]}", flush=True)

        # --- Base Instructions ---
        if op == 'ldc':
            if arg is None:
                raise ValueError("ldc requires an integer constant")
            self._push(int(arg))

        elif op == 'iload':
            if arg is None:
                raise ValueError("iload requires a register index")
            reg = int(arg)
            if reg < 0 or reg >= len(self.registers):
                raise IndexError(f"Register index out of bounds: {reg}")
            self._push(self.registers[reg])

        elif op == 'istore':
            if arg is None:
                raise ValueError("istore requires a register index")
            reg = int(arg)
            if reg < 0 or reg >= len(self.registers):
                raise IndexError(f"Register index out of bounds: {reg}")
            val = self._pop()
            self.registers[reg] = val

        elif op == 'iadd':
            b = self._pop()
            a = self._pop()
            self._push(a + b)

        elif op == 'isub':
            b = self._pop()
            a = self._pop()
            self._push(a - b)

        elif op == 'imul':
            b = self._pop()
            a = self._pop()
            self._push(a * b)

        elif op == 'idiv':
            b = self._pop()
            a = self._pop()
            if b == 0:
                raise ZeroDivisionError("Division by zero in idiv")
            self._push(int(a / b))

        elif op == 'ifeq':
            val = self._pop()
            if val == 0:
                next_pc = self._resolve_target(arg)

        elif op == 'iflt':
            val = self._pop()
            if val < 0:
                next_pc = self._resolve_target(arg)

        elif op == 'ifgt':
            val = self._pop()
            if val > 0:
                next_pc = self._resolve_target(arg)

        elif op == 'ifne':
            val = self._pop()
            if val != 0:
                next_pc = self._resolve_target(arg)

        elif op == 'ifle':
            val = self._pop()
            if val <= 0:
                next_pc = self._resolve_target(arg)

        elif op == 'ifge':
            val = self._pop()
            if val >= 0:
                next_pc = self._resolve_target(arg)

        elif op == 'goto':
            next_pc = self._resolve_target(arg)

        # --- I/O Operations ---
        elif op == 'read':
            val = self._read_next_int("Enter integer: ")
            self._push(val)

        elif op == 'print':
            val = self._pop()
            print(val, flush=True)
            self.output_log.append(str(val))

        # --- Matrix Operations ---
        elif op == 'read2m':
            # Reads 2x2 matrix elements: a11, a12, a21, a22
            a11 = self._read_next_int("Enter a11: ")
            a12 = self._read_next_int("Enter a12: ")
            a21 = self._read_next_int("Enter a21: ")
            a22 = self._read_next_int("Enter a22: ")
            self._push(a11)
            self._push(a12)
            self._push(a21)
            self._push(a22)

        elif op == 'read2sm':
            # Reads in order: a11, a21, a12, a22 -> pushes: a11, a12, a21, a22
            a11 = self._read_next_int("Enter a11: ")
            a21 = self._read_next_int("Enter a21: ")
            a12 = self._read_next_int("Enter a12: ")
            a22 = self._read_next_int("Enter a22: ")
            self._push(a11)
            self._push(a12)
            self._push(a21)
            self._push(a22)

        elif op == 'print2m':
            a22 = self._pop()
            a21 = self._pop()
            a12 = self._pop()
            a11 = self._pop()
            line1 = f"{a11} {a12}"
            line2 = f"{a21} {a22}"
            print(line1, flush=True)
            print(line2, flush=True)
            self.output_log.extend([line1, line2])

        elif op == 'trans2m':
            a22 = self._pop()
            a21 = self._pop()
            a12 = self._pop()
            a11 = self._pop()
            self._push(a11)
            self._push(a21)
            self._push(a12)
            self._push(a22)

        elif op == 'det2m':
            a22 = self._pop()
            a21 = self._pop()
            a12 = self._pop()
            a11 = self._pop()
            det = a11 * a22 - a12 * a21
            self._push(det)

        elif op == 'mul2m':
            b22 = self._pop()
            b21 = self._pop()
            b12 = self._pop()
            b11 = self._pop()

            a22 = self._pop()
            a21 = self._pop()
            a12 = self._pop()
            a11 = self._pop()

            c11 = a11 * b11 + a12 * b21
            c12 = a11 * b12 + a12 * b22
            c21 = a21 * b11 + a22 * b21
            c22 = a21 * b12 + a22 * b22

            self._push(c11)
            self._push(c12)
            self._push(c21)
            self._push(c22)

        elif op == 'compl2m':
            a22 = self._pop()
            a21 = self._pop()
            a12 = self._pop()
            a11 = self._pop()

            m_val = max(a11, a12, a21, a22)
            self._push(m_val - a11)
            self._push(m_val - a12)
            self._push(m_val - a21)
            self._push(m_val - a22)

        elif op == 'sort3up':
            c = self._pop()
            b = self._pop()
            a = self._pop()
            for val in sorted([a, b, c]):
                self._push(val)

        elif op == 'sort3down':
            c = self._pop()
            b = self._pop()
            a = self._pop()
            for val in sorted([a, b, c], reverse=True):
                self._push(val)

        elif op == 'dup':
            val = self._pop()
            self._push(val)
            self._push(val)

        elif op == 'swap':
            v1 = self._pop()
            v2 = self._pop()
            self._push(v1)
            self._push(v2)

        elif op == 'nop':
            pass

        elif op in ('halt', 'stop'):
            self.is_halted = True
            return False

        else:
            raise ValueError(f"Unknown opcode '{op}' at line {instr['line_num']}")

        self.pc = next_pc
        if self.pc >= len(self.instructions):
            self.is_halted = True
            return False
        return True

    def run(self, debug=False, max_steps=100000):
        """Runs the simulator until halted."""
        steps = 0
        while not self.is_halted and steps < max_steps:
            if not self.step(debug=debug):
                break
            steps += 1
        
        if steps >= max_steps:
            raise RuntimeError(f"Execution limit exceeded ({max_steps} steps). Infinite loop detected.")
        return self.output_log


def interactive_menu():
    """Runs a friendly interactive menu for user testing."""
    while True:
        print("\n" + "=" * 65, flush=True)
        print("          JAVA BYTECODE SIMULATOR (PYTHON INTERACTIVE)", flush=True)
        print("=" * 65, flush=True)
        print(" Choose a task or program to run:", flush=True)
        print("   1. Task A: Minimum & Maximum of 3 Integers (task_a.txt)", flush=True)
        print("   2. Task B: Sort N Integers in Ascending Order (task_b.txt)", flush=True)
        print("   3. Task C: 2x2 Matrix Addition (task_c.txt)", flush=True)
        print("   4. Extended Matrix Operations Demo (test_matrix_ops.txt)", flush=True)
        print("   5. Extended 3-Element Sort Demo (test_sort3.txt)", flush=True)
        print("   6. Run Any Custom .txt Bytecode File", flush=True)
        print("   7. Run Full Automated Test Suite", flush=True)
        print("   8. Exit", flush=True)
        print("=" * 65, flush=True)
        print("Enter choice (1-8): ", end="", flush=True)

        try:
            choice_line = sys.stdin.readline()
            if not choice_line:
                break
            choice = choice_line.strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting. Goodbye!", flush=True)
            break

        if not choice:
            continue

        sim = JVMSimulator(interactive=True)

        if choice == '1':
            print("\n-------------------------------------------------------------", flush=True)
            print("Running Task A: Read 3 integers -> Find min & max -> Print them", flush=True)
            print("-------------------------------------------------------------", flush=True)
            try:
                sim.load_file("task_a.txt")
                sim.run()
                print("-------------------------------------------------------------", flush=True)
                print(f"Finished! Min = {sim.output_log[0]}, Max = {sim.output_log[1]}", flush=True)
            except Exception as e:
                print(f"Error: {e}", flush=True)

        elif choice == '2':
            print("\n-------------------------------------------------------------", flush=True)
            print("Running Task B: Sort N integers in ascending order (N = 1 to 5)", flush=True)
            print("First enter count N, then enter the N integers:", flush=True)
            print("-------------------------------------------------------------", flush=True)
            try:
                sim.load_file("task_b.txt")
                sim.run()
                print("-------------------------------------------------------------", flush=True)
                print(f"Finished! Sorted integers: {' '.join(sim.output_log)}", flush=True)
            except Exception as e:
                print(f"Error: {e}", flush=True)

        elif choice == '3':
            print("\n-------------------------------------------------------------", flush=True)
            print("Running Task C: 2x2 Matrix Addition (Matrix A + Matrix B)", flush=True)
            print("Enter 4 elements for Matrix A, then 4 elements for Matrix B:", flush=True)
            print("-------------------------------------------------------------", flush=True)
            try:
                sim.load_file("task_c.txt")
                sim.run()
                print("-------------------------------------------------------------", flush=True)
            except Exception as e:
                print(f"Error: {e}", flush=True)

        elif choice == '4':
            print("\n-------------------------------------------------------------", flush=True)
            print("Running Extended Matrix Operations (test_matrix_ops.txt)", flush=True)
            print("-------------------------------------------------------------", flush=True)
            try:
                sim.load_file("test_matrix_ops.txt")
                sim.run()
                print("-------------------------------------------------------------", flush=True)
            except Exception as e:
                print(f"Error: {e}", flush=True)

        elif choice == '5':
            print("\n-------------------------------------------------------------", flush=True)
            print("Running Extended 3-Element Sort (test_sort3.txt)", flush=True)
            print("-------------------------------------------------------------", flush=True)
            try:
                sim.load_file("test_sort3.txt")
                sim.run()
                print("-------------------------------------------------------------", flush=True)
            except Exception as e:
                print(f"Error: {e}", flush=True)

        elif choice == '6':
            print("Enter bytecode file name: ", end="", flush=True)
            filepath = sys.stdin.readline().strip()
            if not os.path.exists(filepath):
                print(f"File not found: '{filepath}'", flush=True)
                continue
            try:
                sim.load_file(filepath)
                print(f"\n--- Output of {filepath} ---", flush=True)
                sim.run()
                print("--- End of Execution ---", flush=True)
            except Exception as e:
                print(f"Error: {e}", flush=True)

        elif choice == '7':
            print("\n>>> Running Automated Test Suite...", flush=True)
            os.system("python3 test_suite.py")

        elif choice == '8':
            print("Exiting simulator. Good luck with your exam!", flush=True)
            break

        else:
            print(f"Invalid choice '{choice}'. Please select 1 through 8.", flush=True)


def main():
    if len(sys.argv) > 1:
        args = sys.argv[1:]
        if args and args[0] in ("--test", "-t"):
            import unittest
            from test_suite import TestJVMSimulator
            suite = unittest.TestLoader().loadTestsFromTestCase(TestJVMSimulator)
            unittest.TextTestRunner(verbosity=2).run(suite)
            return

        debug_mode = any(arg in ("--debug", "-d") for arg in args)
        filepath = None
        for arg in args:
            if arg not in ("--debug", "-d") and not arg.startswith("--"):
                filepath = arg
                break

        if filepath is None:
            print("Usage: python3 simulator.py [--debug|-d] <bytecode_file.txt>", file=sys.stderr, flush=True)
            sys.exit(1)

        sim = JVMSimulator(interactive=True)
        try:
            sim.load_file(filepath)
            sim.run(debug=debug_mode)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr, flush=True)
            sys.exit(1)
    else:
        interactive_menu()


if __name__ == "__main__":
    main()
