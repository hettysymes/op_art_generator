def handle_port_ref_table(ref_data, port_ref_table):
    ref_data = ref_data if ref_data else {} # Handle None case
    # Update port ref table
    ref_ids_to_add = list(ref_data.keys())
    indices_to_remove = []
    for i, (ref_id, _, deletable) in enumerate(port_ref_table):
        if ref_id in ref_data:
            # Ref already exists - do not add again but update ref data
            if ref_id in ref_ids_to_add:
                ref_ids_to_add.remove(ref_id)
            port_ref_table[i] = (ref_id, ref_data[ref_id], deletable)
        else:
            # Ref has been removed
            indices_to_remove.append(i)
    # Remove no longer existing refs
    for i in reversed(indices_to_remove):
        del port_ref_table[i]
    # Add new refs
    for ref_id in ref_ids_to_add:
        port_ref_table.append((ref_id, ref_data[ref_id], False))