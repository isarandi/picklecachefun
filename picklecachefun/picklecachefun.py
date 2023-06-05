import datetime
import functools
import hashlib
import inspect
import json
import os
import pickle

from loguru import logger

_default_cache_root = os.environ.get('CACHE_DIR')


def cache(path, cache_root=None, forced=False, min_time=None):
    """Caches and restores the results of a function call on disk.
    Specifically, it returns a function decorator that makes a function cache its result in a file.
    It only evaluates the function once, to generate the cached file. The decorator also adds a
    new keyword argument to the function, called 'forced_cache_update' that can explicitly force
    regeneration of the cached file.

    It has rudimentary handling of arguments by hashing their json representation and appending it
    the hash to the cache filename. This somewhat limited, but is enough for the current uses.

    Set `min_time` to the last significant change to the code within the function.
    If the cached file is older than this `min_time`, the file is regenerated.

    Usage:
        @picklecachefun.cache('/some/path/to/a/file', min_time='2025-12-27T10:12:32')
        def some_function(some_arg):
            ....
            return stuff

    Args:
        path: The path where the function's result is stored.
        forced: do not load from disk, always recreate the cached version
        min_time: recreate cached file if its modification timestamp (mtime) is older than this
           param. The format is like 2025-12-27T10:12:32 (%Y-%m-%dT%H:%M:%S)

    Returns:
        The decorator.
    """

    def decorator(f):
        @functools.wraps(f)
        def wrapped(*args, **kwargs):
            inner_forced = forced or kwargs.pop('forced_cache_update', False)
            inner_cache_root = cache_root if cache_root is not None else _default_cache_root
            if inner_cache_root is not None and not os.path.isabs(path):
                inner_path = os.path.join(inner_cache_root, path)
            else:
                inner_path = path

            bound_args = inspect.signature(f).bind(*args, **kwargs)
            args_json = json.dumps((bound_args.args, bound_args.kwargs), sort_keys=True)
            hash_string = hashlib.sha1(str(args_json).encode('utf-8')).hexdigest()[:12]

            if args or kwargs:
                noext, ext = os.path.splitext(inner_path)
                suffixed_path = f'{noext}_{hash_string}{ext}'
            else:
                suffixed_path = inner_path

            if not inner_forced and is_file_newer(suffixed_path, min_time):
                logger.info(f'Loading cached data from {suffixed_path}')
                try:
                    return load_pickle(suffixed_path)
                except Exception as e:
                    error_message = str(e)
                    logger.warning(f'Could not load from {suffixed_path}, due to: {error_message}')

            if os.path.exists(suffixed_path):
                logger.info(f'Recomputing data for {suffixed_path}')
            else:
                logger.info(f'Computing data for {suffixed_path}')

            result = f(*args, **kwargs)
            dump_pickle(result, suffixed_path, protocol=pickle.HIGHEST_PROTOCOL)

            if args or kwargs:
                hash_parent = (
                    inner_cache_root if inner_cache_root is not None
                    else os.path.dirname(suffixed_path))
                hash_path = os.path.join(hash_parent, 'hashes', hash_string)
                write_file(args_json, hash_path)

            return result

        return wrapped

    return decorator


def set_default_cache_root(cache_root):
    global _default_cache_root
    _default_cache_root = cache_root

def is_file_newer(path, min_time=None):
    if min_time is None:
        return os.path.exists(path)
    min_time = datetime.datetime.strptime(min_time, '%Y-%m-%dT%H:%M:%S').timestamp()
    return os.path.exists(path) and os.path.getmtime(path) >= min_time


def load_pickle(file_path):
    with open(file_path, 'rb') as f:
        return pickle.load(f)


def dump_pickle(data, file_path, protocol=pickle.DEFAULT_PROTOCOL):
    ensure_path_exists(file_path)
    with open(file_path, 'wb') as f:
        pickle.dump(data, f, protocol)


def write_file(content, path):
    ensure_path_exists(path)
    with open(path, 'w') as f:
        f.write(content)


def ensure_path_exists(filepath):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
