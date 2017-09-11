# Copyright 2017 Autodesk Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
import yaml
import re
import collections
from pathlib import Path
import textwrap


def yml_dump_color(d):
    s = yaml.dump(d, default_flow_style=False, allow_unicode=True)
    return re.sub(r'^([a-zA-Z0-9_]+?:)', _key_colorer, s, flags=re.MULTILINE)


def fail(err):
    print('\n'.join(textwrap.wrap(err, width=90, replace_whitespace=False)))
    sys.exit(1)


def _key_colorer(m):
    from termcolor import colored
    contents = m.group(1)
    assert contents[-1] == ':'
    return colored(contents, 'blue')


def pretty_path(p):
    p_with_home = None
    if "~" in str(p):
        p_with_home = p
        try:
            p = p.expanduser()
        except AttributeError:
            import os.path
            p = Path(os.path.expanduser( str(p) ))
    p = p.absolute()
    cwd = Path.cwd()
    if p == cwd:
        return 'Current directory'
    try:
        return './' + p.relative_to(cwd).as_posix()
    except ValueError:
        if p_with_home is not None:
            return p_with_home.as_posix()
        return p.as_posix()


def _set_yaml_prettyprint():
    # TODO: don't mess with yaml's global configuratino
    _mapping_tag = yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG

    def str_presenter(dumper, data):
        if len(data.splitlines()) > 1:  # check for multiline string
            return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
        return dumper.represent_scalar('tag:yaml.org,2002:str', data)

    yaml.add_representer(str, str_presenter)

    def dict_representer(dumper, data):
        return dumper.represent_dict(data.items())

    def dict_constructor(loader, node):
        return collections.OrderedDict(loader.construct_pairs(node))

    yaml.add_representer(collections.OrderedDict, dict_representer)
    yaml.add_constructor(_mapping_tag, dict_constructor)

    if sys.version_info.major == 2:
        yaml.add_representer(unicode,
                             lambda dumper, value:
                             dumper.represent_scalar(u'tag:yaml.org,2002:str', value))
        #yaml.add_representer(unicode, str_presenter)

_set_yaml_prettyprint()
