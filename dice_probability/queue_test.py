from dice_probability.queue import AbstractQueue
from django.test import TestCase
from heapq import heapify

class Queue(AbstractQueue):
  def priority(self,x):
    return x[0]

class TestQueue(TestCase):
  def test_init(self):
    q0 = Queue([])
    q1 = Queue()
    self.assertEquals(q0, q1)

    q0 = Queue()
    q0.push((2,'b'))
    q0.push((3,'c'))
    q0.push((1,'a'))
    q0.push((4,'d'))

    q1 = Queue([
      (3,"c"),
      (1,"a"),
      (4,"d"),
      (2,"b")])
    self.assertEquals(q0, q1)

  def test_eq(self):
    q0 = Queue()
    q0.push((2,'b'))
    q0.push((3,'c'))
    q0.push((1,'a'))
    q0.push((4,'d'))

    q1 = Queue()
    q1.push((3,'c'))
    q1.push((4,'d'))
    q1.push((2,'b'))
    q1.push((1,'a'))

    self.assertEquals(q0,q1)

    q0 = Queue()
    q0.push((2,'b'))
    q0.push((3,'c'))
    q0.push((1,'a'))
    q0.push((4,'d'))

    q1 = Queue()
    q1.push((3,'x'))
    q1.push((4,'d'))
    q1.push((2,'b'))
    q1.push((1,'a'))

    self.assertNotEquals(q0,q1)

    q0 = Queue()
    q0.push((2,'b'))
    q0.push((3,'c'))
    q0.push((1,'a'))
    q0.push((4,'d'))

    q1 = Queue()
    q1.push((3,'c'))
    q1.push((4,'d'))
    q1.push((2,'d'))
    q1.push((2,'b'))
    q1.push((1,'a'))

    self.assertNotEquals(q0,q1)

    q0 = Queue()
    q0.push((1,'a'))
    q0.push((2,'b'))
    q0.push((3,'c'))
    q0.push((4,'d'))

    q1 = Queue()
    q1.push((1,'a'))
    q1.push((2,'b'))
    q1.push((3,'c'))
    q1.push((4,'d'))
    q1.push((5,'e'))

    self.assertNotEquals(q0,q1)

  def test_basic(self):
    q = Queue()

    # Make sure it can sort.
    q.push((2,'b'))
    q.push((3,'c'))
    q.push((1,'a'))
    q.push((4,'d'))
    self.assertEquals(q.pop(),(1,'a'))
    self.assertEquals(q.pop(),(2,'b'))
    self.assertEquals(q.pop(),(3,'c'))
    self.assertEquals(q.pop(),(4,'d'))

    # Make sure it is stable if priorities are equal.
    q.push((2,'b'))
    q.push((3,'x'))
    q.push((2,'a'))
    q.push((1,'z'))
    self.assertEquals(q.pop(),(1,'z'))
    self.assertEquals(q.pop(),(2,'b'))
    self.assertEquals(q.pop(),(2,'a'))
    self.assertEquals(q.pop(),(3,'x'))

  def test_pushpop(self):
    q = Queue()

    q.push((1,'a'))
    q.push((2,'bx'))
    q.push((4,'d'))
    q.push((3,'c'))

    self.assertEquals(q.pop(),(1,'a'))
    self.assertEquals(q.pushpop((0,'0')),(0,'0'))
    self.assertEquals(q.pushpop((2,'by')),(2,'bx'))
    self.assertEquals(q.pushpop((2,'bx')),(2,'by'))
    self.assertEquals(q.pop(),(2,'bx'))
    self.assertEquals(q.pop(),(3,'c'))
    self.assertEquals(q.pop(),(4,'d'))

  def test_replace(self):
    q = Queue()

    q.push((1,'a'))
    q.push((2,'bx'))
    q.push((4,'d'))
    q.push((3,'c'))

    self.assertEquals(q.pop(),(1,'a'))
    self.assertEquals(q.replace((0,'0')),(2,'bx'))
    self.assertEquals(q.replace((2,'by')),(0,'0'))
    self.assertEquals(q.replace((2,'bx')),(2,'by'))
    self.assertEquals(q.pop(),(2,'bx'))
    self.assertEquals(q.pop(),(3,'c'))
    self.assertEquals(q.pop(),(4,'d'))


  def test_entries(self):
    q = Queue()

    q.push((1,'a'))
    self.assertEquals(q.entries(),1)
    q.push((2,'b'))
    q.push((3,'c'))
    self.assertEquals(q.entries(),3)
