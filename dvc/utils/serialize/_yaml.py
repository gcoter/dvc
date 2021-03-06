import io
from collections import OrderedDict
from contextlib import contextmanager

from funcy import reraise
from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError

from ._common import ParseError, _dump_data, _load_data, _modify_data


class YAMLFileCorruptedError(ParseError):
    def __init__(self, path):
        super().__init__(path, "YAML file structure is corrupted")


def load_yaml(path, tree=None):
    return _load_data(path, parser=parse_yaml, tree=tree)


def parse_yaml(text, path, typ="safe"):
    yaml = YAML(typ=typ)
    with reraise(YAMLError, YAMLFileCorruptedError(path)):
        return yaml.load(text) or {}


def parse_yaml_for_update(text, path):
    """Parses text into Python structure.

    Unlike `parse_yaml()` this returns ordered dicts, values have special
    attributes to store comments and line breaks. This allows us to preserve
    all of those upon dump.

    This one is, however, several times slower than simple `parse_yaml()`.
    """
    return parse_yaml(text, path, typ="rt")


def _get_yaml():
    yaml = YAML()
    yaml.default_flow_style = False

    # tell Dumper to represent OrderedDict as normal dict
    yaml_repr_cls = yaml.Representer
    yaml_repr_cls.add_representer(OrderedDict, yaml_repr_cls.represent_dict)
    return yaml


def _dump(data, stream):
    yaml = _get_yaml()
    return yaml.dump(data, stream)


def dump_yaml(path, data, tree=None):
    return _dump_data(path, data, dumper=_dump, tree=tree)


def loads_yaml(s, typ="safe"):
    return YAML(typ=typ).load(s)


def dumps_yaml(d):
    stream = io.StringIO()
    _dump(d, stream)
    return stream.getvalue()


@contextmanager
def modify_yaml(path, tree=None):
    with _modify_data(path, parse_yaml_for_update, dump_yaml, tree=tree) as d:
        yield d
