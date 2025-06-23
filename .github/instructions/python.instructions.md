---
applyTo: '*.py, pyproject.toml'
---

# Python Coding Guidelines

These are rules for a modern Python project using uv.

## Python Version

Write for Python 3.11-3.13. Do NOT write code to support earlier versions of Python.
Always use modern Python practices appropriate for Python 3.11-3.13.

Always use full type annotations, generics, and other modern practices.

## Project Setup and Developer Workflows

- This project has a modern pyproject.toml file and a Makefile.
  Be sure you read and understand both.

- Use uv for running all code and managing dependencies.
  Never use direct `pip` or `python` commands.

- Use modern uv commands: `uv sync`, `uv run ...`, etc.
  Prefer `uv add` over `uv pip install`.

- You may use the following shortcuts
  ```shell

  # Install all dependencies:
  make install

  # Run linting (with ruff) and type checking (with basedpyright).
  # Note when you run this, ruff will auto-format and sort imports, resolving any
  # linter warnings about import ordering:
  make lint

  # Run tests:
  make test

  # Run uv sync, lint, and test in one command:
  make
  ```

- The usual `make test` like standard pytest does not show test output.
  Run individual tests and see output with `uv run pytest -s some/file.py`.

- Always run `make lint` and `make test` to check your code after changes.

- You must verify there are zero linter warnings/errors or test failures before
  considering any task complete.

## General Development Practices

- Be sure to resolve the pyright (basedpyright) linter errors as you develop and make
  changes.

- If type checker errors are hard to resolve, check pyproject.toml to see if they are an
  excessively pedantic error.
  In special cases you may consider disabling it globally it in pyproject.toml but you
  *must ask for confirmation* from the user before doing this.

- Never change an existing comment, pydoc, or a log statement, unless it is directly
  fixing the issue you are changing, or the user has asked you to clean up the code.
  Do not drop existing comments when editing code!
  And do not delete or change logging statements.

## Coding Conventions and Imports

- Always use full, absolute imports for paths.
  do NOT use `from .module1.module2 import ...`. Such relative paths make it hard to
  refactor. Use `from toplevel_pkg.module1.modlule2 import ...` instead.

- Be sure to import things like `Callable` and other types from the right modules,
  remembering that many are now in `collections.abc` or `typing_extensions`. For
  example: `from collections.abc import Callable, Coroutine`

- Use `typing_extensions` for things like `@override` (you need to use this, and not
  `typing` since we want to support Python 3.11).

- Add `from __future__ import annotations` on files with types whenever applicable.

- Use pathlib `Path` instead of strings.
  Use `Path(filename).read_text()` instead of two-line `with open(...)` blocks.

- Use strif's `atomic_output_file` context manager when writing files to ensure output
  files are written atomically.

- Use `uv add` and `uv sync` as needed to add dependencies.

## Testing

- Don't write one-off test code in extra files or within `if __name__ == "__main__":`
  blocks. Instead, for simple tests, create simple test functions in the original file
  below a `## Tests` comment.
  This keeps the tests clear and close to the code.

- For longer tests `test_somename.py` in the `tests/` directory.

- Then you can run such tests with `uv run python -s src/.../path/to/test`

- Don't add docs to assertions unless it's not obvious what they're checking - the
  assertion appears in the stack trace.
  Do NOT write `assert x == 5, "x should be 5"`. Do NOT write `assert x == 5 # Check if
  x is 5`. That is redundant.
  Just write `assert x == 5`.

- Don't use pytest fixtures like parameterized tests or expected exception decorators
  unless absolutely necessary in more complex tests.
  It is often far simpler to use simple assertions and put the checks inside the test.
  This is preferable because then we want simple tests in original source files but
  don't want pytest dependencies at runtime.

## Types and Type Annotations

- Use modern union syntax: `str | None` instead of `Optional[str]`, `dict[str]` instead
  of `Dict[str]`, `list[str]` instead of `List[str]`, etc.

- Never use/import `Optional` for new code.

- Use modern enums like `StrEnum` if appropriate.

- One exception to common practice on enums: If an enum has many values that are
  strings, and they have a literal value as a string (like in a JSON protocol), it's
  fine to use lower_snake_case for enum values to match the actual value.
  This is more readable than LONG_ALL_CAPS_VALUES, and you can simply set the value to
  be the same as the name for each.
  For example:
  ```python
  class MediaType(Enum):
    """
    Media types. For broad categories only, to determine what processing
    is possible.
    """

    text = "text"
    image = "image"
    audio = "audio"
    video = "video"
    webpage = "webpage"
    binary = "binary"
  ```

## Guidelines for Docstrings

- Here is an example of the correct style for docstrings:
  ```python
  def check_if_url(
      text: UnresolvedLocator, only_schemes: list[str] | None = None
  ) -> ParseResult | None:
      """
      Convenience function to check if a string or Path is a URL and if so return
      the `urlparse.ParseResult`.

      Also returns false for Paths, so that it's easy to use local paths and URLs
      (`Locator`s) interchangeably. Can provide `HTTP_ONLY` or `HTTP_OR_FILE` to
      restrict to only certain schemes.
      """
      # Function body

  def is_url(text: UnresolvedLocator, only_schemes: list[str] | None = None) -> bool:
      """
      Check if a string is a URL. For convenience, also returns false for
      Paths, so that it's easy to use local paths and URLs interchangeably.
      """
      return check_if_url(text, only_schemes) is not None
  ```

- Use concise pydoc strings with triple quotes on their own lines.

- Use `backticks` around variable names and inline code excerpts.

- Use plain fences (```) around code blocks inside of pydocs.

- For classes with many methods, use a concise docstring on the class that explains all
  the common information, and avoid repeating the same information on every method.

- Docstrings should provide context or as concisely as possible explain "why", not
  obvious details evident from the class names, function names, parameter names, and
  type annotations.

- Docstrings *should* mention any key rationale or pitfalls when using the class or
  function.

- Don't add pydocs that just repeat information obvious from the function, variable
  names, or concise description.
  That is silly and obvious and makes the code longer for no reason.

- Do NOT list args and return values if they're obvious.
  In the above examples, you do not need and `Arguments:` or `Returns:` section, since
  their meaning as obvious from context.
  do list these if there are many arguments and their meaning isn't clear.
  If it returns a less obvious type like a tuple, do explain in the pydoc.

- Exported/public variables, functions, or methods SHOULD have concise docstrings.
  Internal/local variables, functions, and methods DO NOT need docstrings unless their
  purpose is not obvious.
