"""Classic deprecation warning
===========================

Classic ``@deprecated`` decorator to deprecate old python classes, functions or methods.

.. _The Warnings Filter: https://docs.python.org/3/library/warnings.html#the-warnings-filter
"""

import inspect
import platform
import warnings
from typing import Any, Callable, Literal, Optional, Type, Union
import wrapt

_routine_stacklevel = 3
if platform.python_implementation() == "PyPy":
    _class_stacklevel = 2
else:
    _class_stacklevel = 3
string_types = (type(b""), type(""))


import re

class ClassicAdapter(wrapt.AdapterFactory):
    # ... [keep the existing code]

    def get_deprecated_msg(self, wrapped: Callable, instance: Any) -> str:
        """Get the deprecation warning message for the user.

        :param wrapped: Wrapped class or function.

        :param instance: The object to which the wrapped function was bound when it was called.

        :return: The warning message.
        """
        if instance is None:
            if inspect.isclass(wrapped):
                fmt = "Call to deprecated class {name}."
            else:
                fmt = "Call to deprecated function (or staticmethod) {name}."
        else:
            if inspect.isclass(instance):
                fmt = "Call to deprecated class method {name}."
            else:
                fmt = "Call to deprecated method {name}."
        if self.reason:
            fmt += " ({reason})"
        if self.version:
            fmt += " -- Deprecated since version {version}."
        
        # Remove Sphinx syntax from reason
        cleaned_reason = re.sub(r':([\w-]+):`([^`]+)`', r'`\2`', self.reason)
        
        return fmt.format(
            name=wrapped.__name__, reason=cleaned_reason, version=self.version
        )

    def __call__(self, wrapped: Callable) -> Callable:
        """Decorate your class or function.

        :param wrapped: Wrapped class or function.

        :return: the decorated class or function.

        .. versionchanged:: 1.2.4
           Don't pass arguments to :meth:`object.__new__` (other than *cls*).

        .. versionchanged:: 1.2.8
           The warning filter is not set if the *action* parameter is ``None`` or empty.
        """
        @wrapt.decorator
        def wrapper(wrapped, instance, args, kwargs):
            if inspect.isclass(wrapped):
                if not hasattr(wrapped, '_deprecated_warning_issued'):
                    msg = self.get_deprecated_msg(wrapped, instance)
                    if self.action:
                        with warnings.catch_warnings():
                            warnings.simplefilter(self.action, self.category)
                            warnings.warn(msg, category=self.category, stacklevel=2)
                    else:
                        warnings.warn(msg, category=self.category, stacklevel=2)
                    wrapped._deprecated_warning_issued = True
            else:
                msg = self.get_deprecated_msg(wrapped, instance)
                if self.action:
                    with warnings.catch_warnings():
                        warnings.simplefilter(self.action, self.category)
                        warnings.warn(msg, category=self.category, stacklevel=2)
                else:
                    warnings.warn(msg, category=self.category, stacklevel=2)
            return wrapped(*args, **kwargs)

        if inspect.isclass(wrapped):
            original_new = wrapped.__new__

            @classmethod
            def deprecated_new(cls, *args, **kwargs):
                if not hasattr(cls, '_deprecated_warning_issued'):
                    wrapper(cls, None, args, kwargs)
                if original_new is object.__new__:
                    return object.__new__(cls)
                return original_new(cls, *args, **kwargs)

            wrapped.__new__ = deprecated_new

        return wrapper(wrapped)


def deprecated(*args, **kwargs):
    """
    This is a decorator which can be used to mark functions
    as deprecated. It will result in a warning being emitted
    when the function is used.
    """
    if len(args) == 1 and callable(args[0]):
        return ClassicAdapter()(args[0])
    else:
        return ClassicAdapter(*args, **kwargs)
