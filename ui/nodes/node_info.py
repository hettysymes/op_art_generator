from ui.nodes.nodes import UnitNodeInfo, PropTypeList, PropType
from ui.port_defs import PortDef, PortType

# GRID

GRID_NODE_INFO = UnitNodeInfo(
    name="Grid",
    resizable=True,
    in_port_defs=[PortDef("X Warp", PortType.WARP), PortDef("Y Warp", PortType.WARP)],
    out_port_defs=[PortDef("Grid", PortType.GRID)],
    prop_type_list=PropTypeList(
        [
            PropType("width", "int", default_value=5,
                     description="Number of squares in width of grid"),
            PropType("height", "int", default_value=5,
                     description="Number of squares in height of grid")
        ]
    )
)

# CANVAS

CANVAS_NODE_INFO = UnitNodeInfo(
    name="Canvas",
    resizable=False,
    in_port_defs=[PortDef("Drawing", PortType.VISUALISABLE)],
    out_port_defs=[],
    prop_type_list=PropTypeList([
        PropType("width", "int", default_value=150, max_value=500, min_value=1,
                 description=""),
        PropType("height", "int", default_value=150, max_value=500, min_value=1,
                 description="")
    ])
)

# CHECKERBOARD

CHECKERBOARD_NODE_INFO = UnitNodeInfo(
    name="Checkerboard",
    resizable=True,
    in_port_defs=[
        PortDef("Grid", PortType.GRID),
        PortDef("Drawing 1", PortType.ELEMENT),
        PortDef("Drawing 2", PortType.ELEMENT)
    ],
    out_port_defs=[PortDef("Drawing", PortType.ELEMENT)],
    prop_type_list=PropTypeList([])
)

# FUNCTIONS

CUBIC_FUN_NODE_INFO = UnitNodeInfo(
    name="Cubic Function",
    resizable=True,
    in_port_defs=[],
    out_port_defs=[PortDef("Function", PortType.FUNCTION)],
    prop_type_list=PropTypeList(
        [
            PropType("a_coeff", "float", default_value=3.22,
                     description=""),
            PropType("b_coeff", "float", default_value=-5.41,
                     description=""),
            PropType("c_coeff", "float", default_value=3.20,
                     description=""),
            PropType("d_coeff", "float", default_value=0,
                     description="")
        ]
    )
)

CUSTOM_FUN_NODE_INFO = UnitNodeInfo(
    name="Custom Function",
    resizable=True,
    in_port_defs=[],
    out_port_defs=[PortDef("Function", PortType.FUNCTION)],
    prop_type_list=PropTypeList(
        [
            PropType("fun_def", "string", default_value="x",
                     description="")
        ]
    )
)

PIECEWISE_FUN_NODE_INFO = UnitNodeInfo(
    name="Piecewise Function",
    resizable=True,
    in_port_defs=[],
    out_port_defs=[PortDef("Function", PortType.FUNCTION)],
    prop_type_list=PropTypeList(
        [
            PropType("points", "table", default_value=[(0, 0), (0.5, 0.5), (1, 1)],
                     description="")
        ]
    )
)

# SHAPE REPEATER

SHAPE_REPEATER_NODE_INFO = UnitNodeInfo(
    name="Shape Repeater",
    resizable=True,
    in_port_defs=[
        PortDef("Grid", PortType.GRID),
        PortDef("Drawing", PortType.ELEMENT)
    ],
    out_port_defs=[PortDef("Drawing", PortType.ELEMENT)],
    prop_type_list=PropTypeList([])
)

# WARPS

POS_WARP_NODE_INFO = UnitNodeInfo(
    name="Position Warp",
    resizable=True,
    in_port_defs=[PortDef("Function", PortType.FUNCTION)],
    out_port_defs=[PortDef("Warp", PortType.WARP)],
    prop_type_list=PropTypeList([])
)

REL_WARP_NODE_INFO = UnitNodeInfo(
    name="Relative Warp",
    resizable=True,
    in_port_defs=[PortDef("Function", PortType.FUNCTION)],
    out_port_defs=[PortDef("Warp", PortType.WARP)],
    prop_type_list=PropTypeList([])
)
