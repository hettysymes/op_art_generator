from ui.nodes.elem_ref import ElemRef


def handle_multi_inputs(elem_nodes, prop_vals_list):
    elem_node_ids = [en.node_id for en in elem_nodes]
    indices_to_remove = []
    for i, elem_ref in enumerate(prop_vals_list):
        if isinstance(elem_ref, ElemRef):
            if elem_ref.node_id in elem_node_ids:
                # Element already exists - mark as not to add
                index = elem_node_ids.index(elem_ref.node_id)
                elem_node_ids[index] = None
            else:
                # Element has been removed
                indices_to_remove.append(i)
    # Remove no longer existing elements
    for i in reversed(indices_to_remove):
        del prop_vals_list[i]
    # Add new elements
    for i, en_id in enumerate(elem_node_ids):
        if en_id is not None:
            prop_vals_list.append(ElemRef(elem_nodes[i]))