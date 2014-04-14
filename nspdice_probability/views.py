from django import forms
from django.http import HttpResponse
from django.shortcuts import render

from nspdice_probability.die import LazyDie as Die
from nspdice_probability.die import DieParseException, from_string, pool_from_string
from nspdice_probability.formmanager import manager_factory

import string
import urllib

from matplotlib import use as matplot_use
matplot_use('cairo')

from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.pyplot import Axes
from nspdice_probability.boxplot import manual_boxplot
from pylab import yticks

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
    ('plot_box','Box Plot'),
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

class CustomDieForm(forms.Form):
  die = forms.CharField(required=False)

  def __init__(self,*args,**kwargs):
    super(CustomDieForm, self).__init__(*args,**kwargs)

    self.num = None
    self.rawdice = [""]

  def clean_die(self):
    raw = self.cleaned_data['die']

    try:
      (d,self.rawdice) = from_string(Die, raw, max_sides=30, max_dice=15)
      return d
    except DieParseException as e:
      raise forms.ValidationError(*e.args)

  def keep(self):
    if not self.is_valid():
      return True
    else:
      return self.cleaned_data['die'] != None

class PoolDieForm(forms.Form):
  dice_pools = forms.CharField(required=False)

  def __init__(self,*args,**kwargs):
    super(PoolDieForm, self).__init__(*args,**kwargs)
    self.rawdice = [""]

  def clean_dice_pools(self):
    raw = self.cleaned_data['dice_pools']

    try:
      (d,self.rawdice) = pool_from_string(Die, raw, max_dice=30)
      return d
    except DieParseException as e:
      raise forms.ValidationError(*e.args)

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

  poolform = PoolDieForm(request.GET)

  if mode == 'target':
    dice = build_dice(columnmanager,customdiemanager,poolform)
    # Compute probability for each die.
    result = transpose([ d.die.probability_reach() for d in dice ])

    return render(request, 'target.html', {
      'dice': dice,
      'modeform': modeform,
      'columnmanager': columnmanager,
      'customdiemanager': customdiemanager,
      'poolform': poolform,
      'result': result,
    })

  elif mode == 'vs':
    dice = build_dice(columnmanager,customdiemanager,poolform)
    result = [ [ a.die.probability_vs(b.die) for a in dice ] for b in dice ]

    return render(request, 'versus.html', {
      'dice': dice,
      'modeform': modeform,
      'columnmanager': columnmanager,
      'customdiemanager': customdiemanager,
      'poolform': poolform,
      'result': result,
    })
  elif mode == 'plot_target':
    if stage=='plot':
      dice = build_dice(columnmanager,customdiemanager,poolform)
      return plot_prob(dice,target=True)
    else:
      getvars = urllib.urlencode(request.GET)

      return render(request, 'plot_target.html', {
        'modeform': modeform,
        'columnmanager': columnmanager,
        'customdiemanager': customdiemanager,
        'poolform': poolform,
        'getvars': getvars,
      })
  elif mode == 'plot_prob':
    if stage=='plot':
      dice = build_dice(columnmanager,customdiemanager,poolform)
      return plot_prob(dice,target=False)
    else:
      getvars = urllib.urlencode(request.GET)

      return render(request, 'plot_prob.html', {
        'modeform': modeform,
        'columnmanager': columnmanager,
        'customdiemanager': customdiemanager,
        'poolform': poolform,
        'getvars': getvars,
      })
  elif mode == 'plot_box':
    if stage=='plot':
      dice = build_dice(columnmanager,customdiemanager,poolform)
      return plot_box(dice)
    else:
      getvars = urllib.urlencode(request.GET)

      return render(request, 'plot_box.html', {
        'modeform': modeform,
        'columnmanager': columnmanager,
        'customdiemanager': customdiemanager,
        'poolform': poolform,
        'getvars': getvars,
      })
  else:
    return render(request, 'probability_reference.html', {
      'modeform': modeform,
      'columnmanager': columnmanager,
      'customdiemanager': customdiemanager,
      'poolform': poolform,
    })

class DieInfo(object):
  def __init__(self,die,pri,sec,details):
    self.die = die
    self.pri = pri
    self.sec = sec
    self.details = details

  def both(self):
    return string.strip("%s\n%s" % (
      self.pri,
      self.sec
    ))

def build_dice(columnmanager,customdiemanager,poolform):
  dice = []
  if columnmanager.is_valid() and customdiemanager.is_valid() and poolform.is_valid():
    # Create the corresponding die for each form.
    dice += [
      DieInfo(
        SKILL_DIE[f.cleaned_data['skill']] + PRO_DIE[f.cleaned_data['attribute']],
        f.get_skill_display(),
        f.get_attribute_display(),
        "%s\n%s"%(f.get_skill_display(),f.get_attribute_display())
      )
      for f in columnmanager.base_forms()
    ]
    dice += [
      DieInfo(
        d,
        r+"p",
        "",
        r+"p"
      )
      for (d,r) in zip(poolform.cleaned_data['dice_pools'],poolform.rawdice)
    ]
    dice += [
      DieInfo(
        f.cleaned_data['die'],
        "Custom %d" % f.num,
        "",
        "Custom %d:\n%s"%(f.num,string.join(f.rawdice))
      )
      for f in customdiemanager.base_forms()
    ]

  return dice

def transpose(data):
  if len(data)==0:
    return []
  if len(data)==1:
    return map(lambda x: [x],*data)
  else:
    return map(None,*data)

def plot_prob(dice,target=False):
  fig = Figure(figsize=(12, 6),frameon=False)
  ax = Axes(fig,[0.07, 0.07, 0.71, 0.91])
  fig.add_axes(ax)

  for d in dice:
    if target:
      result = d.die.probability_reach()+[0.0]
    else:
      result = d.die.probability()+[0.0]

    ax.plot(result,'-o',label=d.both())
  
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

_BOX_PERCENTILES = [0.95, 0.75, 0.5, 0.25, 0.05]

def plot_box(dice):
  fig = Figure(figsize=(12, 6),frameon=False)
  ax = Axes(fig,[0.15, 0.07, 0.84, 0.91])
  fig.add_axes(ax)

  try:
    boxes = [ d.die.percentile_reach(_BOX_PERCENTILES) for d in reversed(dice) ]
  except ValueError:
    boxes = []
  manual_boxplot(ax, boxes, vert=0)

  ax.set_yticklabels([ d.both() for d in reversed(dice) ])

  ax.set_xlabel('Sum')

  ax.grid(True)

  canvas = FigureCanvas(fig)
  response = HttpResponse(content_type='image/png')
  canvas.print_png(response)
  return response

