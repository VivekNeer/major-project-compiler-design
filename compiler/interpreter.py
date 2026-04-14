"""
IR Interpreter — executes Three-Address Code directly.

Provides dynamic metrics that static analysis cannot:
  - Dynamic instruction count (how many instructions actually execute,
    counting loop iterations)
  - Per-opcode execution frequency
  - Execution trace for debugging

The interpreter also validates IR correctness: if optimized code
produces different output than unoptimized code, the optimization
pass has a bug.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from compiler.ir import IRInstruction, IROpcode, is_constant, const_value


class InterpreterError(Exception):
    pass


@dataclass
class ExecutionResult:
    """Results from executing an IR program."""
    return_value: int | None = None
    output: list[int] = field(default_factory=list)
    dynamic_instruction_count: int = 0
    opcode_frequency: dict[str, int] = field(default_factory=dict)
    max_steps_reached: bool = False


class IRInterpreter:
    """Executes Three-Address Code instructions."""

    MAX_STEPS = 10_000_000  # Safety limit to prevent infinite loops

    def __init__(self, instructions: list[IRInstruction]):
        self._instructions = instructions
        self._vars: dict[str, int] = {}
        self._output: list[int] = []
        self._step_count = 0
        self._opcode_freq: dict[str, int] = {}
        self._label_index: dict[str, int] = {}
        self._func_index: dict[str, int] = {}
        self._call_stack: list[_CallFrame] = []

        # Build label and function indices for fast lookup
        for i, inst in enumerate(instructions):
            if inst.opcode == IROpcode.LABEL and inst.dest:
                self._label_index[inst.dest] = i
            if inst.opcode == IROpcode.FUNC_BEGIN and inst.dest:
                self._func_index[inst.dest] = i

    def execute(self) -> ExecutionResult:
        """Execute the IR program starting from main()."""
        if "main" not in self._func_index:
            raise InterpreterError("No main() function found")

        result = self._execute_function("main", [])

        return ExecutionResult(
            return_value=result,
            output=list(self._output),
            dynamic_instruction_count=self._step_count,
            opcode_frequency=dict(self._opcode_freq),
            max_steps_reached=self._step_count >= self.MAX_STEPS,
        )

    def _execute_function(self, name: str, args: list[int]) -> int:
        """Execute a function with given arguments, return its return value."""
        if name not in self._func_index:
            raise InterpreterError(f"Undefined function: {name}")

        # Save caller state and create new frame
        frame = _CallFrame(
            saved_vars=dict(self._vars),
            return_addr=0,
        )
        self._call_stack.append(frame)

        # Find function body
        func_start = self._func_index[name]
        func_inst = self._instructions[func_start]
        assert func_inst.opcode == IROpcode.FUNC_BEGIN

        # Start fresh variable scope for this function
        self._vars = {}

        # Bind parameters using FUNC_PARAM instructions that follow FUNC_BEGIN
        pc = func_start + 1
        arg_idx = 0
        while pc < len(self._instructions):
            inst = self._instructions[pc]
            if inst.opcode == IROpcode.FUNC_PARAM and inst.dest:
                if arg_idx < len(args):
                    self._vars[inst.dest] = args[arg_idx]
                arg_idx += 1
                pc += 1
            else:
                break
        return_value = 0

        while pc < len(self._instructions):
            if self._step_count >= self.MAX_STEPS:
                break

            inst = self._instructions[pc]
            self._step_count += 1
            self._opcode_freq[inst.opcode.name] = self._opcode_freq.get(inst.opcode.name, 0) + 1

            if inst.opcode == IROpcode.FUNC_END:
                break

            if inst.opcode == IROpcode.LABEL:
                pc += 1
                continue

            if inst.opcode == IROpcode.NOP:
                pc += 1
                continue

            if inst.opcode == IROpcode.FUNC_PARAM:
                # Already handled during function setup
                pc += 1
                continue

            if inst.opcode == IROpcode.LOAD_CONST:
                self._vars[inst.dest] = const_value(inst.src1)
                pc += 1
                continue

            if inst.opcode == IROpcode.COPY:
                self._vars[inst.dest] = self._get_value(inst.src1)
                pc += 1
                continue

            if inst.opcode in _BINARY_OPS:
                v1 = self._get_value(inst.src1)
                v2 = self._get_value(inst.src2)
                self._vars[inst.dest] = _BINARY_OPS[inst.opcode](v1, v2)
                pc += 1
                continue

            if inst.opcode == IROpcode.NEG:
                self._vars[inst.dest] = -self._get_value(inst.src1)
                pc += 1
                continue

            if inst.opcode == IROpcode.NOT:
                self._vars[inst.dest] = int(not self._get_value(inst.src1))
                pc += 1
                continue

            if inst.opcode == IROpcode.JUMP:
                pc = self._label_index[inst.dest]
                continue

            if inst.opcode == IROpcode.JUMP_IF_TRUE:
                if self._get_value(inst.src1):
                    pc = self._label_index[inst.dest]
                else:
                    pc += 1
                continue

            if inst.opcode == IROpcode.JUMP_IF_FALSE:
                if not self._get_value(inst.src1):
                    pc = self._label_index[inst.dest]
                else:
                    pc += 1
                continue

            if inst.opcode == IROpcode.PARAM:
                # Collect params for upcoming CALL
                if not hasattr(self, '_pending_params'):
                    self._pending_params: list[int] = []
                self._pending_params.append(self._get_value(inst.src1))
                pc += 1
                continue

            if inst.opcode == IROpcode.CALL:
                params = getattr(self, '_pending_params', [])
                self._pending_params = []
                ret = self._execute_function(inst.src1, params)
                self._vars[inst.dest] = ret
                pc += 1
                continue

            if inst.opcode == IROpcode.RETURN:
                if inst.src1:
                    return_value = self._get_value(inst.src1)
                break

            if inst.opcode == IROpcode.PRINT:
                val = self._get_value(inst.src1)
                self._output.append(val)
                pc += 1
                continue

            if inst.opcode == IROpcode.FUNC_BEGIN:
                # Skip nested function declarations
                depth = 1
                pc += 1
                while pc < len(self._instructions) and depth > 0:
                    if self._instructions[pc].opcode == IROpcode.FUNC_BEGIN:
                        depth += 1
                    elif self._instructions[pc].opcode == IROpcode.FUNC_END:
                        depth -= 1
                    pc += 1
                continue

            pc += 1

        # Restore caller state
        if self._call_stack:
            frame = self._call_stack.pop()
            self._vars = frame.saved_vars

        return return_value

    def _get_value(self, operand: str | None) -> int:
        """Get the integer value of an operand (constant or variable)."""
        if operand is None:
            return 0
        if is_constant(operand):
            return const_value(operand)
        if operand in self._vars:
            return self._vars[operand]
        # Uninitialized variable — default to 0
        return 0


@dataclass
class _CallFrame:
    saved_vars: dict[str, int]
    return_addr: int


# Binary operation dispatch table
_BINARY_OPS: dict[IROpcode, object] = {
    IROpcode.ADD: lambda a, b: a + b,
    IROpcode.SUB: lambda a, b: a - b,
    IROpcode.MUL: lambda a, b: a * b,
    IROpcode.DIV: lambda a, b: a // b if b != 0 else 0,
    IROpcode.MOD: lambda a, b: a % b if b != 0 else 0,
    IROpcode.EQ:  lambda a, b: int(a == b),
    IROpcode.NEQ: lambda a, b: int(a != b),
    IROpcode.LT:  lambda a, b: int(a < b),
    IROpcode.GT:  lambda a, b: int(a > b),
    IROpcode.LTE: lambda a, b: int(a <= b),
    IROpcode.GTE: lambda a, b: int(a >= b),
    IROpcode.AND: lambda a, b: int(bool(a) and bool(b)),
    IROpcode.OR:  lambda a, b: int(bool(a) or bool(b)),
}


def execute_ir(instructions: list[IRInstruction]) -> ExecutionResult:
    """Convenience: execute IR and return results."""
    return IRInterpreter(instructions).execute()
