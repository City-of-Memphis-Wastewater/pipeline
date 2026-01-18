```
>>> from pipeline_eds.philosophy import Philosophy
>>> p = Philosophy()
>>> str(p)
'Zen of Python: Beautiful is better than ugly.'

>>> repr(p)
'"__str__ is for users. __repr__ is for developers."'

>>> bool(p)
True

>>> p[1]
'Indexing into philosophy returns insight[1]'

>>> p("What is Pythonic?")
"You asked: 'What is Pythonic?'. Python answers with clarity."

>>> "python" in p
True

>>> with p as wisdom:
...     print(wisdom)
...
Entering a context of enlightenment.
Zen of Python: Beautiful is better than ugly.
Exiting the context. Wisdom retained.
```