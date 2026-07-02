import json
import xml.etree.ElementTree as ET


def parse_structured_data(payload, path=None):
    """Parse JSON or XML text and optionally extract a dotted JSON path."""
    if not isinstance(payload, str):
        raise TypeError("payload must be a string")
    if path is not None and not isinstance(path, str):
        raise TypeError("path must be a string or None")

    text = payload.strip()
    if not text:
        return None

    if text.startswith("{") or text.startswith("["):
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            return {"error": "invalid_json"}
        if path in (None, ""):
            return data
        current = data
        for part in path.split("."):
            if isinstance(current, dict):
                if part not in current:
                    return {"error": "path_not_found"}
                current = current[part]
            elif isinstance(current, list):
                if not part.isdigit():
                    return {"error": "path_not_found"}
                index = int(part)
                if index < 0 or index >= len(current):
                    return {"error": "path_not_found"}
                current = current[index]
            else:
                return {"error": "path_not_found"}
        return current

    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        return {"error": "invalid_format"}

    products = []
    for product in root.findall(".//product"):
        price_node = product.find("price")
        products.append(
            {
                "id": product.attrib.get("id", ""),
                "name": (product.findtext("name") or "").strip(),
                "price": float(price_node.text.strip()) if price_node is not None and price_node.text else None,
                "currency": price_node.attrib.get("currency", "") if price_node is not None else "",
                "specs": {},
                "tags": [],
            }
        )
    if products:
        return products

    children = list(root)
    if not children:
        return []
    return [{child.tag: (child.text or "").strip()} for child in children]
