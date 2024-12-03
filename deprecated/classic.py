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
    def __init__(
        self,
        reason: str = "",
        version: str = "",
        action: Optional[
            Literal["error", "ignore", "always", "default", "module", "once"]
        ] = None,
        category: Type[Warning] = DeprecationWarning,
        line_length: int = 70,
    ):
        self.reason = reason
        self.version = version
        self.action = action
        self.category = category
        self.line_length = line_length

    def get_deprecated_msg(self, wrapped: Callable, instance: Any) -> str:
        """Get the deprecation warning message for the user."""
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
        
        cleaned_reason = re.sub(r':([\w-]+):`([^`]+)`', r'`\2`', self.reason)
        
        return fmt.format(
            name=wrapped.__name__, reason=cleaned_reason, version=self.version
        )

    def __call__(self, wrapped: Callable) -> Callable:
        """Decorate your class or function."""
        if inspect.isclass(wrapped):
            return self._decorate_class(wrapped)
        else:
            return self._decorate_function(wrapped)

    def _decorate_class(self, wrapped: Type) -> Type:
        original_new = wrapped.__new__

        @classmethod
        def deprecated_new(cls, *args, **kwargs):
            if cls is wrapped:
                self._warn(self.get_deprecated_msg(wrapped, None))
            if original_new is object.__new__:
                return object.__new__(cls)
            return original_new(cls, *args, **kwargs)

        wrapped.__new__ = deprecated_new
        return wrapped

    def _decorate_function(self, wrapped: Callable) -> Callable:
        @wrapt.decorator
        def wrapper(wrapped, instance, args, kwargs):
            self._warn(self.get_deprecated_msg(wrapped, instance))
            return wrapped(*args, **kwargs)

        return wrapper(wrapped)

    def _warn(self, msg):
        if self.action:
            with warnings.catch_warnings():
                warnings.simplefilter(self.action, self.category)
                warnings.warn(msg, category=self.category, stacklevel=3)
        else:
            warnings.warn(msg, category=self.category, stacklevel=3)


def deprecated(
    reason: str = "",
    version: str = "",
    action: Optional[
        Literal["error", "ignore", "always", "default", "module", "once"]
    ] = None,
    category: Type[Warning] = DeprecationWarning,
    line_length: int = 70,
):
    """
    This is a decorator which can be used to mark functions
    as deprecated. It will result in a warning being emitted
    when the function is used.
    """
    if callable(reason):
        # Direct decoration
        return ClassicAdapter()(reason)
    else:
        # Parameterized decoration
        return ClassicAdapter(
            reason=reason,
            version=version,
            action=action,
            category=category,
            line_length=line_length
        )
