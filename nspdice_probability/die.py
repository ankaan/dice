"""Combine dice and compute probabilities for the composite die, also allow rolling of such dice."""
from itertools import *
import operator
import random
import re

class DieParseException(Exception):
  pass

class Die(object):
  """A generalized die."""

  def __init__(self,sides):
    """
    Create a die based on a liste of probabilities where the index is the outcome or a fair die with the given number of sides.
    """

    self._normalized = False
    self._reach = None

    if type(sides) is list:
      if len(sides)==0:
        self._sides = [1.0]
      else:
        self._sides = sides
    elif type(sides) is int:
      if sides>=0:
        self._sides = [0.0] + [1.0/sides]*sides
      else:
        raise ValueError('If sides in an integer, it must be greater than 0')
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

  _re_const = re.compile('^(\d+)$')
  _re_single = re.compile('^[dD](\d+)$')
  _re_multi = re.compile('^(\d+)[dD](\d+)$')
  _re_seq = re.compile('^[dD](\d+)-[dD](\d+)$')

  _die_seq = [4,6,8,10,12,20]

  @classmethod
  def from_string(self,raw,max_sides=None,max_dice=None):
    """
    Create the composite die described in the string.

    Arguments:
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
    die = Die.const(0)

    # For each proposed die
    for rd in rawdice:
      # Check for constants
      m = self._re_const.match(rd)
      if m:
        die += Die.const(readsides(m.group(1)))
        continue
      
      # Check for single die
      m = self._re_single.match(rd)
      if m:
        countdice(1)
        die += Die(readsides(m.group(1)))
        continue
      
      # Check for multiple copies of same die
      m = self._re_multi.match(rd)
      if m:
        copies = int(m.group(1))
        sides = readsides(m.group(2))

        countdice(copies)

        die += Die(sides).duplicate(copies)
        continue
      
      # Check for die sequences
      m = self._re_seq.match(rd)
      if m:
        try:
          start = self._die_seq.index( int(m.group(1)) )
          stop = self._die_seq.index( int(m.group(2)) )
          if start>stop:
            raise ValueError()
        except ValueError:
          raise DieParseException("Invalid die sequence: %s"%rd)

        countdice(stop+1-start)

        dice = [ Die(n) for n in self._die_seq[start:stop+1] ]
        die += reduce(operator.add, dice, Die.const(0))

        continue

      # None of the above matched; the die is invalid.
      raise DieParseException("Invalid die: %s"%rd)
      
    return die

  def __add__(self,other):
    """
    Create a new composite die by adding two dice together.
    """

    if type(other) is not Die:
      raise TypeError('Only a die can be added to another die.')

    outcomes = [ (sv+ov,sp*op) for (sv,sp) in enumerate(self._sides)
                               for (ov,op) in enumerate(other._sides) ]

    sides = [0.0] + [0.0] * max([ v for (v,p) in outcomes ])
    for (v,p) in outcomes:
      sides[v] += p

    return Die(sides)

  def __eq__(self,other):
    self._normalize()
    other._normalize()
    return self._sides == other._sides

  def similar_to(self,other,ndigits=7):
    self._normalize()
    other._normalize()
    return all([ round(x-y,ndigits)==0.0 for (x,y) in
      zip(self._sides,other._sides) ])

  def duplicate(self,num):
    """Duplicate the die the given number of times."""
    return reduce(operator.add, [self]*num, Die.const(0))

  def _normalize(self):
    """Normalize probabilities."""
    if not self._normalized:
      total_probability = sum(self._sides)
      self._sides = [ s/total_probability for s in self._sides ]
      self._normalized = True

  def probability(self):
    """Get the probabilities for rolling the positional number."""
    self._normalize()
    return self._sides

  def _compute_reach(self):
    """Compute the probabilities to roll at least the positional number."""
    self._normalize()

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
      rnd -=w
      if rnd < 0:
        return i

class DiceCounter(object):
  def __init__(self,max_dice):
    self._max_dice = max_dice
    self._num_dice = 0

  def count(self,dice):
    self._num_dice += dice
    if self._max_dice != None and self._num_dice > self._max_dice:
      raise DieParseException("Only %d dice are allowed."%self._max_dice)

class SideReader(object):
  def __init__(self,max_sides):
    self._max_sides = max_sides

  def read(self,raw):
    sides = int(raw)
    if self._max_sides != None and sides > self._max_sides:
      raise DieParseException("Max %d sides for a die"%self._max_sides)
    return sides

