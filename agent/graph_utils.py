def find_node(graph, cls, in_room=None):
    candidates = [n for n in graph['nodes'] if n['class_name'].lower() == cls.lower()]
    if in_room:
        room_ids = {n['id'] for n in graph['nodes'] if n['class_name'].lower() == in_room.lower()}
        inside_ids = {e['from_id'] for e in graph['edges'] if e['relation_type']=='INSIDE' and e['to_id'] in room_ids}
        candidates = [n for n in candidates if n['id'] in inside_ids]
    return candidates[0] if candidates else None

def find_all(graph, cls):
    return [n for n in graph['nodes'] if n['class_name'].lower() == cls.lower()]

def clean_graph(graph):
    new_nodes = []
    for n in graph['nodes']:
        nc = dict(n)
        if 'bounding_box' in nc:
            del nc['bounding_box']
        new_nodes.append(nc)
    return {'nodes': new_nodes, 'edges': list(graph['edges'])}

def move_item_in_graph(graph, node_id, new_relation, new_target_id):
    # Remove old ON/INSIDE relations
    graph['edges'] = [e for e in graph['edges'] if not (e['from_id'] == node_id and e['relation_type'] in ['ON', 'INSIDE'])]
    
    # Add new relation
    graph['edges'].append({'from_id': node_id, 'relation_type': new_relation, 'to_id': new_target_id})
    
    # Add INSIDE room relation if target is in a room
    room_id = None
    current_target = new_target_id
    visited = set()
    while current_target and current_target not in visited:
        visited.add(current_target)
        target_node = next((n for n in graph['nodes'] if n['id'] == current_target), None)
        if target_node and target_node['category'] == 'Rooms':
            room_id = current_target
            break
        parent_edges = [e for e in graph['edges'] if e['from_id'] == current_target and e['relation_type'] in ['ON', 'INSIDE']]
        if parent_edges:
            current_target = parent_edges[0]['to_id']
        else:
            break
    
    if room_id:
        graph['edges'].append({'from_id': node_id, 'relation_type': 'INSIDE', 'to_id': room_id})

def add_virtual_item(graph, class_name, relation, target_id):
    max_id = max(n['id'] for n in graph['nodes']) if graph['nodes'] else 0
    new_id = max_id + 1
    
    existing = next((n for n in graph['nodes'] if n['class_name'] == class_name), None)
    cat = existing['category'] if existing else 'Decor'
    
    graph['nodes'].append({'id': new_id, 'class_name': class_name, 'category': cat, 'states': []})
    move_item_in_graph(graph, new_id, relation, target_id)
    return new_id

