from Language.compiscriptVisitor import compiscriptVisitor
from Language.compiscriptParser import compiscriptParser
from Model.data_types import *
from Model.object_types import *
from Model.scope import ScopeManager
from Model.symbol_table import Symbol
from Controller.semantic_utils import infer_type

class SemanticAnalyzer(compiscriptVisitor):
    """
    Class that implements the visitor pattern to perform semantic analysis on the parse
    tree generated by the ANTLR parser.

    The semantic analyzer is responsible for creating the symbol table and performing
    type checking on the program.
    """
    def __init__(self):
        self.scope_manager = ScopeManager()  # Create a scope manager

    def visitProgram(self, ctx: compiscriptParser.ProgramContext):
        # Enter the global scope
        print("Entered global scope")
        return self.visitChildren(ctx)
    
    def visitDeclaration(self, ctx: compiscriptParser.DeclarationContext):
        # Check if the declaration is a variable declaration
        if ctx.varDecl() is not None:
            # Visit the variable declaration
            self.visitVarDecl(ctx.varDecl())
        
    def visitVarDecl(self, ctx: compiscriptParser.VarDeclContext):
        # Get the variable identifier
        identifier = ctx.IDENTIFIER().getText()
        print(f"Started variable declaration for var: {identifier}")

        
        # Check if the variable already exists in the current scope
        existing_var = self.scope_manager.get_symbol(identifier, Variable)
        if existing_var is not None:
            # Variable already exists in the current scope
            raise Exception(f"Variable '{identifier}' already exists in the current scope.")
        
        # Create a new variable symbol and add it to the current scope in the symbol table
        variable = Variable(data_type=None) # Initialize the variable without defining its data type
        new_var_symbol = Symbol(name=identifier, obj_type=variable, scope_level=self.scope_manager.current_scope)

        # Add the variable to the current scope
        self.scope_manager.add_symbol(new_var_symbol)
        print(f"Added variable {identifier} to current scope {self.scope_manager.current_scope}")

        # Check if the variable has an initialization expression
        if ctx.expression() is not None:
            # Visit the expression to infer its type
            expression_type = self.visit(ctx.expression())
            variable.data_type = expression_type
            print(f"Inferred type for variable {identifier}: {expression_type}")
        else:
            print(f"No initial value for '{identifier}', type is undefined.")

        # Log the variable declaration
        print(f"Variable '{identifier}' declared with type '{variable.data_type}' in scope {self.scope_manager.current_scope}")


    def visitExpression(self, ctx: compiscriptParser.ExpressionContext):
        if ctx.assignment() is not None:
            return self.visitAssignment(ctx.assignment())
        
    def visitAssignment(self, ctx: compiscriptParser.AssignmentContext):
        if ctx.logic_or() is not None:
            return self.visitLogic_or(ctx.logic_or())
        
    def visitLogic_or(self, ctx: compiscriptParser.Logic_orContext):
        # Initialize the result to the first element of 'logic_and'
        result = self.visitLogic_and(ctx.logic_and(0))

        # Evaluate the rest of the 'logic_and' elements
        for i in range(1, len(ctx.logic_and())):
            logic_and_result = self.visitLogic_and(ctx.logic_and(i))
            result = result or logic_and_result  # Apply the OR operation
            # If the result is True, break the loop
            if result:
                break

        return result

        
    def visitLogic_and(self, ctx: compiscriptParser.Logic_andContext):
        # Initialize the result to the first element of 'equality'
        result = self.visitEquality(ctx.equality(0)) 

        # Evaluate the rest of the 'equality' elements
        for i in range(1, len(ctx.equality())):
            equality_result = self.visitEquality(ctx.equality(i))
            result = result and equality_result  # Apply the AND operation
            # If the result is False, break the loop
            if not result:
                break

        return result


    def visitEquality(self, ctx: compiscriptParser.EqualityContext):
        # Initialize the result to the first element of 'comparison'
        result = self.visitComparison(ctx.comparison(0))

        # Iterate over the rest of the 'comparison' elements
        for i in range(1, len(ctx.comparison())):
            # Get the operator between the comparisons (== or !=)
            operator = ctx.getChild(2 * i - 1).getText()
            
            # Get the result of the comparison
            comparison_result = self.visitComparison(ctx.comparison(i))

            # Determine the result of the equality operation
            if operator == '==':
                result = result == comparison_result
            elif operator == '!=':
                result = result != comparison_result

            # If the result is False, break the loop
            if not result:
                break

        return result


        
    def visitComparison(self, ctx: compiscriptParser.ComparisonContext):
        # Initialize the result to the first element of 'Term'
        result = self.visitTerm(ctx.term(0))

        # Iterate over the rest of the 'Term' elements
        for i in range(1, len(ctx.term())):
            # Get the operator between the terms (<, >, <=, >=)
            operator = ctx.getChild(2 * i - 1).getText()
            
            # Get the result of the term
            term_result = self.visitTerm(ctx.term(i))

            # Determine the result of the comparison operation
            if operator == '<':
                result = result < term_result
            elif operator == '>':
                result = result > term_result
            elif operator == '<=':
                result = result <= term_result
            elif operator == '>=':
                result = result >= term_result

            # If the result is False, break the loop
            if not result:
                break
        
        return result
    
        
    def visitTerm(self, ctx: compiscriptParser.TermContext):
        # Initialize the result to the first element of 'factor'
        result = self.visitFactor(ctx.factor(0))

        # Iterate over the rest of the 'factor' elements
        for i in range(1, len(ctx.factor())):
            # Get the operator between the factors (+, -)
            operator = ctx.getChild(2 * i - 1).getText()
            
            # Get the result of the factor
            factor_result = self.visitFactor(ctx.factor(i))

            # Determine the result of the term operation
            if operator == '+':
                result = result + factor_result
            elif operator == '-':
                result = result - factor_result

        return result
    
        
    def visitFactor(self, ctx: compiscriptParser.FactorContext):
        # Initialize the result to the first element of 'unary'
        result = self.visitUnary(ctx.unary(0))

        # Iterate over the rest of the 'unary' elements
        for i in range(1, len(ctx.unary())):
            # Get the operator between the unary expressions (*, /, %)
            operator = ctx.getChild(2 * i - 1).getText()
            
            # Get the result of the unary expression
            unary_result = self.visitUnary(ctx.unary(i))

            # Determine the result of the factor operation
            if operator == '*':
                result = result * unary_result
            elif operator == '/':
                result = result / unary_result
            elif operator == '%':
                result = result % unary_result

        return result
        
    def visitUnary(self, ctx: compiscriptParser.UnaryContext):
        if ctx.call() is not None:
            return self.visitCall(ctx.call())
        
    def visitCall(self, ctx: compiscriptParser.CallContext):
        if ctx.primary() is not None:
            return self.visitPrimary(ctx.primary())
        
    def visitPrimary(self, ctx: compiscriptParser.PrimaryContext):
        if ctx.NUMBER() is not None:
            return NumType()
        elif ctx.STRING() is not None:
            return StringType()
        elif ctx.getText() == 'true' or ctx.getText() == 'false':
            return BooleanType()
        elif ctx.getText() == 'nil' or ctx.getText() == None:
            return NilType()
        else:
            return "Unknown"