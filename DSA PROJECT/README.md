# Java Bytecode Simulator in Python

A clean, modular, and easy-to-understand simulator for a subset of **Java Virtual Machine (JVM) Bytecode** implemented in Python (`jvm_simulator.py`).

---

## 📋 Table of Contents
1. [Overview & Features](#overview--features)
2. [Supported Instruction Set](#supported-instruction-set)
   - [Base JVM Instructions](#base-jvm-instructions)
   - [Special I/O Instructions](#special-io-instructions)
   - [Extended Matrix Operations](#extended-matrix-operations)
   - [Extended 3-Element Sort Operations](#extended-3-element-sort-operations)
3. [Supplied Test Programs & High-Level Java Equivalents](#supplied-test-programs--high-level-java-equivalents)
   - [Task A: Find Min and Max of 3 Integers](#task-a-min-and-max-of-3-integers)
   - [Task B: Sort $n$ Integers in Ascending Order](#task-b-sort-n-integers-in-ascending-order)
   - [Task C: 2x2 Matrix Addition](#task-c-2x2-matrix-addition)
   - [Extended Matrix & Sort Operations](#extended-matrix--sort-operations)
4. [How to Run](#how-to-run)
5. [Running the Automated Test Suite](#running-the-automated-test-suite)

---

## 1. Overview & Features

- **Execution Model**:
  - **Operand Stack**: Push/pop stack for integer operations.
  - **Local Variables / Registers**: Array of integer registers (`reg 0`, `reg 1`, ...).
  - **Program Counter (PC)**: Tracks current instruction execution.
- **Parsing**:
  - Supports labels (`loop:`, `L1:`) and line number targets.
  - Skips empty lines and comments (`//`, `#`, `;`).
- **Debugging**:
  - Step-by-step trace mode (`--debug`) displaying PC, line number, instruction, stack state, and registers.

---

## 2. Supported Instruction Set

### Base JVM Instructions
| Opcode | Operand | Description |
| :--- | :--- | :--- |
| `ldc` | `<int_val>` | Pushes the integer constant `<int_val>` onto the operand stack. |
| `iload` | `<reg>` | Loads the integer from local variable register `<reg>` and pushes it onto the stack. |
| `istore` | `<reg>` | Pops the top integer from the stack and stores it in register `<reg>`. |
| `iadd` | - | Pops two integers `b`, `a` and pushes `a + b`. |
| `isub` | - | Pops two integers `b`, `a` and pushes `a - b`. |
| `imul` | - | Pops two integers `b`, `a` and pushes `a * b`. |
| `idiv` | - | Pops two integers `b`, `a` and pushes `a / b` (integer division truncating towards zero). |
| `ifeq` | `<target>` | Pops integer `v`. If `v == 0`, jumps to `<target>`. |
| `iflt` | `<target>` | Pops integer `v`. If `v < 0`, jumps to `<target>`. |
| `ifgt` | `<target>` | Pops integer `v`. If `v > 0`, jumps to `<target>`. |
| `goto` | `<target>` | Unconditionally jumps to `<target>`. |
| `ifne` / `ifle` / `ifge` | `<target>` | Conditional branches based on `!= 0`, `<= 0`, `>= 0`. |

### Special I/O Instructions
| Opcode | Description |
| :--- | :--- |
| `read` | Reads an integer from standard input and pushes it onto the operand stack. |
| `print` | Pops the top integer from the operand stack and prints it to the console. |

### Extended Matrix Operations
| Opcode | Description |
| :--- | :--- |
| `read2m` | Reads a 2x2 matrix from 2 lines (`a11 a12` and `a21 a22`). Pushes `a11, a12, a21, a22` onto the stack (`a11` at bottom). |
| `read2sm` | Reads a 2x2 matrix from a single line in order `a11 a21 a12 a22`. Pushes `a11, a12, a21, a22` onto the stack (`a11` at bottom). |
| `print2m` | Pops 4 elements representing a 2x2 matrix (`a11, a12, a21, a22`) and prints in 2x2 format. |
| `trans2m` | Pops 2x2 matrix $a$ and pushes its transpose $a^T = \begin{bmatrix} a_{11} & a_{21} \\ a_{12} & a_{22} \end{bmatrix}$. |
| `det2m` | Pops 2x2 matrix $a$ and pushes determinant: $a_{11} a_{22} - a_{12} a_{21}$. |
| `mul2m` | Pops matrix $b$ and matrix $a$ from stack and pushes matrix product $c = a \times b$. |
| `compl2m` | Pops matrix $a$, finds $M = \max(A)$, and pushes complement matrix $c_{ij} = M - a_{ij}$. |

### Extended 3-Element Sort Operations
| Opcode | Description |
| :--- | :--- |
| `sort3up` | Pops 3 elements from stack, sorts them ascending, and pushes back with smallest at bottom. |
| `sort3down` | Pops 3 elements from stack, sorts them descending, and pushes back with largest at bottom. |

---

## 3. Supplied Test Programs & High-Level Java Equivalents

### Task A: Min and Max of 3 Integers
- **Bytecode**: `task_a.txt`
- **Java Code**: `TaskA.java`
- **Logic**: Reads 3 integers into `reg 0, 1, 2`, computes min into `reg 3` and max into `reg 4`, then prints both.

### Task B: Sort $n$ Integers in Ascending Order
- **Bytecode**: `task_b.txt`
- **Java Code**: `TaskB.java`
- **Logic**: Reads $n$ into `reg 0`, reads $n$ numbers into `reg 1..n`, performs sorting with register swapping, and prints the sorted sequence.

### Task C: 2x2 Matrix Addition
- **Bytecode**: `task_c.txt`
- **Java Code**: `TaskC.java`
- **Logic**: Reads Matrix $A$ (`reg 0..3`) and Matrix $B$ (`reg 4..7`), computes $C = A + B$, and prints $c_{11}, c_{12}, c_{21}, c_{22}$.

### Extended Operations
- **Matrix Bytecode**: `test_matrix_ops.txt`
- **3-Element Sort Bytecode**: `test_sort3.txt`
- **Java Code**: `ExtendedOps.java`

---

## 4. How to Run

### Running Bytecode Programs with the Simulator
```bash
# Run Task A
python3 jvm_simulator.py task_a.txt

# Run Task B
python3 jvm_simulator.py task_b.txt

# Run Task C
python3 jvm_simulator.py task_c.txt

# Run Extended Matrix Operations
python3 jvm_simulator.py test_matrix_ops.txt

# Run Extended 3-Element Sort Operations
python3 jvm_simulator.py test_sort3.txt
```

### Running in Debug / Trace Mode
```bash
python3 jvm_simulator.py task_a.txt --debug
```

### Sample Interactive / Piped Run
```bash
# Task A example: inputs 15, 3, 42 -> output min=3, max=42
printf "15\n3\n42\n" | python3 jvm_simulator.py task_a.txt

# Task B example: n=4, numbers: 9, 3, 7, 1 -> output 1, 3, 7, 9
printf "4\n9\n3\n7\n1\n" | python3 jvm_simulator.py task_b.txt

# Task C example: Matrix A + Matrix B
printf "1 2 3 4\n5 6 7 8\n" | python3 jvm_simulator.py task_c.txt
```

---

## 5. Running the Automated Test Suite

To run all unit and integration tests:
```bash
python3 test_suite.py
```
