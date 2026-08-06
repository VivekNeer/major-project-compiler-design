"""
Minimal RV32IM simulator for testing the assembly backend.

Executes exactly the instruction subset emitted by
compiler/codegen_riscv.py — this is a test oracle, not a general
RISC-V emulator. Supports the Linux write (64) and exit (93) syscalls
used by the generated runtime, capturing stdout bytes.
"""

from __future__ import annotations
from dataclasses import dataclass, field

_MASK = 0xFFFFFFFF
_DATA_BASE = 0x10000000
_STACK_TOP = 0x7FFF0000


def _signed(v: int) -> int:
    v &= _MASK
    return v - 0x100000000 if v >= 0x80000000 else v


@dataclass
class SimResult:
    exit_code: int
    stdout: str
    steps: int = 0
    output_ints: list[int] = field(default_factory=list)

    def __post_init__(self):
        self.output_ints = [
            int(line) for line in self.stdout.splitlines() if line.strip()
        ]


class RiscvSimulator:
    """Parse and execute generated RV32IM assembly text."""

    MAX_STEPS = 50_000_000

    def __init__(self, asm: str):
        self._labels: dict[str, int] = {}
        self._program: list[tuple[str, list[str]]] = []
        self._data_symbols: dict[str, int] = {}
        self._mem: dict[int, int] = {}  # byte-addressed sparse memory
        self._parse(asm)

    def _parse(self, asm: str) -> None:
        section = "text"
        data_addr = _DATA_BASE
        for raw in asm.splitlines():
            line = raw.split("#", 1)[0].strip()
            if not line:
                continue
            if line.startswith(".text"):
                section = "text"
                continue
            if line.startswith(".data"):
                section = "data"
                continue
            if line.startswith(".globl"):
                continue

            if section == "data":
                # "name: .word init"
                name, rest = line.split(":", 1)
                value = int(rest.replace(".word", "").strip())
                self._data_symbols[name.strip()] = data_addr
                self._store_word(data_addr, value)
                data_addr += 4
                continue

            if line.endswith(":"):
                self._labels[line[:-1]] = len(self._program)
                continue

            parts = line.replace(",", " ").split()
            self._program.append((parts[0], parts[1:]))

    # -- memory helpers -------------------------------------------------

    def _store_word(self, addr: int, value: int) -> None:
        value &= _MASK
        for i in range(4):
            self._mem[addr + i] = (value >> (8 * i)) & 0xFF

    def _load_word(self, addr: int) -> int:
        return sum(self._mem.get(addr + i, 0) << (8 * i) for i in range(4))

    # -- execution ------------------------------------------------------

    def run(self) -> SimResult:
        regs: dict[str, int] = {f"x{i}": 0 for i in range(32)}
        reg = regs  # alias
        names = {}
        abi = ("zero ra sp gp tp t0 t1 t2 s0 s1 a0 a1 a2 a3 a4 a5 a6 a7 "
               "s2 s3 s4 s5 s6 s7 s8 s9 s10 s11 t3 t4 t5 t6").split()
        for i, n in enumerate(abi):
            names[n] = f"x{i}"

        def get(r: str) -> int:
            return 0 if r == "zero" else reg[names[r]]

        def put(r: str, v: int) -> None:
            if r != "zero":
                reg[names[r]] = v & _MASK

        put("sp", _STACK_TOP)
        stdout = bytearray()
        pc = self._labels["_start"]
        ra_stack: list[int] = []
        steps = 0
        exit_code = 0

        while steps < self.MAX_STEPS:
            steps += 1
            op, a = self._program[pc]

            if op == "li":
                put(a[0], int(a[1]))
            elif op == "mv":
                put(a[0], get(a[1]))
            elif op == "la":
                put(a[0], self._data_symbols[a[1]])
            elif op in ("add", "sub", "mul", "and", "or"):
                x, y = _signed(get(a[1])), _signed(get(a[2]))
                v = {"add": x + y, "sub": x - y, "mul": x * y,
                     "and": x & y, "or": x | y}[op]
                put(a[0], v)
            elif op == "div":
                x, y = _signed(get(a[1])), _signed(get(a[2]))
                v = -1 if y == 0 else int(abs(x) // abs(y)) * (1 if (x >= 0) == (y >= 0) else -1)
                put(a[0], v)
            elif op == "rem":
                x, y = _signed(get(a[1])), _signed(get(a[2]))
                if y == 0:
                    v = x
                else:
                    q = int(abs(x) // abs(y)) * (1 if (x >= 0) == (y >= 0) else -1)
                    v = x - q * y
                put(a[0], v)
            elif op == "addi":
                put(a[0], _signed(get(a[1])) + int(a[2]))
            elif op == "slli":
                put(a[0], get(a[1]) << int(a[2]))
            elif op == "xori":
                put(a[0], get(a[1]) ^ int(a[2]))
            elif op == "slt":
                put(a[0], int(_signed(get(a[1])) < _signed(get(a[2]))))
            elif op == "slti":
                put(a[0], int(_signed(get(a[1])) < int(a[2])))
            elif op == "seqz":
                put(a[0], int(get(a[1]) == 0))
            elif op == "snez":
                put(a[0], int(get(a[1]) != 0))
            elif op == "neg":
                put(a[0], -_signed(get(a[1])))
            elif op in ("lw", "sw", "sb"):
                # "off(base)" operand
                off_s, base = a[1].rstrip(")").split("(")
                addr = (_signed(get(base)) + int(off_s or "0")) & _MASK
                if op == "lw":
                    put(a[0], self._load_word(addr))
                elif op == "sw":
                    self._store_word(addr, get(a[0]))
                else:
                    self._mem[addr] = get(a[0]) & 0xFF
            elif op == "beqz":
                if get(a[0]) == 0:
                    pc = self._labels[a[1]]
                    continue
            elif op == "bnez":
                if get(a[0]) != 0:
                    pc = self._labels[a[1]]
                    continue
            elif op == "j":
                pc = self._labels[a[0]]
                continue
            elif op == "call":
                ra_stack.append(pc + 1)
                pc = self._labels[a[0]]
                continue
            elif op == "ret":
                pc = ra_stack.pop()
                continue
            elif op == "ecall":
                syscall = _signed(get("a7"))
                if syscall == 93:
                    exit_code = _signed(get("a0"))
                    break
                if syscall == 64:  # write(fd, buf, len)
                    buf = _signed(get("a1"))
                    length = _signed(get("a2"))
                    stdout += bytes(
                        self._mem.get(buf + i, 0) for i in range(length)
                    )
                else:
                    raise ValueError(f"Unsupported syscall {syscall}")
            else:
                raise ValueError(f"Unsupported instruction: {op} {a}")

            pc += 1

        return SimResult(
            exit_code=exit_code,
            stdout=stdout.decode("ascii"),
            steps=steps,
        )


def run_assembly(asm: str) -> SimResult:
    """Parse and execute assembly text, returning captured results."""
    return RiscvSimulator(asm).run()
