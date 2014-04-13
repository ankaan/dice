"""
Combine dice and compute probabilities for the composite die, also allow rolling of such dice.
"""
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
    self._cmp = None

    if isinstance(arg,Die):
      self._sides = arg._sides
      self._reach = arg._reach
    elif type(arg) is list:
      if len(arg)==0:
        self._sides = [1.0]
      elif isinstance(arg[0],Die):
        die = sum(arg[1:], arg[0])
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
      raise TypeError('Die.__init__() either takes a die, a list or an integer.')

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

    if not isinstance(other,Die):
      raise TypeError('Only a die can be added to another die.')

    sides = [0.0]*( self.max_side() + other.max_side() + 1 )

    outcomes = ( (sv+ov,sp*op) for (sv,sp) in enumerate(self._sides)
                               for (ov,op) in enumerate(other._sides) )

    for (v,p) in outcomes:
      sides[v] += p

    return Die(sides)

  def duplicate(self,num):
    """Duplicate the die the given number of times."""
    if type(num)!=int or num<0:
      raise TypeError(
        "Number of times to duplicate must be a non-negative int.")

    if num == 0:
      return Die.const(0)

    # Find all powers of 2 less than or equal to num
    pow2 = [1]
    while pow2[-1] <= num:
      pow2.append(pow2[-1]*2)
    pow2.pop()

    # Cache has space for all such powers of 2
    cache = [None]*len(pow2)

    # Populate cache
    cache[0] = self
    die = self
    for i in xrange(1,len(pow2)):
      die += die
      cache[i] = die
    # Cache now contains: cache[i] = self.duplicate(2**i)

    req = [None]*len(pow2)
    rest = num
    for i, p in enumerate(reversed(pow2),1):
      if p <= rest:
        req[-i] = cache[-i]
        rest -= p

    return fastsum(d for d in req if d is not None)

  def _duplicate(self,num,cache):
    """Duplicate the die the given number of times."""
    try:
      return cache[num]
    except KeyError:
      die = cache[num/2]
      die += die
      if num%2 != 0:
        die += cache[num%2]

  def max_side(self):
    """Get the biggest possible outcome."""
    return len(self._sides) - 1

  def __eq__(self,other):
    """
    Check if two dice are similar enough. Workaround for inexact float results.
    """
    return self.similar_to(other)

  def __cmp__(self,other):
    """
    Compare two dice. Will consider two dice that differ less than 1e-12 to be
    equal.
    """
    if other is None:
      return 1
    elif self.similar_to(other):
      return 0
    else:
      return cmp(self._sides,other._sides)

  def similar_to(self,other,ndigits=12):
    """
    Check if two dice are similar enough Workaround for inexact float results.
    """
    for (x,y) in map(None,self._sides, other._sides):
      if x!=y:
        if x is None or y is None:
          return False
        elif round(x-y,ndigits)!=0.0:
          return False
    return True

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

  def reset(self):
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

_POOL_DIE = Die([7,4,1])

_RE_CONST = re.compile('^(\d+)$')
_RE_SINGLE = re.compile('^[dD](\d+)$')
_RE_MULTI = re.compile('^(\d+)[dD](\d+)$')
_RE_SEQ = re.compile('^[dD](\d+)-[dD](\d+)$')

_RE_POOL = re.compile('^(\d*)[pP]$')

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

    # Check for a pool die
    m = _RE_POOL.match(rd)
    if m:
      try:
        copies = int(m.group(1))
      except ValueError:
        copies = 1

      countdice(copies)
      readsides(3)

      die += makedie(_POOL_DIE).duplicate(copies)
      continue

    # None of the above matched; the die is invalid.
    raise DieParseException("Invalid die: %s"%rd)
    
  return die

def pool_from_string(makedie,raw,max_dice=None):
  """
  Create the list of dice pools described in the string.

  Arguments:
    makedie:    The class of die to create.
    raw:        The input string that describes the die.
    max_dice:   Maximum number of dice described in the input.
                None for infinite, the default.
  """
  rawdice = raw.split()
  dice = []

  counter = DiceCounter(max_dice)

  # For each proposed die
  for rd in rawdice:
    try:
      copies = int(rd)
      if copies<0:
        raise ValueError()
    except ValueError:
      raise DieParseException("Invalid die: %s"%rd)

    counter.reset()
    dice.append(makedie(_POOL_DIE).duplicate(copies))
    counter.count(copies)
    
  return dice

class LazyDie(object):
  """A lazy implementation of a die."""

  @inheritdoc(Die)
  def __init__(self,arg=0):
    if type(arg) is list and len(arg)>0 and isinstance(arg[0],(Die,LazyDie)):
      if all(isinstance(a,Die) for a in arg):
        self._dice = [ (a,1) for a in arg ]
      elif all(isinstance(a,LazyDie) for a in arg):
        self._dice = sum(arg[1:], arg[0])._dice
      else:
        raise ValueError("Invalid side definition.")
    elif type(arg) is list and len(arg)>0 and type(arg[0]) is tuple:
      if all(type(a) is tuple and isinstance(a[0],Die) for a in arg):
        self._dice = arg
      else:
        raise ValueError("Invalid side definition.")
    elif isinstance(arg,LazyDie):
      self._dice = arg._dice[:]
    elif isinstance(arg,Die):
      self._dice = [ (arg,1) ]
    else:
      self._dice = [ (Die(arg),1) ]

  @classmethod
  @inheritdoc(Die)
  def const(self,*args,**kwargs):
    return LazyDie(Die.const(*args,**kwargs))

  @inheritdoc(Die)
  def __add__(self,other):
    return LazyDie(self._dice + other._dice)

  @inheritdoc(Die)
  def duplicate(self,num):
    return LazyDie([ (d,n*num) for (d,n) in self._dice if n*num>0 ])

  @inheritdoc(Die)
  def max_side(self):
    return sum(d.max_side() for (d,n) in self._dice)

  def collapse(self):
    """Collapse the lazy die into a single die. Do all the heavy computation."""
    if len(self._dice)>1 or self._dice[0][1]>1:
      self._dice.sort(reverse=True)

      dice = []
      while len(self._dice)>0:
        (d,n) = self._dice.pop()
        while len(self._dice)>0 and self._dice[-1][0]==d:
          n += self._dice.pop()[1]
        dice.append(d.duplicate(n))

      self._dice = [(fastsum(dice),1)]

  def collapsed(self):
    """Get the collapsed die, all lazily described dice combined into one."""
    self.collapse()
    return self._dice[0][0]
      
  @inheritdoc(Die)
  def __cmp__(self,other):
    if other is None:
      return 1
    return self.collapsed().__cmp__(other.collapsed())

  @inheritdoc(Die)
  def similar_to(self,other,*args,**kwargs):
    return self.collapsed().similar_to(other.collapsed(),*args,**kwargs)

  @inheritdoc(Die)
  def probability(self,*args,**kwargs):
    return self.collapsed().probability(*args,**kwargs)

  @inheritdoc(Die)
  def probability_reach(self,*args,**kwargs):
    return self.collapsed().probability_reach(*args,**kwargs)

  @inheritdoc(Die)
  def probability_vs(self,other,*args,**kwargs):
    return self.collapsed().probability_vs(other.collapsed(),*args,**kwargs)

  @inheritdoc(Die)
  def probability_eq(self,other,*args,**kwargs):
    return self.collapsed().probability_eq(other.collapsed(),*args,**kwargs)

  @inheritdoc(Die)
  def roll(self,*args,**kwargs):
    return self.collapsed().roll(*args,**kwargs)

class DieQueue(AbstractQueue):
  def priority(self,obj):
    return obj.max_side()

def fastsum(dice):
  """
  Sums upp all dice in dice (must be at least length 1). Addition is done in
  the order such that at each step the two candidates with smallest maximum
  sides are summed up and returned to the pool of items to sum.
  """
  dieq = DieQueue(dice)

  die = dieq.pop()
  while dieq.entries()>0:
    die = dieq.pushpop(die)
    die += dieq.pop()

  return die
