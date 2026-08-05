"""
IR Generator — translates an AST into Three-Address Code.

Walks the AST recursively, emitting flat IR instructions. Uses
temporary variables (t0, t1, ...) and labels (L0, L1, ...) to
linearize control flow.
"""

from __future__ import annotations

from compiler.ast_nodes import (
    Program, FunctionDecl, Block,
    VarDecl, ArrayDecl, IfStatement, WhileStatement, ForStatement,
    ReturnStatement,
    PrintStatement, ExpressionStatement, Assignment, ArrayAssignment,
    BinaryOp, UnaryOp, NumberLiteral, Identifier, FunctionCall, ArrayAccess,
    ASTNode,
)
from compiler.ir import IRInstruction, IROpcode, OP_TO_OPCODE
from compiler.symbol_table import SymbolTable
from compiler.errors import CompilerError


class IRGeneratorError(CompilerError):
    pass


class IRGenerator:
    """Translates an AST into a list of IRInstructions."""

    def __init__(self) -> None:
        self._instructions: list[IRInstruction] = []
        self._temp_counter: int = 0
        self._label_counter: int = 0
        self._symtab = SymbolTable()
        self._all_symbols: list[dict] = []

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _new_temp(self) -> str:
        name = f"t{self._temp_counter}"
        self._temp_counter += 1
        return name

    def _new_label(self) -> str:
        name = f"L{self._label_counter}"
        self._label_counter += 1
        return name

    def _emit(self, opcode: IROpcode, dest: str | None = None,
              src1: str | None = None, src2: str | None = None) -> None:
        self._instructions.append(IRInstruction(opcode, dest, src1, src2))

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def generate(self, program: Program) -> list[IRInstruction]:
        """Generate IR for an entire program."""
        for glob in program.globals:
            self._gen_global_decl(glob)
        for func in program.functions:
            self._gen_function(func)
        return self._instructions

    def _gen_global_decl(self, node: VarDecl) -> None:
        """Emit a GLOBAL_DECL. Initialiser must be a compile-time constant."""
        value = 0
        if node.init is not None:
            value = self._const_eval(node.init)
        sym = self._symtab.declare(node.name, var_type="global")
        self._all_symbols.append({
            "name": sym.name, "type": "global",
            "scope": sym.scope_depth, "ir_name": sym.ir_name,
        })
        self._emit(IROpcode.GLOBAL_DECL, dest=sym.ir_name, src1=str(value))

    def _const_eval(self, node: ASTNode) -> int:
        """Evaluate a constant initialiser expression (C-style global rule)."""
        if isinstance(node, NumberLiteral):
            return node.value
        if isinstance(node, UnaryOp) and node.op == "-":
            return -self._const_eval(node.operand)
        raise IRGeneratorError(
            f"Global initializer must be a constant expression "
            f"(at L{node.line}:{node.col})"
        )

    def generate_with_symbols(self, program: Program) -> tuple[list[IRInstruction], list[dict]]:
        """Generate IR and return accumulated symbol information."""
        self._all_symbols = []
        instructions = self.generate(program)
        return instructions, self._all_symbols

    # ------------------------------------------------------------------
    # Functions
    # ------------------------------------------------------------------

    def _gen_function(self, func: FunctionDecl) -> None:
        self._emit(IROpcode.FUNC_BEGIN, dest=func.name)
        self._symtab.enter_scope()

        # Declare parameters and emit FUNC_PARAM instructions
        for param in func.params:
            sym = self._symtab.declare(param.name)
            self._all_symbols.append({
                "name": sym.name, "type": "int",
                "scope": sym.scope_depth, "ir_name": sym.ir_name,
            })
            self._emit(IROpcode.FUNC_PARAM, dest=sym.ir_name)

        self._gen_block(func.body)

        self._symtab.exit_scope()
        self._emit(IROpcode.FUNC_END, dest=func.name)

    # ------------------------------------------------------------------
    # Statements
    # ------------------------------------------------------------------

    def _gen_block(self, block: Block) -> None:
        self._symtab.enter_scope()
        for stmt in block.statements:
            self._gen_statement(stmt)
        self._symtab.exit_scope()

    def _gen_statement(self, node: ASTNode) -> None:
        if isinstance(node, VarDecl):
            self._gen_var_decl(node)
        elif isinstance(node, ArrayDecl):
            self._gen_array_decl(node)
        elif isinstance(node, Assignment):
            self._gen_assignment(node)
        elif isinstance(node, ArrayAssignment):
            self._gen_array_assignment(node)
        elif isinstance(node, IfStatement):
            self._gen_if(node)
        elif isinstance(node, WhileStatement):
            self._gen_while(node)
        elif isinstance(node, ForStatement):
            self._gen_for(node)
        elif isinstance(node, ReturnStatement):
            self._gen_return(node)
        elif isinstance(node, PrintStatement):
            self._gen_print(node)
        elif isinstance(node, ExpressionStatement):
            self._gen_expr(node.expr)  # result discarded
        elif isinstance(node, Block):
            self._gen_block(node)
        else:
            raise IRGeneratorError(f"Unknown statement type: {type(node).__name__}")

    def _gen_var_decl(self, node: VarDecl) -> None:
        sym = self._symtab.declare(node.name)
        self._all_symbols.append({
            "name": sym.name, "type": sym.var_type,
            "scope": sym.scope_depth, "ir_name": sym.ir_name,
        })
        if node.init is not None:
            val = self._gen_expr(node.init)
            self._emit(IROpcode.COPY, dest=sym.ir_name, src1=val)
        else:
            # Default-initialise to 0
            self._emit(IROpcode.LOAD_CONST, dest=sym.ir_name, src1="0")

    def _gen_array_decl(self, node: ArrayDecl) -> None:
        sym = self._symtab.declare(node.name, var_type="array", array_size=node.size)
        self._all_symbols.append({
            "name": sym.name, "type": sym.var_type,
            "scope": sym.scope_depth, "ir_name": sym.ir_name,
            "array_size": sym.array_size,
        })
        self._emit(IROpcode.ARR_DECL, dest=sym.ir_name, src1=str(node.size))

    def _gen_assignment(self, node: Assignment) -> None:
        sym = self._symtab.lookup(node.name)
        val = self._gen_expr(node.value)
        if sym.var_type == "global":
            self._emit(IROpcode.GLOBAL_STORE, dest=sym.ir_name, src1=val)
        else:
            self._emit(IROpcode.COPY, dest=sym.ir_name, src1=val)

    def _gen_array_assignment(self, node: ArrayAssignment) -> None:
        sym = self._symtab.lookup(node.name)
        index = self._gen_expr(node.index)
        val = self._gen_expr(node.value)
        self._emit(IROpcode.ARR_STORE, dest=sym.ir_name, src1=index, src2=val)

    def _gen_if(self, node: IfStatement) -> None:
        cond = self._gen_expr(node.condition)

        if node.else_block:
            else_label = self._new_label()
            end_label = self._new_label()
            self._emit(IROpcode.JUMP_IF_FALSE, dest=else_label, src1=cond)
            self._gen_block(node.then_block)
            self._emit(IROpcode.JUMP, dest=end_label)
            self._emit(IROpcode.LABEL, dest=else_label)
            self._gen_block(node.else_block)
            self._emit(IROpcode.LABEL, dest=end_label)
        else:
            end_label = self._new_label()
            self._emit(IROpcode.JUMP_IF_FALSE, dest=end_label, src1=cond)
            self._gen_block(node.then_block)
            self._emit(IROpcode.LABEL, dest=end_label)

    def _gen_while(self, node: WhileStatement) -> None:
        loop_label = self._new_label()
        end_label = self._new_label()
        self._emit(IROpcode.LABEL, dest=loop_label)
        cond = self._gen_expr(node.condition)
        self._emit(IROpcode.JUMP_IF_FALSE, dest=end_label, src1=cond)
        self._gen_block(node.body)
        self._emit(IROpcode.JUMP, dest=loop_label)
        self._emit(IROpcode.LABEL, dest=end_label)

    def _gen_for(self, node: ForStatement) -> None:
        """Lower `for (init; cond; update) body` to labels and jumps.

        The init clause runs once inside its own scope; an empty
        condition means the loop only exits via the body's control flow.
        """
        self._symtab.enter_scope()
        if node.init is not None:
            self._gen_statement(node.init)

        loop_label = self._new_label()
        end_label = self._new_label()
        self._emit(IROpcode.LABEL, dest=loop_label)
        if node.condition is not None:
            cond = self._gen_expr(node.condition)
            self._emit(IROpcode.JUMP_IF_FALSE, dest=end_label, src1=cond)
        self._gen_block(node.body)
        if node.update is not None:
            self._gen_statement(node.update)
        self._emit(IROpcode.JUMP, dest=loop_label)
        self._emit(IROpcode.LABEL, dest=end_label)
        self._symtab.exit_scope()

    def _gen_return(self, node: ReturnStatement) -> None:
        if node.value:
            val = self._gen_expr(node.value)
            self._emit(IROpcode.RETURN, src1=val)
        else:
            self._emit(IROpcode.RETURN)

    def _gen_print(self, node: PrintStatement) -> None:
        val = self._gen_expr(node.value)
        self._emit(IROpcode.PRINT, src1=val)

    # ------------------------------------------------------------------
    # Expressions — each returns the name of the temp/var holding the result
    # ------------------------------------------------------------------

    def _gen_expr(self, node: ASTNode) -> str:
        if isinstance(node, NumberLiteral):
            tmp = self._new_temp()
            self._emit(IROpcode.LOAD_CONST, dest=tmp, src1=str(node.value))
            return tmp

        if isinstance(node, Identifier):
            sym = self._symtab.lookup(node.name)
            if sym.var_type == "global":
                tmp = self._new_temp()
                self._emit(IROpcode.GLOBAL_LOAD, dest=tmp, src1=sym.ir_name)
                return tmp
            return sym.ir_name

        if isinstance(node, ArrayAccess):
            sym = self._symtab.lookup(node.name)
            index = self._gen_expr(node.index)
            tmp = self._new_temp()
            self._emit(IROpcode.ARR_LOAD, dest=tmp, src1=sym.ir_name, src2=index)
            return tmp

        if isinstance(node, BinaryOp):
            if node.op in ("&&", "||"):
                return self._gen_short_circuit(node)
            left = self._gen_expr(node.left)
            right = self._gen_expr(node.right)
            tmp = self._new_temp()
            opcode = OP_TO_OPCODE.get(node.op)
            if opcode is None:
                raise IRGeneratorError(f"Unknown binary operator: {node.op}")
            self._emit(opcode, dest=tmp, src1=left, src2=right)
            return tmp

        if isinstance(node, UnaryOp):
            operand = self._gen_expr(node.operand)
            tmp = self._new_temp()
            if node.op == "-":
                self._emit(IROpcode.NEG, dest=tmp, src1=operand)
            elif node.op == "!":
                self._emit(IROpcode.NOT, dest=tmp, src1=operand)
            else:
                raise IRGeneratorError(f"Unknown unary operator: {node.op}")
            return tmp

        if isinstance(node, FunctionCall):
            # Evaluate arguments and emit PARAM instructions
            arg_temps = [self._gen_expr(arg) for arg in node.args]
            for at in arg_temps:
                self._emit(IROpcode.PARAM, src1=at)
            tmp = self._new_temp()
            self._emit(IROpcode.CALL, dest=tmp, src1=node.name, src2=str(len(node.args)))
            return tmp

        if isinstance(node, Assignment):
            # Assignment used as expression
            sym = self._symtab.lookup(node.name)
            val = self._gen_expr(node.value)
            if sym.var_type == "global":
                self._emit(IROpcode.GLOBAL_STORE, dest=sym.ir_name, src1=val)
                return val
            self._emit(IROpcode.COPY, dest=sym.ir_name, src1=val)
            return sym.ir_name

        raise IRGeneratorError(f"Unknown expression type: {type(node).__name__}")

    def _gen_short_circuit(self, node: BinaryOp) -> str:
        """Lower && and || with C short-circuit semantics.

        The right operand is only evaluated when the left operand does
        not already determine the result. The result is normalised to
        0/1 via a `!= 0` comparison, matching the eager AND/OR opcodes.
        """
        tmp = self._new_temp()
        skip_label = self._new_label()
        end_label = self._new_label()

        left = self._gen_expr(node.left)
        if node.op == "&&":
            self._emit(IROpcode.JUMP_IF_FALSE, dest=skip_label, src1=left)
        else:  # ||
            self._emit(IROpcode.JUMP_IF_TRUE, dest=skip_label, src1=left)

        right = self._gen_expr(node.right)
        self._emit(IROpcode.NEQ, dest=tmp, src1=right, src2="0")
        self._emit(IROpcode.JUMP, dest=end_label)

        self._emit(IROpcode.LABEL, dest=skip_label)
        short_value = "0" if node.op == "&&" else "1"
        self._emit(IROpcode.LOAD_CONST, dest=tmp, src1=short_value)
        self._emit(IROpcode.LABEL, dest=end_label)
        return tmp


def generate_ir(program: Program) -> list[IRInstruction]:
    """Convenience: generate IR from an AST in one call."""
    return IRGenerator().generate(program)
