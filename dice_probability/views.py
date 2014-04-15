from django import forms
from django.http import HttpResponse
from django.shortcuts import render

from dice_probability.die import LazyDie as Die
from dice_probability.die import DieParseException, from_string, pool_from_string
from dice_probability.formmanager import manager_factory

import string
import urllib

from matplotlib import use as matplot_use
matplot_use('cairo')

from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.pyplot import Axes
from dice_probability.boxplot import manual_boxplot
from pylab import yticks

MAX_DICE = 10
MAX_SIDES = 30

class ModeForm(forms.Form):
  MODE_CHOICES = (
    ('target','Target'),
    ('vs','Versus'),
    ('plot_target','Target Plot'),
    ('plot_prob','Probability Plot'),
    ('plot_box','Box Plot'),
  )

  mode =  forms.ChoiceField(choices=MODE_CHOICES,required=False)

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

CustomDieFormManager = manager_factory(CustomDieForm,max_forms=10)

def _probability_reference(request, stage):
  mode = 'target'
  if "mode" in request.GET:
    modeform = ModeForm(request.GET)
    if modeform.is_valid():
      mode = modeform.cleaned_data.get('mode','target')
  else:
    modeform = ModeForm()

  customdiemanager = CustomDieFormManager(request.GET)

  for i, f in enumerate(customdiemanager.base_forms(),1):
    f.num = i

  poolform = PoolDieForm(request.GET)

  if mode == 'target':
    dice = build_dice(customdiemanager,poolform)
    # Compute probability for each die.
    result = transpose([ d.die.probability_reach() for d in dice ])

    return render(request, 'target.html', {
      'dice': dice,
      'modeform': modeform,
      'customdiemanager': customdiemanager,
      'poolform': poolform,
      'result': result,
    })

  elif mode == 'vs':
    dice = build_dice(customdiemanager,poolform)
    result = [ [ a.die.probability_vs(b.die) for a in dice ] for b in dice ]

    return render(request, 'versus.html', {
      'dice': dice,
      'modeform': modeform,
      'customdiemanager': customdiemanager,
      'poolform': poolform,
      'result': result,
    })
  elif mode == 'plot_target':
    if stage=='plot':
      dice = build_dice(customdiemanager,poolform)
      return plot_prob(dice,target=True)
    else:
      getvars = urllib.urlencode(request.GET)

      return render(request, 'plot_target.html', {
        'modeform': modeform,
        'customdiemanager': customdiemanager,
        'poolform': poolform,
        'getvars': getvars,
      })
  elif mode == 'plot_prob':
    if stage=='plot':
      dice = build_dice(customdiemanager,poolform)
      return plot_prob(dice,target=False)
    else:
      getvars = urllib.urlencode(request.GET)

      return render(request, 'plot_prob.html', {
        'modeform': modeform,
        'customdiemanager': customdiemanager,
        'poolform': poolform,
        'getvars': getvars,
      })
  elif mode == 'plot_box':
    if stage=='plot':
      dice = build_dice(customdiemanager,poolform)
      return plot_box(dice)
    else:
      getvars = urllib.urlencode(request.GET)

      return render(request, 'plot_box.html', {
        'modeform': modeform,
        'customdiemanager': customdiemanager,
        'poolform': poolform,
        'getvars': getvars,
      })
  else:
    return render(request, 'probability_reference.html', {
      'modeform': modeform,
      'customdiemanager': customdiemanager,
      'poolform': poolform,
    })

class DieInfo(object):
  def __init__(self,die,pri,details):
    self.die = die
    self.pri = pri
    self.details = details

def build_dice(customdiemanager,poolform):
  dice = []
  if customdiemanager.is_valid() and poolform.is_valid():
    # Create the corresponding dice for each form.
    dice += [
      DieInfo(
        d,
        r+"p",
        r+"p"
      )
      for (d,r) in zip(poolform.cleaned_data['dice_pools'],poolform.rawdice)
    ]
    dice += [
      DieInfo(
        f.cleaned_data['die'],
        "Custom %d" % f.num,
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

    ax.plot(result,'-o',label=d.pri)
  
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

  if boxes:
    manual_boxplot(ax, boxes, vert=0)
  else:
    ax.plot([])

  ax.set_yticklabels([ d.pri for d in reversed(dice) ])

  ax.set_xlabel('Sum')

  ax.grid(True)

  canvas = FigureCanvas(fig)
  response = HttpResponse(content_type='image/png')
  canvas.print_png(response)
  return response

