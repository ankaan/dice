from heapq import heappop, heappush, heappushpop, heapreplace, heapify
import itertools

class AbstractQueue(object):
  def __init__(self,data=None):
    self._counter = itertools.count()
    if data:
      self._pq = [ self._entry(d) for d in data ]
    else:
      self._pq = []
    heapify(self._pq)

  def __eq__(self,other):
    a = self._pq[:]
    b = other._pq[:]
    if len(a) != len(b):
      return False

    for i in range(len(a)):
      if heappop(a)[2] != heappop(b)[2]:
        return False

    return True

  def _entry(self,item):
    return (self.priority(item), next(self._counter), item)

  def push(self,item):
    heappush(self._pq, self._entry(item))

  def pop(self):
    return heappop(self._pq)[2]

  def pushpop(self,item):
    return heappushpop(self._pq, self._entry(item))[2]

  def replace(self,item):
    return heapreplace(self._pq, self._entry(item))[2]

  def entries(self):
    return len(self._pq)
