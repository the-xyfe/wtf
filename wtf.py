#!/usr/bin/env python3

from collections import namedtuple, OrderedDict
from datetime import datetime, timedelta
from dataclasses import dataclass
import xml.etree.ElementTree
from pathlib import Path
import traceback
import logging
import inspect
import pprint
import json
import pdb
import sys
import re
import io


red = lambda s: f'\033[38;5;9m{s}\033[0m'


def _pythonise_var_name(heathenscript):
    underscore_separated = re.sub(r'([a-z])([A-Z])', r'\1_\2', heathenscript)
    only_word_chars = re.sub(r'[^a-zA-Z]+', '_', underscore_separated)
    return only_word_chars.lower().strip('_')


def _is_boring(x, attribute_name=None):
    boring_types = (float, int, bool, str, list, tuple, set, dict)
    if attribute_name:
        if attribute_name.startswith('_'):
            return True
        for boring_type in boring_types:
            if issubclass(type(x), boring_type) and hasattr(boring_type(), attribute_name):
                return True
    else:
        for boring_type in boring_types:
            if x == boring_type or type(x) == boring_type:
                return True
    return False


class UnIronic(str):
    def __repr__(self):
        return self


class WTF:
    '''WTF is this?

    wtf(x)             # Print info about x. Drop into the pdb debugger if we're not in interactive mode already.
    wtf(x, stop=False) # Return an object describing x and continue. Try print(wtf(wtf, stop=False).code).
    wtf[x]             # Return an object describing x and continue. Try print(wtf[wtf].short).
    42/0               # Drop into a debugger at every uncaught exception. Print info about the exception.

    @wtf.happens       # A decorator for a function that you want to study
    '''
    def __call__(self, x, stop=True):
        W = WTF()
        W.x = x
        W._name = W._source_var_name()
        if type(W.x) == type:
            W._type = W.x
        else:
            W._type = type(W.x)
        W._type_name = W._type.__name__
        W._human_readable_string_representation = W._remove_memory_address(W.x)
        W._machine_readable_string_representation = W._remove_memory_address(repr(W.x))
        
        if stop:
            print(W)
            if not hasattr(sys, 'ps1'):
                pdb.Pdb(skip=['wtf']).set_trace()
        return W
    def __getitem__(cls, x):
        return wtf(x, stop=False)


    @property
    def fields(self):
        return list(filter(lambda p: not _is_boring(self.x, p) and not callable(getattr(self.x, p)), dir(self.x)))


    @property
    def functions(self):
        return list(filter(lambda p: not _is_boring(self.x, p) and callable(getattr(self.x, p)), dir(self.x)))


    def __repr__(self):
        return str(self)


    @property
    def _fully_qualified_type_name(self):
        x_type = type(self.x)
        type_name = x_type.__name__
        if namespace := getattr(x_type, '__module__', ''):
            type_name = f'{namespace}.{type_name}'
        return type_name


    def __str__(self):
        type_name = self._type_name
        lines = list()

        match self.x:
            case float() | int():
                lines.append(f'{type_name}({self._machine_readable_string_representation})')
            case str() | bool():
                lines.append(self._machine_readable_string_representation)
            case list() | tuple() | set() | Object():
                lines.append(self.code)
            case OrderedDict():
                lines.append(self._fully_qualified_type_name)
                dictised = dict(self.x)
                # See if printing the whole thing would be too much clutter.
                pformatted = pprint.pformat(dictised)
                if len(pformatted) < 300:
                    lines.append(pformatted)
                else:
                    # Alternatively, only show keys and some analytics about each value.
                    for k, v in dictised.items():
                        lines.append(f'{k}:\t{wtf(v, stop=False).short}')
            case dict():
                # See if printing the whole thing would be too much clutter.
                pformatted = pprint.pformat(self.x)
                if len(pformatted) < 300:
                    lines.append(pformatted)
                else:
                    # Alternatively, only show keys and some analytics about each value.
                    for k, v in self.x.items():
                        lines.append(f'{k}:\t{wtf(v, stop=False).short}')
            case json.decoder.JSONDecodeError() if (match := re.search(r'char (\d+)', str(self.x))):
                lines.append(self._machine_readable_string_representation)
                char_number = min(int(match.group(1)), len(self.x.doc)-1)
                context_snippet_length = 80
                context_before = UnIronic(self.x.doc[char_number-((context_snippet_length//2)-2):char_number])
                bad = UnIronic(self.x.doc[char_number])
                context_after = UnIronic(self.x.doc[char_number:char_number+((context_snippet_length//2)-2)])
                lines.append(context_before + red(bad) + context_after)
                if 0 <= ord(self.x.doc[char_number]) <= 31:
                    lines.append(f'hint: json.loads(s, strict=False)')
            case _:
                if isinstance(self.x, Exception):
                    lines.append(self._fully_qualified_type_name)
                    lines.append(self._human_readable_string_representation)
                elif isinstance(self.x, xml.etree.ElementTree.Element):
                    pass
                elif inspect.isgeneratorfunction(self.x) and self._human_readable_string_representation.startswith('<function '):
                    lines.append(self._human_readable_string_representation.replace('<function ', '<generator function '))
                elif self._machine_readable_string_representation == self._human_readable_string_representation:
                    lines.append(self._machine_readable_string_representation)
                else:
                    lines.append(    f'str():     {self.x}')
                    lines.append(    f'repr():    {self.x!r}')
                if not (self._fully_qualified_type_name in self._machine_readable_string_representation or self._fully_qualified_type_name.startswith('builtins.')):
                    lines.append(    f'type:      {self._fully_qualified_type_name}')
                try:
                    source_file_path = inspect.getfile(self.x)
                    if source_file_path not in self._machine_readable_string_representation:
                        lines.append(f'from:      {source_file_path}')
                except TypeError:
                    pass
                inherits = ', '.join([wtf[o].short for o in self._type.__bases__ if o != object])
                grandparents = list(self._type.__mro__)
                for uninteresting in self._type.__bases__ + (self._type, object):
                    try:
                        grandparents.remove(uninteresting)
                    except ValueError:
                        pass
                if grandparents:
                    inherits += ' (and ' + ', '.join([wtf[o].short for o in grandparents]) + ')'
                if inherits:
                    lines.append(    'inherits:  ' + inherits)
                if self.fields:
                    lines.append('fields:    ' + ', '.join(self.fields))
                if self.functions:
                    lines.append('functions: ' + ', '.join([f'{p}()' for p in self.functions]))
                if callable(self.x):
                    # For callables, reconstruct the signature.
                    try:
                        lines.append(f'{self.x.__name__}{inspect.signature(self.x)}')
                    except:
                        pass
                elif (name := getattr(self.x, '__name__', None)) and name not in self._machine_readable_string_representation:
                    # Not a callable, but has a name.
                    lines.append(f'name:      {name}')
                if docstring := inspect.getdoc(self.x):
                    # If available, show the docstring.
                    for line in docstring.split('\n'):
                        lines.append(f'\t{line}')
                if isinstance(self.x, xml.etree.ElementTree.ElementTree):
                    reconstructed_xml = xml.etree.ElementTree.tostring(self.x.getroot(), encoding='unicode')
                    if len(reconstructed_xml) < 1000:
                        lines.append(reconstructed_xml)
                elif isinstance(self.x, xml.etree.ElementTree.Element):
                    reconstructed_xml = xml.etree.ElementTree.tostring(self.x, encoding='unicode')
                    if len(reconstructed_xml) < 1000:
                        lines.append(reconstructed_xml)
                    else:
                        lines.append(f'<{self.x.tag}>')
        return UnIronic('\n'.join(lines))


    @property
    def short(self):
        description = str(self)
        is_one_short_line = lambda d: d and len(d) <= 100 and '\n' not in d
        if not is_one_short_line(description):
            match self.x:
                case Exception():
                    description = f'{self._fully_qualified_type_name}()'
                case list() | tuple() | set():
                    try:
                        description = repr(self._type(list([wtf[o].short for o in self.x])))
                        if len(description) > 100:
                            description = self._machine_readable_string_representation
                            if len(description) > 100:
                                description = f'{len(self.x)} item {self._type_name}'
                    except:
                        # Tried to blindly instantiate something that might be inheriting from an iterable type. It didn't "just work".
                        description = self._machine_readable_string_representation
                        if len(description) > 100:
                            description = f'{len(self.x)} item {self._type_name}'
                case OrderedDict():
                    dictised = dict(self.x)
                    description = str({wtf[k].short: wtf[v].short for k, v in dictised.items()})
                    if len(description) > 100:
                        description = self._machine_readable_string_representation
                        if len(description) > 100:
                            description = f'{self._type_name} with keys: {", ".join(dictised.keys())}'
                            if len(description) > 100:
                                description = f'{len(dictised)} key {self._type_name}'
                case dict():
                    description = f'{self._type_name}(' + str({wtf[k].short: wtf[v].short for k, v in self.x.items()}) + ')'
                    if len(description) > 100:
                        description = self._machine_readable_string_representation
                        if len(description) > 100:
                            description = f'{self._type_name} with keys: {", ".join(self.x.keys())}'
                            if len(description) > 100:
                                description = f'{len(self.x)} key {self._type_name}'
                case _:
                    description = None
                    if callable(self.x):
                        # For callables, reconstruct the signature.
                        try:
                            description = f'{self.x.__name__}{inspect.signature(self.x)}'
                        except:
                            pass

        if not is_one_short_line(description):
            description = f'{self._type_name}()'
        return UnIronic(description)


    def _remove_memory_address(self, string):
        return re.sub(r'(\s*object)? at 0x[a-fA-F0-9]+', r'\1', str(string))


    def _source_line(self):
        stack = inspect.stack()
        try:
            this_frame = stack[0]
            this_package_file = Path(this_frame.filename)
            for frame in stack:
                code = None
                if Path(frame.filename) == this_package_file:
                    # Skip our own calls.
                    continue
                try:
                    code = ''.join(frame.code_context)
                except TypeError:
                    if frame.code_context:
                        code = str(frame.code_context)
                SourceLine = namedtuple('SourceLine', ['location', 'code', 'frame'])
                return SourceLine(f'{frame.filename} line {frame.lineno}', code, frame.frame)
        finally:
            del stack


    def _source_var_name(self):
        if (source_line := self._source_line()) and (code := source_line.code):
            if match := re.search(r'wtf\((\w+)\s*[,\)]', code):
                return match.group(1)


    @property
    def code(self, case_=''):
        source_var_name = self._name or 'x'
        scaffolding = ''
        if match := re.search(r'^(get|list)?_*(\w)s$', source_var_name):
            item_var_name = match.group(2)
        else:
            item_var_name = 'item'

        match self.x:
            case list() | tuple() | set():
                cases = dict()
                detail_code_lines_per_case = dict()
                def add_case(case_code, detail_code_lines=[]):
                    cases[case_code] = cases.get(case_code, 0) + 1
                    detail_code_lines_per_case[case_code] = detail_code_lines

                source_var_name = self._name or 'items'
                seen_all_items = False
                start = datetime.now()
                for item in self.x:
                    match item:
                        case dict():
                            case_code = ', '.join([f'{k!r}: {type(v).__name__}({_pythonise_var_name(k)})' for k, v in sorted(item.items())])
                            case_code = '{' + case_code + '}'
                            # TODO: Pass a dict(str(k): {wtf(v, stop=False).short})
                            #       so we can take the longest example value that we find.
                            add_case(case_code, detail_code_lines=[f"            print(f'{{{_pythonise_var_name(k)}=}}') # {wtf(v, stop=False).short}" for k, v in sorted(item.items())])
                            # TODO: list()
                        case _:
                            add_case(f'{type(item).__name__}({item})')
                    if datetime.now() - start > timedelta(seconds=2):
                        seen_all_items = False
                        break
                scaffolding = f'''for {item_var_name} in {source_var_name}:
    match {item_var_name}:
'''
                for case_code, num_matches in cases.items():
                    detail_code = '\n'.join(detail_code_lines_per_case[case_code])
                    scaffolding += f"""        case {case_code}:
            # Would match{seen_all_items and '' or ' at least'} {num_matches} {item_var_name}s.
{detail_code}
"""
                if case_ != '':
                    case_ = case_ or f'raise NotImplementedError({item_var_name})'
                    scaffolding += f"""        case _:
            {case_}
"""
            case Object():
                scaffolding = self.x.code(use_parent_name=True)
            case _ if callable(self.x):
                if inspect.isgeneratorfunction(self.x):
                    scaffolding = f'''for {item_var_name} in {source_var_name}{inspect.signature(self.x)}:
    wtf({item_var_name})'''
                else:
                    scaffolding = f'{source_var_name}{inspect.signature(self.x)}'
            case Exception():
                scaffolding = f'''except {self.short.strip("()")} as ex:
    # {self.x}
    print(f'{{ex}} while trying...')'''
            case _:
                scaffolding = f'# {self.short}'
        return UnIronic(scaffolding)


    @classmethod
    def happens(cls, function, *args, **kwargs):
        '''A decorator for a function that you want to study.

        @wtf.happens
        def f():
            yield from mysteries

        Tells you what arguments are used when calling it, and tells you what it returns'''

        def wrapper(*args, **kwargs):
            args_given_positionally = 0
            print(f'Press s+[enter] to step into {wtf(function, stop=False).short}{(args or kwargs) and " with:" or ""}')
            for param, arg in zip(inspect.signature(function).parameters.values(), args):
                print(f'\t{param.name} = {wtf(arg, stop=False).short}')
                args_given_positionally += 1
            for param in list(inspect.signature(function).parameters.values())[args_given_positionally:]:
                print(f'\t{param.name} = {wtf(kwargs[param.name], stop=False).short}')
            pdb.Pdb(skip=['wtf']).set_trace()
            returned = function(*args, **kwargs)
            print()
            print(f'Returns: {wtf(returned, stop=False)}')
            pdb.Pdb(skip=['wtf']).set_trace()
            return returned
        return wrapper


    def find(self, child_name):
        results = list(self._find(child_name))
        for result in results:
            wtf(result)
        else:
            print(f'{child_name} not found inside {self._name}')
        # TODO
        #if name in self.fields:
        #    return f'{self._name}.{name}'
        #if name in self.


    def _find(self, child_name, max_depth=42):
        if max_depth <= 0:
            return
        print(f'Looking in {self._name} ({self.short})')
        if child_name in self.fields:
            print(f'{child_name} is a field!')
            # Yield matching field.
            yield Field(self._name, child_name, value=getattr(self.x, child_name))

        match self.x:
            case dict():
                if child_name in self.x.keys():
                    print(f'{child_name} is a key!')
                    # Yield matching dict key.
                    yield Key(name=self._name, child_name=child_name, value=self.x[child_name])
                # Recurse into dict values.
                for k, v in self.x.items():
                    dict_value_wtf = wtf(v, stop=False)
                    for dict_value_result in dict_value_wtf._find(child_name, max_depth=max_depth-1):
                        yield Key(name=self._name, child_name=k, child=dict_value_result, value=v)
            case list():
                print(f'Looping over a {len(self.x)} item list...')
                # Loop over list, yield maching list (sub)items.
                for list_item in self.x:
                    list_item_wtf = wtf(list_item, stop=False)
                    for list_item_result in list_item_wtf._find(child_name, max_depth=max_depth-1):
                        yield ListItem(name=self._name, child=list_item_result, value=list_item)

        # Recurse into fields.
        for field_name in self.fields:
            if not _is_boring(self.x, field_name):
                print(f'Recursing into {self._name}.{field_name}')
                value = getattr(self.x, field_name)
                field_wtf = wtf(value, stop=False)
                field_wtf.name = field_name
                for field_result in field_wtf._find(child_name, max_depth=max_depth-1):
                    yield Field(self._name, child_name=field_name, child=field_result, value=value)


@dataclass
class Object:
    name: str
    child: None = None
    value: None = None

    def as_match(self):
        pass

    def as_oneliner(self):
        pass

    def code(self, use_parent_name=False):
        scaffolding, remaining = self.as_oneliner(use_parent_name)
        if remaining:
            remaining.name = _pythonise_var_name(scaffolding)
            scaffolding = f'{remaining.name} = {scaffolding}\n{remaining.code()}'
        return scaffolding


@dataclass
class Field(Object):
    child_name: str = None

    def as_oneliner(self, use_parent_name=False):
        s = f'{use_parent_name and self.name or ""}.{self.child_name}'
        if self.child == None:
            return (None, s, None)
        else:
            child_match, remaining = self.child.as_oneliner()
            return (f'{s}{child_match}', remaining)


@dataclass
class Key(Object):
    child_name: str = None

    def as_match(self):
        if self.child == None:
            return f"{{{self.child_name!r}: {type(self.value).__name__}({_pythonise_var_name(self.child_name)})}}"
        elif child_match := self.child.as_match():
            return f"{{{self.child_name!r}: {child_match}}}"

    def as_oneliner(self, use_parent_name=False):
        s = f'{use_parent_name and self.name or ""}.get({self.child_name!r})'
        if self.child == None:
            return (s, None)
        else:
            child_match, remaining = self.child.as_oneliner()
            return (f'{s}{child_match}', remaining)


@dataclass
class ListItem(Object):
    from_start: int = None
    from_end: int = None

    def as_oneliner(self, use_parent_name=False):
        return ('', self)

    def code(self, use_parent_name=False):
        self.child.name = 'item'
        return f'''for item in {self.name}:
    {self.child.code(use_parent_name=True)}'''


# Replace the module with a WTF instance to save typing.
wtf = WTF()
wtf.__spec__ = __spec__
sys.modules[__name__] = wtf

# Replace the default excepthook to drop into a debugger and get extra Exception info when an exception is not caught.
def wtf_excepthook(type, value, trace_back):
    traceback.print_tb(trace_back)
    print(wtf[value])
    p = pdb.Pdb(skip=['wtf'])
    p.reset()
    p.interaction(None, trace_back)
    p.set_trace()
sys.excepthook = wtf_excepthook

if not logging.getLogger().isEnabledFor(logging.DEBUG):
    # Reminder to remove this import if you've used it only for debugging.
    logging.info('wtf?')
