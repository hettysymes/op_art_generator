from ui.nodes.elem_ref import ElemRef


def handle_multi_inputs(elem_nodes, prop_vals_list):
    elem_node_ids = [en.node_id for en in elem_nodes]
    print("Polygon points")
    print(elem_node_ids)
    elem_node_add_ids = [True for _ in range(len(elem_nodes))]
    indices_to_remove = []
    for i, elem_ref in enumerate(prop_vals_list):
        if isinstance(elem_ref, ElemRef):
            if elem_ref.node_id in elem_node_ids:
                # Element already exists - mark as not to add
                index = elem_node_ids.index(elem_ref.node_id)
                elem_node_add_ids[index] = False
            else:
                # Element has been removed
                indices_to_remove.append(i)
    # Remove no longer existing elements
    for i in reversed(indices_to_remove):
        del prop_vals_list[i]
    # Add new elements
    for i in range(len(elem_node_ids)):
        if elem_node_add_ids[i]:
            prop_vals_list.append(ElemRef(elem_nodes[i]))
