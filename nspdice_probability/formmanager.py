"""A basic manager for dynamically handling multiple copies of a form."""

class BaseFormManager(object):
  """Manage multiple copies of the same form dynamically."""

  def _allow_new_form(self):
    numforms = len(self._forms) + len(self._forms_extra)
    return self.max_forms == None or numforms<self.max_forms


  def _add_form(self,form_id):
    if self._allow_new_form():
      prefix = self._prefix+str(form_id)
      form = self.form(self._data,prefix=prefix)
      if form.keep():
        self._forms.append(form)
        return True
      else:
        return False

  def _add_form_extra(self,form_id):
    if self._allow_new_form():
      prefix = self._prefix+str(form_id)
      form = self.form(prefix=prefix)
      self._forms_extra.append(form)

  def forms(self):
    return self._forms + self._forms_extra

  def base_forms(self):
    return self._forms

  def extra_forms(self):
    return self._forms_extra

  def is_valid(self):
    return all([ f.is_valid() for f in self._forms ])

  def cleaned_data(self):
    return [ f.cleaned_data for f in self._forms ]

  def __init__(self,data=None,prefix=''):
    """
    Arguments:
      data:     The data GET/POST data that the forms should be bound to.
                Use None to make the forms unbound, which is the default.
      prefix:   Each form gets this prefix in addition to a generated one.
                By default empty.
    """
    self._prefix = prefix
    if len(self._prefix)>0:
      self._prefix += '-'

    self._forms = []
    self._forms_extra = []
    self._data = data

    form_ids = []
    if data:
      basenames = self.form().fields.keys()

      # Loop over all field names provided by the user, with prefix removed.
      for fn in [ fn[len(self._prefix):] for fn in data.keys() ]:
        # Make sure it can be split into a form name and base name.
        if fn.count('-')==1:
          [name,bn] = fn.split('-')
          # If the base name and form name is valid and not already known.
          if bn in basenames and name.isdigit() and int(name) not in form_ids:
            form_ids.append(int(name))

    form_ids = sorted(form_ids)

    extra_offset = 0
    for i in form_ids:
      if self._add_form(i):
        extra_offset = i+1

    # Add extra forms.
    for i in range(self.extra):
      self._add_form_extra(i+extra_offset)

def manager_factory(form, manager=BaseFormManager, extra=1, max_forms=None):
  """
  Return a manager for the given form.
  
  Arguments:
    form:       The form tho create a manager for.
    manager:    What form manager to create.
    extra:      Number of extra initial forms.
    max_forms:  Maximum number of forms allowed. None for infinite, the default.
  """
  attrs = { 'form': form, 'extra': extra, 'max_forms': max_forms }
  return type(form.__name__+"Manager", (manager,), attrs)
