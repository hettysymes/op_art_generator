from typing import Optional

from id_datatypes import PropKey
from nodes.drawers.draw_graph import create_graph_svg
from nodes.node_defs import PrivateNodeInfo, ResolvedProps, PropDef, PortStatus, NodeCategory, DisplayStatus
from nodes.node_implementations.visualiser import visualise_by_type
from nodes.nodes import AnimatableNode
from nodes.prop_types import PT_List, PT_Number, PT_Enum
from nodes.prop_values import PropValue, List, Enum
from vis_types import Visualisable, MatplotlibFig

DEF_ANIMATOR_INFO = PrivateNodeInfo(
    description="Animate.",
    prop_defs={
        'val_list': PropDef(
            prop_type=PT_List(),
            input_port_status=PortStatus.COMPULSORY,
            output_port_status=PortStatus.FORBIDDEN,
            display_status=DisplayStatus.NO_DISPLAY
        ),
        'iter_type_enum': PropDef(
            prop_type=PT_Enum(),
            display_name="Iteration Type",
            description="When reaching the end of the list, the animation can either 'reflect' back (i.e. ABCBA) or cycle back from the start (i.e. ABCABC).",
            default_value=Enum([True, False], ["Reflective", "Cyclic"]),
            input_port_status=PortStatus.FORBIDDEN,
            output_port_status=PortStatus.FORBIDDEN
        ),
        '_main': PropDef(
            input_port_status=PortStatus.FORBIDDEN,
            output_port_status=PortStatus.COMPULSORY,
            display_name="List item",
            display_status=DisplayStatus.NO_DISPLAY
        )
    }
)


class AnimatorNode(AnimatableNode):
    NAME = "List Animator"
    NODE_CATEGORY = NodeCategory.ANIMATOR
    DEFAULT_NODE_INFO = DEF_ANIMATOR_INFO

    def __init__(self, internal_props: Optional[dict[PropKey, PropValue]] = None, add_info=None):
        self._curr_idx = None
        self._right_dir = None
        self._reset_idx()
        super().__init__(internal_props, add_info)

    def _reset_idx(self):
        self._curr_idx = 0
        self._right_dir = True

    def compute(self, props: ResolvedProps, *args):
        val_list: List = props.get('val_list')
        if not val_list:
            return {}
        # Reset curr index if necessary
        if self._curr_idx >= len(val_list):
            self._reset_idx()
        output = val_list[self._curr_idx]
        old_idx = self._curr_idx

        if self.tick_reanimate():
            if props.get('iter_type_enum').selected_option:
                # Reverse direction at boundaries and update index
                if self._curr_idx == 0:
                    self._right_dir = True
                elif self._curr_idx == len(val_list) - 1:
                    self._right_dir = False
            else:
                self._right_dir = True
            self._curr_idx += 1 if self._right_dir else -1

        return {'_main': output, 'curr_index': old_idx, 'val_list': val_list}

    def visualise(self, compute_results: dict[PropKey, PropValue]) -> Optional[Visualisable]:
        output = compute_results.get('_main')
        val_list: List = compute_results.get('val_list')
        if output is not None:
            if isinstance(val_list.item_type, PT_Number):
                return MatplotlibFig(
                    create_graph_svg(val_list.items, scatter=True, highlight_index=compute_results.get('curr_index')))
            return visualise_by_type(output, output.type)
        return None
