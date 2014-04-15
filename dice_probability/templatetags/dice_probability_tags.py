from django import template

register = template.Library()

register.filter('zip',lambda x, y: zip(x,y))

@register.filter(name='format')
def format_filter(value,arg):
  try:
    return unicode(arg).format(value)
  except (ValueError, TypeError):
    return u""

@register.filter()
def fmul(value, arg):
  """Multiplies the float in arg with the value."""
  try:
    return float(value) * float(arg)
  except (ValueError, TypeError):
    return ''
