# picklecachefun
Cache the results of function calls to disk, using pickle, similarly to `functools.cache` in the standard library.

## Example usage

Basic use:

```python
import picklecachefun

@picklecachefun.cache('/path/to/filename.pkl')
def some_function(some_arg):
    ....
    return stuff
```

A default cache root can be set too:

```python
picklecachefun.set_cache_root('/path/to/cache')

@picklecachefun.cache('filename.pkl')
...

```

The cache can be invalidated through setting a `min_time`.
In short, set the `min_time` to the timestamp of 
when you most recently changed the function definition and need
to invalidate the cache.

```python
@picklecachefun.cache('filename.pkl', min_time="2023-12-04T20:56:48")
...
```
