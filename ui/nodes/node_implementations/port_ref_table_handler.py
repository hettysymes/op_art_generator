from ui.nodes.prop_defs import PortRefTableEntry


def handle_port_ref_table(ref_data, port_ref_table):
    ref_data = ref_data if ref_data else {} # Handle None case
    # Update port ref table
    ref_ids_to_add = list(ref_data.keys())
    indices_to_remove = []
    for i, table_entry in enumerate(port_ref_table):
        if not table_entry.ref_id: continue
        if table_entry.ref_id in ref_data:
            # Ref already exists - do not add again but update ref data
            if table_entry.ref_id in ref_ids_to_add:
                ref_ids_to_add.remove(table_entry.ref_id)
            port_ref_table[i] = PortRefTableEntry(table_entry.ref_id, table_entry.deletable, data=ref_data[table_entry.ref_id])
        else:
            # Ref has been removed
            indices_to_remove.append(i)
    # Remove no longer existing refs
    for i in reversed(indices_to_remove):
        del port_ref_table[i]
    # Add new refs
    for ref_id in ref_ids_to_add:
        port_ref_table.append(PortRefTableEntry(ref_id, False, data=ref_data[ref_id]))