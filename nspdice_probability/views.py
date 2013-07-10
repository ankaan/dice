from django import forms
from django.http import HttpResponse
from django.shortcuts import render

from nspdice_probability.die import LazyDie as Die
from nspdice_probability.die import DieParseException, from_string
from nspdice_probability.formmanager import manager_factory

import string
import urllib

from matplotlib import use as matplot_use
matplot_use('cairo')

from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.pyplot import Axes

MAX_DICE = 10
MAX_SIDES = 30

SKILL_DIE = {}
SKILL_DIE['del'] = Die.const(0)
SKILL_DIE['basic'] = Die(4)

SKILL_DIE['seq1'] = Die(4) + Die(6)
SKILL_DIE['seq2'] = SKILL_DIE['seq1'] + Die(8)
SKILL_DIE['seq3'] = SKILL_DIE['seq2'] + Die(10)
SKILL_DIE['seq4'] = SKILL_DIE['seq3'] + Die(12)
SKILL_DIE['seq5'] = SKILL_DIE['seq4'] + Die(20)
SKILL_DIE['seq6'] = SKILL_DIE['seq5'] + Die.const(6)

SKILL_DIE['1'] = Die(6)
SKILL_DIE['2'] = Die(8)
SKILL_DIE['3'] = Die(10)
SKILL_DIE['4'] = Die(12)
SKILL_DIE['5'] = Die(20)
SKILL_DIE['6'] = Die(20) + Die.const(6)

PRO_DIE = {}
PRO_DIE['del'] = Die.const(0)
PRO_DIE['basic'] = Die(4)

PRO_DIE['seq1'] = Die(4) + Die.const(1)
PRO_DIE['seq2'] = Die(4) + Die(6)
PRO_DIE['seq3'] = PRO_DIE['seq2'] + Die(8)
PRO_DIE['seq4'] = PRO_DIE['seq3'] + Die(10)
PRO_DIE['seq5'] = PRO_DIE['seq4'] + Die(12)
PRO_DIE['seq6'] = PRO_DIE['seq5'] + Die(20)
PRO_DIE['seq7'] = PRO_DIE['seq6'] + Die.const(6)

PRO_DIE['1'] = Die.const(1)
PRO_DIE['2'] = Die(6)
PRO_DIE['3'] = Die(8)
PRO_DIE['4'] = Die(10)
PRO_DIE['5'] = Die(12)
PRO_DIE['6'] = Die(20)
PRO_DIE['7'] = Die(20) + Die.const(6)

class ModeForm(forms.Form):
  MODE_CHOICES = (
    ('target','Target'),
    ('vs','Versus'),
    ('plot_target','Target Plot'),
    ('plot_prob','Probability Plot'),
  )

  mode =  forms.ChoiceField(choices=MODE_CHOICES,required=False)

class ColumnForm(forms.Form):

  SKILL_CHOICES = (
    ('del',''),
    ('Die Sequence', (
      ('seq1','LvL 1 (D4-D6)'),
      ('seq2','LvL 2 (D4-D8)'),
      ('seq3','LvL 3 (D4-D10)'),
      ('seq4','LvL 4 (D4-D12)'),
      ('seq5','LvL 5 (D4-D20)'),
      ('seq6','LvL 6 (D4-D20+6)'),
      )),
    ('Single Die', (
      ('basic','Basic (D4)'),
      ('1','LvL 1 (D6)'),
      ('2','LvL 2 (D8)'),
      ('3','LvL 3 (D10)'),
      ('4','LvL 4 (D12)'),
      ('5','LvL 5 (D20)'),
      ('6','LvL 6 (D20+6)'),
    )),
  )

  PRO_CHOICES = (
    ('del',''),
    ('Die Sequence', (
      ('seq1','1-5 (D4+1)'),
      ('seq2','6-10 (D4-D6)'),
      ('seq3','11-15 (D4-D8)'),
      ('seq4','16-20 (D4-D10)'),
      ('seq5','21-25 (D4-D12)'),
      ('seq6','26-29 (D4-D20)'),
      ('seq7','30 (D4-D20+6)'),
      )),
    ('Single Die', (
      ('basic','Basic (D4)'),
      ('1','1-5 (D4+1)'),
      ('2','6-10 (D6)'),
      ('3','11-15 (D8)'),
      ('4','16-20 (D10)'),
      ('5','21-25 (D12)'),
      ('6','26-29 (D20)'),
      ('7','30 (D20+6)'),
    )),
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

  def get_attribute_display(self):
    value = self.cleaned_data['attribute']
    return dict(self._flatten(self.PRO_CHOICES)).get(value, value)

  skill =     forms.ChoiceField(choices=SKILL_CHOICES)
  attribute = forms.ChoiceField(choices=PRO_CHOICES)

  def keep(self):
    return any([not self.is_valid(),
                self.cleaned_data['skill'] != 'del',
                self.cleaned_data['attribute'] != 'del'])

  def details(self):
    return "%s\n%s"%(self.get_skill_display(),self.get_attribute_display())

class CustomDieForm(forms.Form):
  die = forms.CharField(required=False)

  def __init__(self,*args,**kwargs):
    super(CustomDieForm, self).__init__(*args,**kwargs)

    self.num = None

  def get_skill_display(self):
    return "Custom %d" % self.num

  def get_attribute_display(self):
    return ""

  def clean_die(self):
    raw = self.cleaned_data['die']
    self.rawdice = raw.split()

    try:
      return from_string(Die, raw, max_sides=30, max_dice=15)
    except DieParseException as e:
      raise forms.ValidationError(*e.args)

  def keep(self):
    if not self.is_valid():
      return True
    else:
      return self.cleaned_data['die'] != None

  def details(self):
    return "Custom %d:\n%s"%(self.num,string.join(self.rawdice))

def probability_reference(request):
  return _probability_reference(request, stage='html')

def probability_reference_plot(request):
  return _probability_reference(request, stage='plot')

ColumnFormManager = manager_factory(ColumnForm,max_forms=60)
CustomDieFormManager = manager_factory(CustomDieForm,max_forms=10)

def _probability_reference(request, stage):
  mode = 'target'
  if "mode" in request.GET:
    modeform = ModeForm(request.GET)
    if modeform.is_valid():
      mode = modeform.cleaned_data.get('mode','target')
  else:
    modeform = ModeForm()

  columnmanager = ColumnFormManager(request.GET)
  customdiemanager = CustomDieFormManager(request.GET)

  for i, f in enumerate(customdiemanager.base_forms(),1):
    f.num = i

  if mode == 'target':
    dice = build_dice(columnmanager,customdiemanager)
    # Compute probability for each die.
    result = transpose([ d.probability_reach() for d in dice ])

    return render(request, 'target.html', {
      'modeform': modeform,
      'columnmanager': columnmanager,
      'customdiemanager': customdiemanager,
      'result': result,
    })

  elif mode == 'vs':
    dice = build_dice(columnmanager,customdiemanager)
    result = [ [ a.probability_vs(b) for a in dice ] for b in dice ]

    return render(request, 'versus.html', {
      'modeform': modeform,
      'columnmanager': columnmanager,
      'customdiemanager': customdiemanager,
      'result': result,
    })
  elif mode == 'plot_target':
    if stage=='plot':
      dice = build_dice(columnmanager,customdiemanager)
      return prob_plot(request,dice,columnmanager,customdiemanager,target=True)
    else:
      getvars = urllib.urlencode(request.GET)

      return render(request, 'plot_target.html', {
        'modeform': modeform,
        'columnmanager': columnmanager,
        'customdiemanager': customdiemanager,
        'getvars': getvars,
      })
  elif mode == 'plot_prob':
    if stage=='plot':
      dice = build_dice(columnmanager,customdiemanager)
      return prob_plot(request,dice,columnmanager,customdiemanager,target=False)
    else:
      getvars = urllib.urlencode(request.GET)

      return render(request, 'plot_prob.html', {
        'modeform': modeform,
        'columnmanager': columnmanager,
        'customdiemanager': customdiemanager,
        'getvars': getvars,
      })
  else:
    return render(request, 'probability_reference.html', {
      'modeform': modeform,
      'columnmanager': columnmanager,
      'customdiemanager': customdiemanager,
    })

def build_dice(columnmanager,customdiemanager):
  if columnmanager.is_valid() and customdiemanager.is_valid():
    # Create the corresponding die for each form.
    dice = [
      SKILL_DIE[d['skill']] + PRO_DIE[d['attribute']]
      for d in columnmanager.cleaned_data()
    ]
    dice += [ d['die'] for d in customdiemanager.cleaned_data() ]
  else:
    dice = []

  return dice

def transpose(data):
  if len(data)==0:
    return []
  if len(data)==1:
    return map(lambda x: [x],*data)
  else:
    return map(None,*data)


def prob_plot(request,dice,columnmanager,customdiemanager,target=False):
  fig = Figure(figsize=(12, 6),frameon=False)
  ax = Axes(fig,[0.07, 0.07, 0.71, 0.91])
  fig.add_axes(ax)

  base_forms = columnmanager.base_forms() + customdiemanager.base_forms()

  ymax = 0
  for (d,f) in zip(dice,base_forms):
    if target:
      result = d.probability_reach()+[0.0]
    else:
      result = d.probability()+[0.0]
    ymax = max(ymax,max(result))

    label = string.strip("%s\n%s" % (
      f.get_skill_display(),
      f.get_attribute_display(),
    ))
    ax.plot(result,'-o',label=label)
  
  ax.set_ylabel('Probability')
  if target:
    ax.set_xlabel('Target Sum')
  else:
    ax.set_xlabel('Sum')
  ax.grid(True)

  if dice:
    ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))

  canvas = FigureCanvas(fig)
  response = HttpResponse(content_type='image/png')
  canvas.print_png(response)
  return response
