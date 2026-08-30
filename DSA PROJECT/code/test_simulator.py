"""
simulator.py
------------
A simulator for a small subset of Java byte code.

Supported instructions
-----------------------
ldc <n>      : push integer constant n onto the operand stack
iload <i>    : push the value of local variable (register) i onto the stack
istore <i>   : pop the top of the stack and store it into local variable i
iadd         : pop b, pop a, push (a + b)
isub         : pop b, pop a, push (a - b)
imul         : pop b, pop a, push (a * b)
idiv         : pop b, pop a, push (a / b)   (integer division, truncated toward zero)
ifeq <t>     : pop a; if a == 0, jump to target t
iflt <t>     : pop a; if a <  0, jump to target t
ifgt <t>     : pop a; if a >  0, jump to target t
read         : read one integer from standard input, push it onto the stack
print        : pop the top of the stack and print it

Extra (non-JVM) instructions specified in the assignment: read, print.

Design notes
------------
1. Program format: one instruction per line. A line that ends with ':' is
   treated as a LABEL (it marks a jump target but is not itself an
   instruction, so it costs no program-counter slot). Blank lines and lines
   starting with '#' are ignored (comments). Jump targets (the operand of
   ifeq / iflt / ifgt) may be either a label name or a raw integer program
   address -- both are supported.

2. The real byte-code instruction set given in the assignment has NO
   unconditional jump ("goto"). We emulate one whenever it is needed
   (e.g. to skip over an "if-true" block, or to jump back to the top of a
   loop) using the standard trick:
        ldc 0
        ifeq <target>
   Since the constant 0 always equals 0, "ifeq" here always branches, so
   this two-instruction idiom behaves exactly like an unconditional goto.
   This is documented at every place it is used in the test programs.

3. Operand stack and local-variable (register) array are each fixed size
   10, per the assignment ("assume maximum sizes of the operand stack and
   register set to be 10 each"). Overflow/underflow raise a RuntimeError
   so bugs are caught immediately instead of silently corrupting state.

4. There are no array instructions (no iaload/iastore) in the given
   instruction subset, so any local variable that is accessed must be
   accessed by a compile-time-constant index -- exactly like real JVM
   iload/istore. This matters for program (b) -- see sort.txt and the
   accompanying note in README.md for how a variable-length sort is done
   within this constraint.
"""

import os
import sys


class SimulatorError(Exception):
    pass


def resolve_file_path(filepath):
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


def load_program(filename, num_locals=10):
    """Read the text program, strip comments/blank lines, and resolve labels."""
    program = []
    labels = {}
    resolved_path = resolve_file_path(filename)
    with open(resolved_path) as f:
        raw_lines = f.readlines()

    for raw in raw_lines:
        line = raw.strip()
        for comment_char in ('//', '#', ';'):
            if comment_char in line:
                line = line.split(comment_char, 1)[0].strip()
        if not line:
            continue
        if line.endswith(':'):
            label_name = line[:-1].strip()
            labels[label_name] = len(program)
            continue
        program.append(line)

    return program, labels


def parse_instr(line):
    parts = line.split()
    op = parts[0]
    arg = parts[1] if len(parts) > 1 else None
    return op, arg


def resolve_target(arg, labels):
    if arg in labels:
        return labels[arg]
    try:
        return int(arg)
    except ValueError:
        raise SimulatorError(f"Unknown jump target: {arg}")


def java_int_div(a, b):
    """Integer division truncated toward zero, matching Java's idiv semantics."""
    if b == 0:
        raise SimulatorError("Division by zero")
    q = abs(a) // abs(b)
    if (a < 0) != (b < 0):
        q = -q
    return q


def run(program, labels, stack_size=10, num_locals=10, verbose=False):
    stack = []
    regs = [0] * num_locals
    pc = 0
    steps = 0
    max_steps = 1_000_000  # safety net against runaway loops

    while pc < len(program):
        steps += 1
        if steps > max_steps:
            raise SimulatorError("Exceeded maximum instruction count "
                                  "(possible infinite loop)")

        op, arg = parse_instr(program[pc])
        next_pc = pc + 1

        if verbose:
            print(f"[pc={pc}] {program[pc]:<20} stack={stack} regs={regs}",
                  file=sys.stderr)

        if op == 'ldc':
            stack.append(int(arg))

        elif op == 'iload':
            idx = int(arg)
            if not (0 <= idx < num_locals):
                raise SimulatorError(f"iload: register {idx} out of range")
            stack.append(regs[idx])

        elif op == 'istore':
            idx = int(arg)
            if not (0 <= idx < num_locals):
                raise SimulatorError(f"istore: register {idx} out of range")
            if not stack:
                raise SimulatorError("istore: stack underflow")
            regs[idx] = stack.pop()

        elif op == 'iadd':
            b = stack.pop(); a = stack.pop(); stack.append(a + b)

        elif op == 'isub':
            b = stack.pop(); a = stack.pop(); stack.append(a - b)

        elif op == 'imul':
            b = stack.pop(); a = stack.pop(); stack.append(a * b)

        elif op == 'idiv':
            b = stack.pop(); a = stack.pop(); stack.append(java_int_div(a, b))

        elif op == 'ifeq':
            v = stack.pop()
            if v == 0:
                next_pc = resolve_target(arg, labels)

        elif op == 'iflt':
            v = stack.pop()
            if v < 0:
                next_pc = resolve_target(arg, labels)

        elif op == 'ifgt':
            v = stack.pop()
            if v > 0:
                next_pc = resolve_target(arg, labels)

        elif op == 'read':
            line = sys.stdin.readline()
            if line == '':
                raise SimulatorError("read: no more input available")
            stack.append(int(line.strip()))

        elif op == 'print':
            if not stack:
                raise SimulatorError("print: stack underflow")
            print(stack.pop())

        elif op == 'dumpstack':
            print(*stack)


        elif op == 'read3':
            for _ in range(3):
                line = sys.stdin.readline()
                if line == '':
                    raise SimulatorError("read3: not enough input available")
                stack.append(int(line.strip()))

        elif op == 'read4':
            line1 = sys.stdin.readline()
            line2 = sys.stdin.readline()
            part1= line1.strip().split()
            part2 = line2.strip().split()
            parts=part1+part2
            numbers = [int(p) for p in parts]
            stack.extend(reversed(numbers))  
        elif op == 'combo4':
            if len(stack)<4:
                raise SimulatorError("combo4: stack underflow")
            d=stack.pop()
            c= stack.pop()
            b = stack.pop()
            a = stack.pop()
            stack.append((a+b)*(c+d))


        elif op == 'det2m':
            d = stack.pop()
            c = stack.pop()
            b = stack.pop()
            a = stack.pop()
            stack.append(a*d - b*c)


        elif op == 'trans2':
            d = stack.pop()
            c = stack.pop()
            b = stack.pop() 
            a = stack.pop()
            stack.append(a)
            stack.append(c)
            stack.append(b)
            stack.append(d)


        elif op == 'read2sm':
            line = sys.stdin.readline()
            parts = line.strip().split()
            a,c,b,d = [int(q) for q in parts]
            stack.append(a)
            stack.append(b)
            stack.append(c)
            stack.append(d)


        elif op == 'print2':
            if len(stack) <4:
                raise SimulatorError("print2:stack underflow") 
            d = stack.pop()
            c = stack.pop()
            b = stack.pop()
            a = stack.pop()
            print(a , b)
            print(c , d)


        elif op == 'mul2':
            if len(stack)<8:
                raise SimulatorError("mul2:stack underflow")
            b22 = stack.pop()
            b21 = stack.pop()
            b12 = stack.pop()
            b11 = stack.pop()
            a22 = stack.pop()
            a21 = stack.pop()
            a12 = stack.pop()
            a11 = stack.pop()
            c11 = a11*b11
            c12 = a12*b12
            c21 = a21*b21
            c22 = a22*b22
            stack.append(c11)
            stack.append(c12)
            stack.append(c21)
            stack.append(c22)


        elif op == 'compl2m':
            if len(stack)< 4:
                raise SimulatorError("compl2m : stack underflow")
            x = stack.pop()
            y = stack.pop()
            z = stack.pop()
            q = stack.pop()
            big = max(x,y,z,q)
            a11 = big - q
            a12 = big - z
            a21 = big - y 
            a22 = big - x
            stack.append(a11)
            stack.append(a12)
            stack.append(a21)
            stack.append(a22)
            


                
                

            

        else:
            raise SimulatorError(f"Unknown instruction '{op}' at line {pc}")

        if len(stack) > stack_size:
            raise SimulatorError("Operand stack overflow")

        pc = next_pc


def main():
    args = sys.argv[1:]
    debug_mode = any(arg in ("--debug", "-d") for arg in args)
    filepath = None

    for arg in args:
        if arg not in ("--debug", "-d") and not arg.startswith("--"):
            filepath = arg
            break

    if filepath is None:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        txt_dir = os.path.join(project_root, "TXT file")
        if os.path.isdir(txt_dir):
            txt_files = sorted(
                name for name in os.listdir(txt_dir)
                if name.lower().endswith(".txt")
            )
            if not txt_files:
                print("No .txt files found in the TXT folder.", file=sys.stderr)
                sys.exit(1)

            try:
                choice = input("Enter Bytecode File: ").strip()
            except EOFError:
                print("\nNo file entered.", file=sys.stderr)
                sys.exit(1)

            choice_lower = choice.lower()
            if choice_lower == 'all':
                for name in txt_files:
                    file_path = os.path.join(txt_dir, name)
                    print(f"\n--- {name} ---")
                    try:
                        program, labels = load_program(file_path)
                        run(program, labels, verbose=debug_mode)
                    except SimulatorError as e:
                        print(f"Simulation error for {name}: {e}", file=sys.stderr)
                        sys.exit(1)
                return

            if not choice:
                print("No file selected.", file=sys.stderr)
                sys.exit(1)

            selected_name = None
            if choice_lower.endswith('.txt'):
                for name in txt_files:
                    if name.lower() == choice_lower:
                        selected_name = name
                        break
            else:
                for name in txt_files:
                    if name.lower() == f"{choice_lower}.txt":
                        selected_name = name
                        break

            if selected_name is None:
                print(f"File not found: {choice}", file=sys.stderr)
                sys.exit(1)

            filepath = os.path.join(txt_dir, selected_name)
        else:
            print("Usage: python3 test_simulator.py [--debug|-d] <program.txt>", file=sys.stderr)
            sys.exit(1)

    try:
        program, labels = load_program(filepath)
        run(program, labels, verbose=debug_mode)
    except SimulatorError as e:
        print(f"Simulation error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
