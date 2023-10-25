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

