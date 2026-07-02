def classify_cv_task(input_shape, output_type):
    if not isinstance(input_shape, (list, tuple)):
        raise TypeError("input_shape must be list or tuple")
    if not isinstance(output_type, str):
        raise TypeError("output_type must be str")
    if len(input_shape) != 3:
        raise ValueError("input_shape must have length 3")
    mapping = {
        "label": "classification",
        "boxes": "detection",
        "mask": "pixel_annotation",
        "id": "recognition",
    }
    if output_type not in mapping:
        raise ValueError("invalid output_type")
    return mapping[output_type]


def compute_image_size_bytes(width, height, channels, bytes_per_pixel=1):
    for value in (width, height, channels, bytes_per_pixel):
        if not isinstance(value, int) or isinstance(value, bool):
            raise TypeError("all dimensions must be int")
        if value <= 0:
            raise ValueError("all dimensions must be positive")
    return width * height * channels * bytes_per_pixel


def resize_aspect_ratio(orig_w, orig_h, target_max_dim):
    for value in (orig_w, orig_h, target_max_dim):
        if not isinstance(value, int) or isinstance(value, bool):
            raise TypeError("all dimensions must be int")
        if value <= 0:
            raise ValueError("all dimensions must be positive")
    ratio = target_max_dim / max(orig_w, orig_h)
    return (round(orig_w * ratio), round(orig_h * ratio))


def normalize_pixel_array(values, max_value=255):
    if not isinstance(values, list):
        raise TypeError("values must be list")
    if not values:
        raise ValueError("values must not be empty")
    if not isinstance(max_value, int) or isinstance(max_value, bool):
        raise TypeError("max_value must be int")
    if max_value <= 0:
        raise ValueError("max_value must be positive")
    result = []
    for value in values:
        if not isinstance(value, int) or isinstance(value, bool):
            raise TypeError("pixel values must be int")
        if value < 0 or value > max_value:
            raise ValueError("pixel value out of range")
        result.append(value / max_value)
    return result
