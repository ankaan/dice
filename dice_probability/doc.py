"""Decorators to handle python documentation."""

def docfrom(src):
  """Copy pydoc string from given source."""
  def decorator(dst):
    dst.__doc__ = src.__doc__
    return dst
  return decorator

def inheritdoc(src):
  """Copy pydoc string from component of the same name in the given class."""
  def decorator(dst):
    dst.__doc__ = src.__dict__[dst.__name__].__doc__
    return dst
  return decorator
