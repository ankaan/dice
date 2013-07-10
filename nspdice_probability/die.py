"""
Combine dice and compute probabilities for the composite die, also allow rolling of such dice.
"""
from itertools import *
import operator
import random
import re

from nspdice_probability.queue import AbstractQueue
from nspdice_probability.doc import docfrom, inheritdoc

class DieParseException(Exception):
  """
  Raised if it was not possible to create a composite die from the string
  description.
  """
  pass

class Die(object):
  """A generalized die."""

  def __init__(self,arg):
    """
    Create a die based on a liste of probabilities where the index is the
    outcome or a fair die with the given number of sides. It is also possible
    to supply another die to create a duplicate of or a list of dice to sum.
    """

    self._reach = None

    if type(arg) is Die:
      self._sides = arg._sides
      self._reach = arg._reach
    if type(arg) is list:
      if len(arg)==0:
        self._sides = [1.0]
      elif type(arg[0]) is Die:
        die = reduce(operator.add, arg, Die.const(0))
        self._sides = die._sides
        self._reach = die._reach
      else:
        total_probability = float(sum(arg))

        if total_probability == 0.0 or any(float(s)<0.0 for s in arg):
          raise ValueError('Invalid probabilities.')

        self._sides = [ float(s)/total_probability for s in arg ]

        for (i,s) in enumerate(reversed(self._sides),1):
          if s>0.0:
            break
          else:
            del self._sides[-i]
    elif type(arg) is int:
      if arg>0:
        self._sides = [0.0] + [1.0/arg]*arg
      elif arg==0:
        self._sides = [1.0]
      else:
        raise ValueError('A die cannot have negative number of sides.')
    else:
      raise TypeError('Die.__init() either takes a list or an integer.')

  @classmethod
  def const(self,value):
    """
    Create a die that always shows a certain value.
    """
    if type(value) is not int:
      raise TypeError('Die.const() only takes an integer.')

    return self([0.0]*value + [1.0])

  def __add__(self,other):
    """
    Create a new composite die by adding two dice together.
    """

    if type(other) is not Die:
      raise TypeError('Only a die can be added to another die.')

    sides = [0.0]*( self.max_side() + other.max_side() + 1 )

    outcomes = ( (sv+ov,sp*op) for (sv,sp) in enumerate(self._sides)
                               for (ov,op) in enumerate(other._sides) )

    for (v,p) in outcomes:
      sides[v] += p

    return Die(sides)

  def max_side(self):
    return len(self._sides) - 1

  def __eq__(self,other):
    """
    Check if two dice are similar enough. Workaround for inexact float results.
    """
    return self.similar_to(other)

  def similar_to(self,other,ndigits=12):
    """
    Check if two dice are similar enough. Workaround for inexact float results.
    """
    return all([ round(x-y,ndigits)==0.0 for (x,y) in
        map(None,self._sides,other._sides) ])

  def duplicate(self,num):
    """Duplicate the die the given number of times."""
    return Die([self]*num)

  def probability(self):
    """Get the probabilities for rolling the positional number."""
    return self._sides

  def _compute_reach(self):
    """Compute the probabilities to roll at least the positional number."""

    if self._reach is None:
      self._reach = []

      s = 1.0
      for w in self._sides:
        self._reach.append(s)
        s -= w

  def probability_reach(self):
    """Get the probabilities to roll at least the positional number."""
    self._compute_reach()
    return self._reach

  def probability_vs(self,opponent):
    """Compute probability to roll higher than opponent die."""
    # For each possible opponent outcome, compute the propability to reach at
    # least 1 more than that. Sum that up and we have the probability to beat
    # the opponent.
    return sum([ p*pr for (p,pr) in 
      zip(opponent.probability(), self.probability_reach()[1:]) ])

  def probability_eq(self,other):
    """Compute probability that two different die roll the same result."""
    return sum([ sp*op for (sp,op) in 
      zip(self.probability(),other.probability()) ])

  def roll(self,rnd=None):
    """Roll the die."""
    if rnd is None: 
      rnd = random.random()
    elif not (0.0 <= rnd < 1.0):
      raise ValueError("rnd must be in [0.0, 1.0)")
    for i, w in enumerate(self._sides):
      rnd -= w
      if rnd < 0.0:
        return i

class DiceCounter(object):
  """
  Count number of dice.
  """
  def __init__(self,max_dice):
    """
    Arguments:
      max_dice:   The maximum number of dice allowed.
    """
    self._max_dice = max_dice
    self._num_dice = 0

  def count(self,dice):
    """Register the given number of dice."""
    self._num_dice += dice
    if self._max_dice != None and self._num_dice > self._max_dice:
      raise DieParseException("Only %d dice are allowed."%self._max_dice)

class SideReader(object):
  """
  Read the number of sides (an integer) from a string, taking into account the
  maximum number of sides for a die.
  """
  def __init__(self,max_sides):
    """
    Arguments:
      max_sides:  The maximum number of sides allowed for a die.
    """
    self._max_sides = max_sides

  def read(self,raw):
    """Read number of sides from a string."""
    sides = int(raw)
    if self._max_sides != None and sides > self._max_sides:
      raise DieParseException("Max %d sides for a die"%self._max_sides)
    return sides

_RE_CONST = re.compile('^(\d+)$')
_RE_SINGLE = re.compile('^[dD](\d+)$')
_RE_MULTI = re.compile('^(\d+)[dD](\d+)$')
_RE_SEQ = re.compile('^[dD](\d+)-[dD](\d+)$')

_DIE_SEQ = [4,6,8,10,12,20]

def from_string(makedie,raw,max_sides=None,max_dice=None):
  """
  Create the composite die described in the string.

  Arguments:
    makedie:    The class of die to create.
    raw:        The input string that describes the die.
    max_sides:  Maximum number of sides a die may have in the input.
                None for infinite, the default.
    max_dice:   Maximum number of dice described in the input.
                None for infinite, the default.
  """
  rawdice = raw.split()
  if len(rawdice) == 0:
    return None

  countdice = DiceCounter(max_dice).count
  readsides = SideReader(max_sides).read
  
  # Place-holder die that always rolls a sum of 0
  die = makedie.const(0)

  # For each proposed die
  for rd in rawdice:
    # Check for constants
    m = _RE_CONST.match(rd)
    if m:
      die += makedie.const(readsides(m.group(1)))
      continue
    
    # Check for single die
    m = _RE_SINGLE.match(rd)
    if m:
      countdice(1)
      die += makedie(readsides(m.group(1)))
      continue
    
    # Check for multiple copies of same die
    m = _RE_MULTI.match(rd)
    if m:
      copies = int(m.group(1))
      sides = readsides(m.group(2))

      countdice(copies)

      die += makedie(sides).duplicate(copies)
      continue
    
    # Check for die sequences
    m = _RE_SEQ.match(rd)
    if m:
      try:
        start = _DIE_SEQ.index( int(m.group(1)) )
        stop = _DIE_SEQ.index( int(m.group(2)) )
        if start>stop:
          raise ValueError()
      except ValueError:
        raise DieParseException("Invalid die sequence: %s"%rd)

      countdice(stop+1-start)

      die += makedie([ makedie(n) for n in _DIE_SEQ[start:stop+1] ])

      continue

    # None of the above matched; the die is invalid.
    raise DieParseException("Invalid die: %s"%rd)
    
  return die


class DieQueue(AbstractQueue):
  def priority(self,obj):
    return obj.max_side()

class LazyDie(object):
  """A lazy implementation of a die."""

  @inheritdoc(Die)
  def __init__(self,sides=None):
    self._dice = [ Die(sides) ]
    pass

  @classmethod
  @inheritdoc(Die)
  def const(self,*args,**kwargs):
    return LazyDie(Die.const(*args,**kwargs))

  @inheritdoc(Die)
  def __add__(self,other):
    dice = self._dice + other._dice
