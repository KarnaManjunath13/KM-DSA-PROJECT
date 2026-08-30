def run(program, labels, stack_size=10, num_locals=10, verbose=False):
    stack = []
    regs = [0] * num_locals
    pc = 0
    steps = 0
    max_steps = 1_000_000
    input_tokens = []   # <-- add this

    def next_token():
        nonlocal input_tokens
        while not input_tokens:
            line = sys.stdin.readline()
            if line == '':
                raise SimulatorError("read: no more input available")
            input_tokens = line.split()
        return input_tokens.pop(0)