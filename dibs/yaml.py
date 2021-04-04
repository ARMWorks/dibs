from ruamel.yaml import YAML

from dibs.multidict import MultiDict

def _constr_dict(constructor, node):
    md = MultiDict()
    for key_node, value_node in node.value:
        key = constructor.construct_object(key_node)
        value = constructor.construct_object(value_node)
        md.append(key, value)
    return md

def _repr_dict(representer, data):
    return representer.represent_mapping(
        yaml.resolver.DEFAULT_MAPPING_TAG, data)

yaml = YAML()
yaml.constructor.add_constructor(yaml.resolver.DEFAULT_MAPPING_TAG,
        _constr_dict)
yaml.representer.add_representer(MultiDict, _repr_dict)
