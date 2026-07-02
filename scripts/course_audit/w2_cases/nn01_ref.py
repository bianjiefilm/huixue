def count_dense_parameters(layer_sizes):
    if not isinstance(layer_sizes, list):
        raise TypeError("layer_sizes must be list")
    if not layer_sizes:
        raise ValueError("layer_sizes required")
    return sum(layer_sizes[i] * layer_sizes[i + 1] + layer_sizes[i + 1] for i in range(len(layer_sizes) - 1))


def classify_input_modality(shape):
    if not isinstance(shape, (list, tuple)):
        raise TypeError("shape must be list")
    if not shape:
        raise ValueError("shape required")
    if len(shape) == 1:
        return "tabular"
    if len(shape) == 2:
        return "sequence"
    if len(shape) == 3:
        return "image"
    if len(shape) == 4:
        return "video"
    raise ValueError("unsupported rank")


def compute_data_split_sizes(total, ratios):
    if not isinstance(total, int):
        raise TypeError("total must be int")
    if not isinstance(ratios, list):
        raise TypeError("ratios must be list")
    if total < 0:
        raise ValueError("total must be non-negative")
    if abs(sum(ratios) - 1.0) > 1e-9:
        raise ValueError("ratios must sum to 1")
    sizes = [int(total * r) for r in ratios]
    if sizes:
        sizes[-1] += total - sum(sizes)
    return sizes


def estimate_param_size_mb(param_count):
    if not isinstance(param_count, int):
        raise TypeError("param_count must be int")
    if param_count < 0:
        raise ValueError("param_count must be non-negative")
    return param_count * 4 / (1024 * 1024)
