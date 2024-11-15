"""Sphinx directive integration
============================

We usually need to document the life-cycle of functions and classes:
when they are created, modified or deprecated.

To do that, `Sphinx <http://www.sphinx-doc.org>`_ has a set
of `Paragraph-level markups <http://www.sphinx-doc.org/en/stable/markup/para.html>`_:

- ``versionadded``: to document the version of the project which added the described feature to the library,
- ``versionchanged``: to document changes of a feature,
- ``deprecated``: to document a deprecated feature.

The purpose of this module is to defined decorators which adds this Sphinx directives
to the docstring of your function and classes.

Of course, the ``@deprecated`` decorator will emit a deprecation warning
when the function/method is called or the class is constructed.
"""

import re
import textwrap
from deprecated.classic import ClassicAdapter


from typing import Any, Callable, Literal, Optional, Type


class SphinxAdapter(ClassicAdapter):
    """Sphinx adapter -- *for advanced usage only*

    Adapter that overrides the :class:`~deprecated.classic.ClassicAdapter`
    to add Sphinx directives to the end of the function/class docstring.
    Such a directive is a `Paragraph-level markup <http://www.sphinx-doc.org/en/stable/markup/para.html>`_

    - The directive can be one of "versionadded", "versionchanged" or "deprecated".
    - The version number is added if provided.
    - The reason message is added in the directive block if not empty.
    """

    def __init__(
        self,
        directive: str,
        reason: str = "",
        version: str = "",
        action: Optional[
            Literal["error", "ignore", "always", "default", "module", "once"]
        ] = None,
        category: Type[Warning] = DeprecationWarning,
        line_length: int = 70,
    ):
        """Construct a wrapper adapter.

        Args:
        ----
            directive: Sphinx directive: can be one of "versionadded", "versionchanged" or "deprecated".
            reason: Reason message which documents the deprecation in your library (can be omitted).
            version: Version of your project which deprecates this feature.
                If you follow the `Semantic Versioning <https://semver.org/>`_,
                the version number has the format "MAJOR.MINOR.PATCH".
            action: A warning filter used to activate or not the deprecation warning.
                Can be one of "error", "ignore", "always", "default", "module", or "once".
                If ``None`` or empty, the global filtering mechanism is used.
                See: `The Warnings Filter`_ in the Python documentation.
            category: The warning category to use for the deprecation warning.
                By default, the category class is :class:`~DeprecationWarning`,
                you can inherit this class to define your own deprecation warning category.
            line_length: Max line length of the directive text. If non-zero, a long text is wrapped in several lines.

        """
        if not version:
            raise ValueError("'version' argument is required in Sphinx directives")
        self.directive = directive
        self.line_length = line_length
        super(SphinxAdapter, self).__init__(
            reason=reason, version=version, action=action, category=category
        )

    def __call__(self, wrapped: Callable) -> Callable:
        """Add the Sphinx directive to the class or function.

        Args:
        ----
            wrapped: Wrapped class or function.

        Returns:
        -------
            The decorated class or function.

        """
        fmt = ".. {directive}:: {version}" if self.version else ".. {directive}::"
        div_lines = [fmt.format(directive=self.directive, version=self.version)]
        width = self.line_length - 3 if self.line_length > 3 else 2**16
        reason = textwrap.dedent(self.reason).strip()
        for paragraph in reason.splitlines():
            if paragraph:
                div_lines.extend(
                    textwrap.fill(
                        paragraph,
                        width=width,
                        initial_indent="   ",
                        subsequent_indent="   ",
                    ).splitlines()
                )
            else:
                div_lines.append("")
        docstring = wrapped.__doc__ or ""
        lines = docstring.splitlines(keepends=True) or [""]
        docstring = textwrap.dedent("".join(lines[1:])) if len(lines) > 1 else ""
        docstring = lines[0] + docstring
        if docstring:
            docstring = re.sub("\\n+$", "", docstring, flags=re.DOTALL) + "\n\n"
        else:
            docstring = "\n"
        docstring += "".join(("{}\n".format(line) for line in div_lines))
        wrapped.__doc__ = docstring
        if self.directive in {"versionadded", "versionchanged"}:
            return wrapped
        return super(SphinxAdapter, self).__call__(wrapped)

    def get_deprecated_msg(self, wrapped: Callable, instance: Any) -> str:
        """Get the deprecation warning message (without Sphinx cross-referencing syntax) for the user.

        Args:
        ----
            wrapped: Wrapped class or function.
            instance: The object to which the wrapped function was bound when it was called.

        Returns:
        -------
            The warning message.

        .. versionadded:: 1.2.12
           Strip Sphinx cross-referencing syntax from warning message.

        """
        message = super(SphinxAdapter, self).get_deprecated_msg(wrapped, instance)
        return re.sub(
            r":(?:class|func|meth|mod|attr|exc|const|data):`[^`]+`",
            lambda m: m.group(0)[1:-1].split("`")[1],
            message,
        )


def versionadded(
    reason: str = "", version: str = "", line_length: int = 70
) -> Callable:
    """Insert a "versionadded" directive in the function/class docstring.

    Documents the version of the project which adds this new functionality to your library.

    Args:
    ----
        reason: Reason message which documents the addition in your library (can be omitted).
        version: Version of your project which adds this feature.
            If you follow the `Semantic Versioning <https://semver.org/>`_,
            the version number has the format "MAJOR.MINOR.PATCH", and,
            in the case of a new functionality, the "PATCH" component should be "0".
        line_length: Max line length of the directive text. If non-zero, a long text is wrapped in several lines.

    Returns:
    -------
        The decorated function.

    """
    return SphinxAdapter(
        "versionadded", reason=reason, version=version, line_length=line_length
    )


def versionchanged(
    reason: str = "", version: str = "", line_length: int = 70
) -> Callable:
    """Insert a "versionchanged" directive in the function/class docstring.

    Documents the version of the project which modifies this functionality in your library.

    Args:
    ----
        reason: Reason message which documents the modification in your library (can be omitted).
        version: Version of your project which modifies this feature.
            If you follow the `Semantic Versioning <https://semver.org/>`_,
            the version number has the format "MAJOR.MINOR.PATCH".
        line_length: Max line length of the directive text. If non-zero, a long text is wrapped in several lines.

    Returns:
    -------
        The decorated function.

    """
    return SphinxAdapter(
        "versionchanged", reason=reason, version=version, line_length=line_length
    )


def deprecated(
    reason: str = "", version: str = "", line_length: int = 70, **kwargs: Any
) -> Callable:
    """Insert a "deprecated" directive in the function/class docstring.

    Documents the version of the project which deprecates this functionality in your library.

    Args:
    ----
        reason: Reason message which documents the deprecation in your library (can be omitted).
        version: Version of your project which deprecates this feature.
            If you follow the `Semantic Versioning <https://semver.org/>`_,
            the version number has the format "MAJOR.MINOR.PATCH".
        line_length: Max line length of the directive text. If non-zero, a long text is wrapped in several lines.
        **kwargs: Additional keyword arguments.

    Keyword Arguments:
    -----------------
        action: A warning filter used to activate or not the deprecation warning.
            Can be one of "error", "ignore", "always", "default", "module", or "once".
            If ``None``, empty or missing, the global filtering mechanism is used.
        category: The warning category to use for the deprecation warning.
            By default, the category class is :class:`~DeprecationWarning`,
            you can inherit this class to define your own deprecation warning category.

    Returns:
    -------
        A decorator used to deprecate a function.

    .. versionchanged:: 1.2.13
       Change the signature of the decorator to reflect the valid use cases.

    """
    return SphinxAdapter(
        "deprecated", reason=reason, version=version, line_length=line_length, **kwargs
    )
