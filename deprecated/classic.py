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


class ClassicAdapter(wrapt.AdapterFactory):
    """Classic adapter -- *for advanced usage only*

    This adapter is used to get the deprecation message according to the wrapped object type:
    class, function, standard method, static method, or class method.

    This is the base class of the :class:`~deprecated.sphinx.SphinxAdapter` class
    which is used to update the wrapped object docstring.

    You can also inherit this class to change the deprecation message.

    In the following example, we change the message into "The ... is deprecated.":

    .. code-block:: python

       import inspect

       from deprecated.classic import ClassicAdapter
       from deprecated.classic import deprecated


       class MyClassicAdapter(ClassicAdapter):
           def get_deprecated_msg(self, wrapped, instance):
               if instance is None:
                   if inspect.isclass(wrapped):
                       fmt = "The class {name} is deprecated."
                   else:
                       fmt = "The function {name} is deprecated."
               else:
                   if inspect.isclass(instance):
                       fmt = "The class method {name} is deprecated."
                   else:
                       fmt = "The method {name} is deprecated."
               if self.reason:
                   fmt += " ({reason})"
               if self.version:
                   fmt += " -- Deprecated since version {version}."
               return fmt.format(name=wrapped.__name__,
                                 reason=self.reason or "",
                                 version=self.version or "")

    Then, you can use your ``MyClassicAdapter`` class like this in your source code:

    .. code-block:: python

       @deprecated(reason="use another function", adapter_cls=MyClassicAdapter)
       def some_old_function(x, y):
           return x + y
    """

    def __init__(
        self,
        reason: str = "",
        version: str = "",
        action: Optional[
            Literal["error", "ignore", "always", "default", "module", "once"]
        ] = None,
        category: Type[Warning] = DeprecationWarning,
    ):
        """Construct a wrapper adapter.

        :type  reason: str
        :param reason:
            Reason message which documents the deprecation in your library (can be omitted).

        :type  version: str
        :param version:
            Version of your project which deprecates this feature.
            If you follow the `Semantic Versioning <https://semver.org/>`_,
            the version number has the format "MAJOR.MINOR.PATCH".

        :type  action: str
        :param action:
            A warning filter used to activate or not the deprecation warning.
            Can be one of "error", "ignore", "always", "default", "module", or "once".
            If ``None`` or empty, the the global filtering mechanism is used.
            See: `The Warnings Filter`_ in the Python documentation.

        :type  category: type
        :param category:
            The warning category to use for the deprecation warning.
            By default, the category class is :class:`~DeprecationWarning`,
            you can inherit this class to define your own deprecation warning category.
        """
        self.reason = reason or ""
        self.version = version or ""
        self.action = action
        self.category = category
        super(ClassicAdapter, self).__init__()

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
        return fmt.format(
            name=wrapped.__name__, reason=self.reason, version=self.version
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
                wrapper(cls, None, args, kwargs)
                if original_new is object.__new__:
                    return object.__new__(cls)
                return original_new(*args, **kwargs)

            wrapped.__new__ = deprecated_new

        if inspect.isclass(wrapped):
            wrapped._deprecated_warning_issued = False
        
        @wrapt.decorator
        def wrapper(wrapped, instance, args, kwargs):
            if inspect.isclass(wrapped):
                if not wrapped._deprecated_warning_issued:
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
