#!/usr/bin/env python3

from collections import OrderedDict
from pathlib import Path
import importlib
import logging
import json

logging.getLogger().setLevel(logging.DEBUG)
print('Importing with debug logging enabled. This should print nothing.')
import wtf
logging.getLogger().setLevel(logging.INFO)
print('Re-importing with debug logging disabled. This should print WTF.')
importlib.reload(wtf)


class A:
    pass

class B:
    pass

class C(B, A):
    attribute_1 = 1
    def __init__(self):
        self.attribute_2 = 2
    def get_attribute(self, i, default=None):
        pass
    @property
    def attribute_property(self):
        pass


def show(string_of_x):
    print('-' * 100)
    print(f'>>> wtf({string_of_x})')
    print(wtf[eval(string_of_x)])
    print()

show("0.1")
show("0")
show("False")
show("'foo'")
show("object()")
show("Exception")
string_of_x = "RuntimeError('boo')"
show(string_of_x)

print('-' * 100)
print(f'>>> wtf[{string_of_x}].short')
enlightenment = wtf[eval(string_of_x)]
print(enlightenment.short)
print()

print('-' * 100)
print(f'>>> wtf(object(), stop=True)')
wtf(object())

show("C")
show("C()")
show("Path")

frobbles = [{'a':42}, {'a':3}, {'b':'foo'}]
print('-' * 100)
print('>>> x = wtf(frobbles)')
x = wtf[frobbles]
print('>>> print(x)')
print(x)
print()

small_dict = {'a':42, 'c':3, 'b':'foo'}
show("small_dict")
ordered_dict = OrderedDict(small_dict)
show("ordered_dict")
large_dict = {'a':42*99999, 'c':3, 'b':'foo'*100, 'sub': {'l': 42, 'far': 'zoo', 'cow': 'moo'}}
show("large_dict")

show("wtf[42]")

def normal_function(starting_list):
    '''return the starting list or an example list'''
    return starting_list or (1, 2, 3)
def generator_example(starting_list, endless=False):
    yield from normal_function()

show("normal_function")
show("generator_example")

@wtf.happens
def black_box(a, b, x=42, y=-1):
    return frobbles

print('-' * 100)
print('''>>> @wtf.happens
... def black_box(a, b, x=42, y=-1):
...     return frobbles
>>> black_box(1, 2, 'g', y=None)''')
black_box(1, 2, 'g', y=None)
print()


def show_code(string_of_x):
    print('-' * 100)
    print(f'>>> print(wtf[{string_of_x}].code)')
    w = wtf[eval(string_of_x)]
    print(w.code)
    print()

show_code("ValueError('value problem')")
show_code("[1, 2, 3]")
show_code("normal_function")
show_code("generator_example")

with open('.test.json', 'r') as f:
    j = json.load(f, strict=False)
huge_nested_object = C()
huge_nested_object.attribute_1 = j
print('-' * 100)
print(""">>> wtf.find(huge_nested_object, 'descriptionTxt')""")
wtf(huge_nested_object).find('descriptionTxt')
print()

try:
    j = json.loads('''{"foo":
            42}''')
except Exception as json_decode_error:
    show_code("json_decode_error")

print('-' * 100)
print(""">>> raise ValueError('Uncaught exception!')""")
raise ValueError('Uncaught exception!')

