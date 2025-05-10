from ui.nodes.port_defs import PortRefTableEntry


def handle_port_ref_table(ref_data, port_ref_table, entry_class=PortRefTableEntry):
    ref_data = ref_data if ref_data else {} # Handle None case
    # Update port ref table
    ref_ids_to_add = list(ref_data.keys())
    indices_to_remove = []
    for i, table_entry in enumerate(port_ref_table):
        if not isinstance(table_entry, PortRefTableEntry): continue
        if table_entry.ref_id in ref_data:
            # Ref already exists - do not add again but update ref data
            if table_entry.ref_id in ref_ids_to_add:
                ref_ids_to_add.remove(table_entry.ref_id)
            port_ref_table[i] = entry_class(table_entry.ref_id, table_entry.deletable, ref_data[table_entry.ref_id], table_entry.own_data)
        else:
            # Ref has been removed
            indices_to_remove.append(i)
    # Remove no longer existing refs
    for i in reversed(indices_to_remove):
        del port_ref_table[i]
    # Add new refs
    for ref_id in ref_ids_to_add:
        port_ref_table.append(entry_class(ref_id, False, ref_data[ref_id]))
    # Return flattened port data list
    return flatten_list(
        [entry.port_data if isinstance(entry, PortRefTableEntry) else entry for entry in port_ref_table]
    )

def flatten_list(lst):
    return [item for sublist in lst for item in (sublist if isinstance(sublist, list) else [sublist])]