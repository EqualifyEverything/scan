def fix_axe(response_dict, mapping):
processed = {}
for key, value in response_dict.items():
    if isinstance(value, dict):
        for inner_key, inner_value in value.items():
            combined_key = f"{key}.{inner_key}"
            new_key = mapping.get(combined_key)
            if new_key:
                processed[new_key] = inner_value
            else:
                processed[combined_key] = inner_value
    else:
        new_key = mapping.get(key)
        if new_key:
            processed[new_key] = value
        else:
            processed[key] = value
return processed
