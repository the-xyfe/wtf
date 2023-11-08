## WTF?

You've imported a module, ran a function, it returned an object x, now what?

You could try and find documentation or read the source code to understand what x is, but you're not in reading mode. You're in hacker mode. So, your next steps are:

```python
print(x)
print(type(x))
print(dir(x))
help(x)
breakpoint()
```

wtf lets you skip a few steps. You can do roughly the same as the above code using only:
```python
import wtf
wtf(x)
```

### Get it

```sh
$ pip install git+https://github.com/the-xyfe/wtf
```

### Features

Just importing wtf is enough to drop into a helpful debug console when an exception is uncaught:

```python
>>> import wtf
>>> raise RuntimeError()
  File "<stdin>", line 1, in <module>
builtins.RuntimeError

inherits:  Exception() (and BaseException())
fields:    args
functions: add_note(), with_traceback()
        Unspecified run-time error.
> <stdin>(1)<module>()
(Pdb)
```

You can also catch `Exception`s and generate code to handle specific types of them:

```python
>>> print(wtf[caught_exception].code)
except json.decoder.JSONDecodeError as ex:
    # Expecting value: line 2 column 13 (char 20)
    print(f'{ex} while trying...')
```

Actually, you can generate code snippets to handle most objects:

```python
>>> def generate_items(n, endless=False):
...    yield from range(n)
...
>>> wtf(generate_items)
<generator function generate_items>
from:      <stdin>
generate_items(n, endless=False)
>>> print(wtf[generate_items].code)
for item in x(starting_list, endless=False):
    wtf(item)
```

Obviously, you can get simple info about simple objects:

```python
>>> wtf(ordered_dict)
collections.OrderedDict
{'a': 42, 'b': 'foo', 'c': 3}

```

When simple objects get too large, wtf summarizes them (or their contents):

```python
>>> wtf(large_dict)
a:      int(4199958)
c:      int(3)
b:      str()
sub:    {'cow': 'moo', 'far': 'zoo', 'l': 42}
```

Inspecting a list will give you code to loop over it, doing structural pattern matching on the items:

```python
>>> wtf[[1, {'k': 2}, {'k': 3}]]
for item in items:
    match item:
        case int(1):
            # Would match at least 1 items.

        case {'k': int(k)}:
            # Would match at least 2 items.
            print(f'{k=}') # int(3)
```

For other objects or types it shows:

- The file where the object is defined
- Inherited classes
- Fields, separated from functions
- Function or constructor signature
- The docstring

```python
>>> wtf(C)
<class 'mystery.C'>
from:      /usr/lib/python3.11/site-packages/mystery.py
inherits:  B(), A()
fields:    ok, title
functions: get_lock()
C()
```

Suppose you have a function and you want to know how it is used. Decorating it with `wtf.happens` will drop you into a debugger when the function is called and when it returns, giving you the parameter values that were given and the usual description of the funtion's return value:

```python
>>> @wtf.happens
... def black_box(a, b, x=42, y=-1):
...     return [{'a':42}, {'a':3}, {'b':'foo'}]
... 
>>> black_box(1, 2, 'g', y=None)
Press s+[enter] to step into black_box(a, b, x=42, y=-1) with:
        a = int(1)
        b = int(2)
        x = 'g'
        y = None
--Call--
> <stdin>(1)black_box()
(Pdb) c

Returns: for item in items:
    match item:
        case {'a': int(a)}:
            # Would match at least 2 items.
            print(f'{a=}') # int(3)
        case {'b': str(b)}:
            # Would match at least 1 items.
            print(f'{b=}') # 'foo'

[{'a': 42}, {'a': 3}, {'b': 'foo'}]
--Return--
> <stdin>(1)<module>()->None
(Pdb)
```

### Usage

To save you keystrokes, wtf does some magic, unpythonic things. You should probably only use it during development, and nowhere near production code. Be aware of the following:

- When you `import wtf`, a custom global exception handler is set that drops you into a debugger when any exception goes uncaught.
- `wtf(x)` gives you info and drops you into a debugger. `wtf[x]` only returns the info as a string.
- `wtf[x].short` gives the shortest summary about x, trying to keep it on one line.
- `wtf[x].code` tries to give you a useful code snippet.
- The output format of wtf is subject to change.

