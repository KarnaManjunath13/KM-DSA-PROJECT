#!/usr/bin/env python3
"""
Comprehensive Test Suite for Java Bytecode Simulator
Tests all tasks (a, b, c), all basic JVM instructions, and all extended matrix/sort instructions.
"""

import io
import os
import sys
import tempfile
import unittest
from simulator import JVMSimulator

class TestJVMSimulator(unittest.TestCase):

    def setUp(self):
        self.sim = JVMSimulator(stack_size=20, register_size=20, interactive=False)

    def test_loads_default_task_files_from_txt_folder(self):
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        txt_dir = os.path.join(project_root, "TXT file")
        self.assertTrue(os.path.isdir(txt_dir), "Expected TXT folder to exist")
        self.assertTrue(os.path.exists(os.path.join(txt_dir, "task_a.txt")))

        self.sim.load_file("task_a.txt")
        self.sim.set_input([5, 1, 9])
        self.assertEqual(self.sim.run(), ["1", "9"])

    # -------------------------------------------------------------------------
    # Task A Tests: Read 3 integers -> find min and max -> print them
    # -------------------------------------------------------------------------
    def test_task_a_basic(self):
        self.sim.load_file("task_a.txt")
        self.sim.set_input([15, 3, 42])
        output = self.sim.run()
        self.assertEqual(output, ["3", "42"])

    def test_task_a_negatives(self):
        self.sim.load_file("task_a.txt")
        self.sim.set_input([-10, -50, -5])
        output = self.sim.run()
        self.assertEqual(output, ["-50", "-5"])

    def test_task_a_all_equal(self):
        self.sim.load_file("task_a.txt")
        self.sim.set_input([7, 7, 7])
        output = self.sim.run()
        self.assertEqual(output, ["7", "7"])

    def test_task_a_mixed(self):
        self.sim.load_file("task_a.txt")
        self.sim.set_input([0, -100, 100])
        output = self.sim.run()
        self.assertEqual(output, ["-100", "100"])

    # -------------------------------------------------------------------------
    # Task B Tests: Read n, read n integers, sort ascending, print
    # -------------------------------------------------------------------------
    def test_task_b_n1(self):
        self.sim.load_file("task_b.txt")
        self.sim.set_input([1, 42])
        output = self.sim.run()
        self.assertEqual(output, ["42"])

    def test_task_b_n2(self):
        self.sim.load_file("task_b.txt")
        self.sim.set_input([2, 50, 20])
        output = self.sim.run()
        self.assertEqual(output, ["20", "50"])

    def test_task_b_n3(self):
        self.sim.load_file("task_b.txt")
        self.sim.set_input([3, 30, 10, 20])
        output = self.sim.run()
        self.assertEqual(output, ["10", "20", "30"])

    def test_task_b_n3_negatives(self):
        self.sim.load_file("task_b.txt")
        self.sim.set_input([3, -5, -20, 0])
        output = self.sim.run()
        self.assertEqual(output, ["-20", "-5", "0"])

    def test_task_b_n4(self):
        self.sim.load_file("task_b.txt")
        self.sim.set_input([4, 9, 3, 7, 1])
        output = self.sim.run()
        self.assertEqual(output, ["1", "3", "7", "9"])

    def test_task_b_n5(self):
        self.sim.load_file("task_b.txt")
        self.sim.set_input([5, 100, -2, 50, 0, 15])
        output = self.sim.run()
        self.assertEqual(output, ["-2", "0", "15", "50", "100"])

    # -------------------------------------------------------------------------
    # Task C Tests: 2x2 Matrix Addition
    # -------------------------------------------------------------------------
    def test_task_c_basic(self):
        self.sim.load_file("task_c.txt")
        # Matrix A: 1 2 / 3 4
        # Matrix B: 5 6 / 7 8
        # Sum: 6 8 / 10 12
        self.sim.set_input([1, 2, 3, 4, 5, 6, 7, 8])
        output = self.sim.run()
        self.assertEqual(output, ["6", "8", "10", "12"])

    def test_task_c_negatives_and_zeros(self):
        self.sim.load_file("task_c.txt")
        # Matrix A: 10 -5 / 0 3
        # Matrix B: -4 5 / 10 -3
        # Sum: 6 0 / 10 0
        self.sim.set_input([10, -5, 0, 3, -4, 5, 10, -3])
        output = self.sim.run()
        self.assertEqual(output, ["6", "0", "10", "0"])

    # -------------------------------------------------------------------------
    # Extended Matrix Operations Tests
    # -------------------------------------------------------------------------
    def test_extended_matrix_ops(self):
        self.sim.load_file("test_matrix_ops.txt")
        self.sim.set_input([
            10, 25, 20, 5,    # for read2m
            2, 4, 3, 5        # for read2sm
        ])
        output = self.sim.run()
        expected = [
            "10 25", "20 5",   # 1. print2m after read2m
            "2 4", "3 5",     # 2. print2m after read2sm + trans2m
            "-2",             # 3. det2m on [2 3; 4 5]
            "120 155", "60 85", # 4. mul2m [10 25; 20 5] x [2 3; 4 5]
            "15 0", "5 20"    # 5. compl2m on [10 25; 20 5] (max=25)
        ]
        self.assertEqual(output, expected)

    # -------------------------------------------------------------------------
    # Extended 3-Element Sort Tests
    # -------------------------------------------------------------------------
    def test_extended_sort3(self):
        self.sim.load_file("test_sort3.txt")
        output = self.sim.run()
        expected = ["3", "2", "1", "1", "2", "3"]
        self.assertEqual(output, expected)

    # -------------------------------------------------------------------------
    # Base Instruction Set Unit Tests
    # -------------------------------------------------------------------------
    def test_arithmetic_ops(self):
        code = """
        ldc 10
        ldc 4
        iadd
        print
        ldc 10
        ldc 4
        isub
        print
        ldc 10
        ldc 4
        imul
        print
        ldc 10
        ldc 4
        idiv
        print
        """
        self.sim.load_program(code)
        output = self.sim.run()
        self.assertEqual(output, ["14", "6", "40", "2"])

    def test_branching_ifeq_iflt_ifgt(self):
        code = """
        ldc 0
        ifeq target_eq
        ldc 99
        print
        target_eq:
        ldc 100
        print

        ldc -5
        iflt target_lt
        ldc 99
        print
        target_lt:
        ldc 200
        print

        ldc 5
        ifgt target_gt
        ldc 99
        print
        target_gt:
        ldc 300
        print
        """
        self.sim.load_program(code)
        output = self.sim.run()
        self.assertEqual(output, ["100", "200", "300"])

    def test_cli_accepts_debug_flag_before_file(self):
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
            f.write("ldc 7\nldc 8\niadd\nprint\n")
            path = f.name

        old_argv = sys.argv[:]
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        output = io.StringIO()
        sys.argv = ["simulator.py", "--debug", path]
        sys.stdout = output
        sys.stderr = output

        try:
            import simulator
            simulator.main()
            self.assertIn("15", output.getvalue())
            self.assertNotIn("Error:", output.getvalue())
        finally:
            sys.argv = old_argv
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            os.unlink(path)

    def test_error_handling(self):
        # Stack underflow
        sim_err = JVMSimulator(interactive=False)
        sim_err.load_program("iadd")
        with self.assertRaises(RuntimeError):
            sim_err.run()

        # Division by zero
        sim_err2 = JVMSimulator(interactive=False)
        sim_err2.load_program("ldc 10\nldc 0\nidiv")
        with self.assertRaises(ZeroDivisionError):
            sim_err2.run()

        # Stack overflow
        sim_err3 = JVMSimulator(stack_size=2, interactive=False)
        sim_err3.load_program("ldc 1\nldc 2\nldc 3")
        with self.assertRaises(RuntimeError):
            sim_err3.run()


if __name__ == "__main__":
    unittest.main()
