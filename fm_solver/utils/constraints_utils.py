"""
This module contains all utils related to the management of a cross-tree constraints.
"""

from flamapy.core.models import ASTOperation
from flamapy.metamodels.fm_metamodel.models import Constraint


def is_simple_constraint(constraint: Constraint) -> bool:
    """Return true if the constraint is a simple constraint (requires or excludes)."""
    return is_requires_constraint(constraint) or is_excludes_constraint(constraint)


def is_complex_constraint(constraint: Constraint) -> bool:
    """Return true if the constraint is a complex constraint 
    (i.e., it is not a simple constraint)."""
    return not is_simple_constraint(constraint)


def is_requires_constraint(constraint: Constraint) -> bool:
    """Return true if the constraint is a requires constraint."""
    root_op = constraint.ast.root
    if root_op.is_binary_op():
        if root_op.data in [ASTOperation.REQUIRES, ASTOperation.IMPLIES]:
            return root_op.left.is_term() and root_op.right.is_term()
        elif root_op.data == ASTOperation.OR:
            neg_left = root_op.left.data == ASTOperation.NOT and root_op.left.left.is_term()
            neg_right = root_op.right.data == ASTOperation.NOT and root_op.right.left.is_term()
            return neg_left and root_op.right.is_term() or neg_right and root_op.left.is_term()
    return False


def is_excludes_constraint(constraint: Constraint) -> bool:
    """Return true if the constraint is an excludes constraint."""
    root_op = constraint.ast.root
    if root_op.is_binary_op():
        if root_op.data in [ASTOperation.EXCLUDES, ASTOperation.XOR]:
            return root_op.left.is_term() and root_op.right.is_term()
        elif root_op.data in [ASTOperation.REQUIRES, ASTOperation.IMPLIES]:
            neg_right = root_op.right.data == ASTOperation.NOT and root_op.right.left.is_term()
            return root_op.left.is_term() and neg_right
        elif root_op.data == ASTOperation.OR:
            neg_left = root_op.left.data == ASTOperation.NOT and root_op.left.left.is_term()
            neg_right = root_op.right.data == ASTOperation.NOT and root_op.right.left.is_term()
            return neg_left and neg_right
    return False


def get_new_ctc_name(ctcs_names: list[str], prefix_name: str) -> str:
    """Return a new name for a constraint (based on the provided prefix) that is not already 
    in the given list of constraints' names."""
    count = 1
    new_name = f'{prefix_name}'
    while new_name in ctcs_names:
        new_name = f'{prefix_name}{count}'
        count += 1
    return new_name


def left_right_features_from_simple_constraint(simple_ctc: Constraint) -> tuple[str, str]:
    """Return the names of the features involved in a simple constraint.
    
    A simple constraint can be a requires constraint or an excludes constraint.
    A requires constraint can be represented in the AST of the constraint with one of the 
    following structures:
        A requires B
        A => B
        !A v B
    An excludes constraint can be represented in the AST of the constraint with one of the 
    following structures:
        A excludes B
        A => !B
        !A v !B
    """
    root_op = simple_ctc.ast.root
    if root_op.data in [ASTOperation.REQUIRES, ASTOperation.IMPLIES, ASTOperation.EXCLUDES]:
        left = root_op.left.data
        right = root_op.right.data
        if right == ASTOperation.NOT:
            right = root_op.right.left.data
    elif root_op.data == ASTOperation.OR:
        left = root_op.left.data
        right = root_op.right.data
        if left == ASTOperation.NOT and right == ASTOperation.NOT:  # excludes
            left = root_op.left.left.data
            right = root_op.right.left.data
        elif left == ASTOperation.NOT:  # implies: A -> B
            left = root_op.left.left.data
            right = root_op.right.data
        elif right == ASTOperation.NOT:  # implies: B -> A
            left = root_op.right.left.data
            right = root_op.left.data
    return (left, right)