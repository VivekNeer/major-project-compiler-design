"""
IR Generator — translates an AST into Three-Address Code.

Walks the AST recursively, emitting flat IR instructions. Uses
temporary variables (t0, t1, ...) and labels (L0, L1, ...) to
linearize control flow.
"""

from __future__ import annotations

from compiler.ast_nodes import (
    Program, FunctionDecl, Block,
    VarDecl, IfStatement, WhileStatement, ReturnStatement,
    PrintStatement, ExpressionStatement, Assignment,
    BinaryOp, UnaryOp, NumberLiteral, Identifier, FunctionCall,
    ASTNode,
)
from compiler.ir import IRInstruction, IROpcode, OP_TO_OPCODE
from compiler.symbol_table import SymbolTable


class IRGeneratorError(Exception):
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
        for func in program.functions:
            self._gen_function(func)
        return self._instructions

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
        elif isinstance(node, Assignment):
            self._gen_assignment(node)
        elif isinstance(node, IfStatement):
            self._gen_if(node)
        elif isinstance(node, WhileStatement):
            self._gen_while(node)
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

    def _gen_assignment(self, node: Assignment) -> None:
        sym = self._symtab.lookup(node.name)
        val = self._gen_expr(node.value)
        self._emit(IROpcode.COPY, dest=sym.ir_name, src1=val)

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
            return sym.ir_name

        if isinstance(node, BinaryOp):
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
            self._emit(IROpcode.COPY, dest=sym.ir_name, src1=val)
            return sym.ir_name

        raise IRGeneratorError(f"Unknown expression type: {type(node).__name__}")


def generate_ir(program: Program) -> list[IRInstruction]:
    """Convenience: generate IR from an AST in one call."""
    return IRGenerator().generate(program)
