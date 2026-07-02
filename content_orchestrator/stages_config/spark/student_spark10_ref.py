def run_graph_operation(graph, operation, param=None):
    """Run a GraphX-style operation on Python graph data."""
    if not isinstance(graph, dict):
        raise TypeError("graph must be a dict")
    if not isinstance(operation, str):
        raise TypeError("operation must be a string")
    vertices = graph.get("vertices", [])
    edges = graph.get("edges", [])

    if operation == "num_vertices":
        return len(vertices)
    if operation == "num_edges":
        return len(edges)
    if operation == "out_degree":
        return sum(1 for src, _ in edges if src == param)
    if operation == "in_degree":
        return sum(1 for _, dst in edges if dst == param)
    if operation == "top_out_degree":
        counts = {vertex: sum(1 for src, _ in edges if src == vertex) for vertex in vertices}
        return [[vertex, degree] for vertex, degree in sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:param]]
    if operation == "triplets":
        attrs = graph.get("attrs", {})
        return [
            f"{attrs.get(str(src), attrs.get(src, src))}->{attrs.get(str(dst), attrs.get(dst, dst))}"
            for src, dst in edges
        ]
    if operation == "connected_components_count":
        seen = set()
        count = 0
        adjacency = {vertex: set() for vertex in vertices}
        for src, dst in edges:
            adjacency.setdefault(src, set()).add(dst)
            adjacency.setdefault(dst, set()).add(src)
        for vertex in vertices:
            if vertex in seen:
                continue
            count += 1
            stack = [vertex]
            while stack:
                current = stack.pop()
                if current in seen:
                    continue
                seen.add(current)
                stack.extend(adjacency.get(current, set()) - seen)
        return count
    if operation == "aggregate_messages_length":
        return len({dst for _, dst in edges})
    if operation == "neighbors":
        return sorted(dst for src, dst in edges if src == param)
    if operation == "has_direct_edge":
        return param in edges
    if operation == "isolated_vertices":
        touched = {node for edge in edges for node in edge}
        return sorted(vertex for vertex in vertices if vertex not in touched)
    return {"error": "unsupported_operation"}
