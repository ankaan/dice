from django import forms
from django.forms.formsets import formset_factory
from django.shortcuts import render

from nspdice_probability.die import Die

class BaseFormManager(object):
  """Manage multiple copies of the same form dynamically."""

  def _add_form(self,form_id):
    prefix = self._prefix+str(form_id)
    form = self.form(self._data,prefix=prefix)
    if form.keep():
      self._forms.append(form)

  def _add_form_extra(self,form_id):
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

    for i in form_ids:
      self._add_form(i)

    if len(form_ids) > 0:
      extra_offset = form_ids[-1]+1
    else:
      extra_offset = 0

    # Add extra forms.
    for i in range(self.extra):
      self._add_form_extra(i+extra_offset)

def manager_factory(form, manager=BaseFormManager, extra=1):
  """
  Return a manager for the given form.
  
  Arguments:
    form:     The form tho create a manager for.
    manager:  What form manager to create.
    extra:    Number of extra initial forms.
  """
  attrs = { 'form': form, 'extra': extra }
  return type(form.__name__+"Manager", (manager,), attrs)


class ModeForm(forms.Form):
  MODE_CHOICES = (
    ('target','Target'),
    ('vs','Versus'),
  )

  mode =  forms.ChoiceField(choices=MODE_CHOICES,required=False)

class ColumnForm(forms.Form):

  SKILL_CHOICES = (
    ('del','Delete'),
    ('pro','Property'),
    ('Skill', (
      ('1','LvL 1 (D6)'),
      ('2','LvL 2 (D8)'),
      ('3','LvL 3 (D10)'),
      ('4','LvL 4 (D12)'),
      ('5','LvL 5 (D20)'),
      ('6','LvL 6 (+6)'),
    )),
  )
  
  PRO_CHOICES = (
    ('1','1-8   (D6)'),
    ('2','9-14  (D8)'),
    ('3','15-17 (D10)'),
    ('4','18-9  (D12)'),
    ('5','20    (D20)'),
    ('6','21-24 (D16)'),
    ('7','25-29 (D24)'),
    ('8','30    (D30)'),
  )

  def _flatten(self,choices):
    flat = []
    for choice, value in choices:
      if isinstance(value, (list, tuple)):
        flat.extend(value)
      else:
        flat.append((choice,value))
    return flat

  def get_skill_display(self):
    value = self.cleaned_data['skill']
    return dict(self._flatten(self.SKILL_CHOICES)).get(value, value)

  def get_pro_display(self):
    value = self.cleaned_data['pro']
    return dict(self._flatten(self.PRO_CHOICES)).get(value, value)

  skill = forms.ChoiceField(choices=SKILL_CHOICES)
  pro =   forms.ChoiceField(choices=PRO_CHOICES)

  def keep(self):
    if not self.is_valid():
      return True
    else:
      return self.cleaned_data['skill'] != 'del'

def probability_reference(request):
  # Create factory...
  ColumnFormManager = manager_factory(ColumnForm)

  mode = 'target'
  if "mode" in request.GET:
    modeform = ModeForm(request.GET)
    if modeform.is_valid():
      mode = modeform.cleaned_data.get('mode','target')
  else:
    modeform = ModeForm()

  columnmanager = ColumnFormManager(request.GET)

  if mode == 'target':
    if columnmanager.is_valid():
      result = transpose([
        # Create the corresponding die for each form and compute probability.
        build_die(d['skill'],d['pro']).probability_reach()
        for d in columnmanager.cleaned_data()
      ])
    else:
      result = []

    return render(request, 'target.html', {
      'modeform': modeform,
      'columnmanager': columnmanager,
      'result': result,
    })
  else:
    return render(request, 'probability_reference.html', {
      'modeform': modeform,
      'columnmanager': columnmanager,
    })

SKILL_DIE = {}
SKILL_DIE['1'] = Die(4) + Die(6)
SKILL_DIE['2'] = SKILL_DIE['1'] + Die(8)
SKILL_DIE['3'] = SKILL_DIE['2'] + Die(10)
SKILL_DIE['4'] = SKILL_DIE['3'] + Die(12)
SKILL_DIE['5'] = SKILL_DIE['4'] + Die(20)
SKILL_DIE['6'] = SKILL_DIE['5'] + Die.const(6)

DB_DIE = {}
DB_DIE['1'] = Die(6)
DB_DIE['2'] = Die(8)
DB_DIE['3'] = Die(10)
DB_DIE['4'] = Die(12)
DB_DIE['5'] = Die(20)
DB_DIE['6'] = Die(16)
DB_DIE['7'] = Die(24)
DB_DIE['8'] = Die(30)

PRO_DIE = {}
PRO_DIE['1'] = Die(4) +       DB_DIE['1']
PRO_DIE['2'] = PRO_DIE['1'] + DB_DIE['2']
PRO_DIE['3'] = PRO_DIE['2'] + DB_DIE['3']
PRO_DIE['4'] = PRO_DIE['3'] + DB_DIE['4']
PRO_DIE['5'] = PRO_DIE['4'] + DB_DIE['5']
PRO_DIE['6'] = PRO_DIE['5'] + DB_DIE['6']
PRO_DIE['7'] = PRO_DIE['5'] + DB_DIE['7']
PRO_DIE['8'] = PRO_DIE['5'] + DB_DIE['8']

def build_die(skill,pro):
  if skill == 'pro':
    return PRO_DIE[pro]
  else:
    return SKILL_DIE[skill] + DB_DIE[pro]

def transpose(data):
  if len(data)==0:
    return []
  if len(data)==1:
    return map(lambda x: [x],*data)
  else:
    return map(None,*data)
