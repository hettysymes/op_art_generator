import sympy as sp

from nodes.function_datatypes import CubicFun, CustomFun, PiecewiseFun
from nodes.node_defs import PrivateNodeInfo, ResolvedProps, PropDef, PortStatus, NodeCategory, DisplayStatus
from nodes.nodes import UnitNode, CombinationNode
from nodes.prop_types import PT_Function, PT_Number, PT_String, PT_PointsHolder, PT_List
from nodes.prop_values import List, Float, Point

DEF_CUBIC_FUN_INFO = PrivateNodeInfo(
    description="Define a cubic function.",
    prop_defs={
        '_main': PropDef(
            prop_type=PT_Function(),
            display_name="Function",
            input_port_status=PortStatus.FORBIDDEN,
            output_port_status=PortStatus.COMPULSORY,
            display_status=DisplayStatus.NO_DISPLAY
        ),
        'a_coeff': PropDef(
            prop_type=PT_Number(),
            display_name="x³ coefficient",
            description="x³ coefficient (i.e. a in the expression ax³ + bx² + cx + d).",
            default_value=Float(3.22)
        ),
        'b_coeff': PropDef(
            prop_type=PT_Number(),
            display_name="x² coefficient",
            description="x² coefficient (i.e. b in the expression ax³ + bx² + cx + d).",
            default_value=Float(-5.41)
        ),
        'c_coeff': PropDef(
            prop_type=PT_Number(),
            display_name="x coefficient",
            description="x coefficient ( i.e. c in the expression ax³ + bx² + cx + d).",
            default_value=Float(3.20)
        ),
        'd_coeff': PropDef(
            prop_type=PT_Number(),
            display_name="Constant",
            description="Constant (i.e. d in the expression ax³ + bx² + cx + d).",
            default_value=Float(0)
        )
    }
)


class CubicFunNode(UnitNode):
    NAME = "Cubic Function"
    NODE_CATEGORY = NodeCategory.BASE_PROPERTY
    DEFAULT_NODE_INFO = DEF_CUBIC_FUN_INFO

    def compute(self, props: ResolvedProps, *args):
        return {'_main':
                    CubicFun(props.get('a_coeff'), props.get('b_coeff'), props.get('c_coeff'),
                             props.get('d_coeff'))}


DEF_CUSTOM_FUN_INFO = PrivateNodeInfo(
    description="Define a custom function by entering an equation in terms of x.",
    prop_defs={
        '_main': PropDef(
            prop_type=PT_Function(),
            display_name="Function",
            input_port_status=PortStatus.FORBIDDEN,
            output_port_status=PortStatus.COMPULSORY,
            display_status=DisplayStatus.NO_DISPLAY
        ),
        'fun_def': PropDef(
            prop_type=PT_String(),
            display_name="f(x) =",
            description="Custom function f(x) defined in terms of x.",
            auto_format=False
        )
    }
)


class CustomFunNode(UnitNode):
    NAME = "Custom Function"
    NODE_CATEGORY = NodeCategory.BASE_PROPERTY
    DEFAULT_NODE_INFO = DEF_CUSTOM_FUN_INFO

    def compute(self, props: ResolvedProps, *args):
        x = sp.symbols('x')
        parsed_expr = sp.sympify(props.get('fun_def'))
        return {'_main': CustomFun(x, parsed_expr)}


DEF_PIECEWISE_FUN_INFO = PrivateNodeInfo(
    description="Define a piecewise linear function by entering points the function passes through.",
    prop_defs={
        '_main': PropDef(
            prop_type=PT_Function(),
            display_name="Function",
            input_port_status=PortStatus.FORBIDDEN,
            output_port_status=PortStatus.COMPULSORY,
            display_status=DisplayStatus.NO_DISPLAY
        ),
        'points': PropDef(
            prop_type=PT_List(PT_PointsHolder(), input_multiple=True),
            display_name="Points",
            description="Points defining where the piecewise linear function passes through.",
            default_value=List(PT_PointsHolder(), [Point(0, 0), Point(0.5, 0.5), Point(1, 1)]),
            input_port_status=PortStatus.FORBIDDEN
        )
    }
)


class PiecewiseFunNode(UnitNode):
    NAME = "Piecewise Linear Function"
    NODE_CATEGORY = NodeCategory.BASE_PROPERTY
    DEFAULT_NODE_INFO = DEF_PIECEWISE_FUN_INFO

    def compute(self, props: ResolvedProps, *args):
        xs, ys = zip(*props.get('points'))
        return {'_main': PiecewiseFun(xs, ys)}


class FunctionNode(CombinationNode):
    NAME = "Function"
    NODE_CATEGORY = NodeCategory.BASE_PROPERTY
    SELECTIONS = [CubicFunNode, PiecewiseFunNode, CustomFunNode]
