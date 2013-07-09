from nspdice_probability.die import Die, DieParseException
from django.test import TestCase

import operator

class TestDie(TestCase):

  def test_init(self):
    self.assertRaises(ZeroDivisionError,Die,0)

    self.assertEquals(Die(4).probability(),[0.0, 0.25, 0.25, 0.25, 0.25])
    self.assertEquals(Die([]).probability(),[1.0])

    seq = [0.0, 0.2, 0.3, 0.5]
    self.assertEquals(Die(seq).probability(),seq)

    self.assertEqual(Die(5),Die([0.0, 0.2, 0.2, 0.2, 0.2, 0.2]))

    self.assertRaises(TypeError,Die,(1,2,3))
    self.assertRaises(TypeError,Die,Die(3))
    self.assertRaises(ValueError,Die,-1)

  def test_const(self):
    self.assertEquals(Die.const(0).probability(),[1.0])
    self.assertEquals(Die.const(1).probability(),[0.0,1.0])
    self.assertEquals(Die.const(2).probability(),[0.0,0.0,1.0])

  def test_add(self):
    d = Die(2)+Die(2)
    self.assertEquals(d.probability(),[0.0, 0.0, 0.25, 0.5, 0.25])

    left  = (Die(2) + Die(10)) + Die(20)
    right = Die(2) + (Die(10) + Die(20))
    self.assertTrue(left.similar_to(right))

    inc = Die(8) + Die(12)
    dec = Die(12) + Die(8)
    self.assertEquals(inc, dec)

    a = Die(10) + Die(10) 
    b = Die(12) + Die(8)
    self.assertNotEqual(a, b)

    a = Die(20)
    b = Die(10) + Die(10)
    self.assertNotEqual(a, b)

  def test_eq(self):
    self.assertEqual(Die(2),Die(2))
    self.assertEqual(Die(2),Die([0,0.5,0.5]))
    self.assertNotEqual(Die(2),Die(4))
    self.assertEqual(Die([0.0,1,1]),Die([0,0.5,0.5]))
    self.assertEqual(Die([0.0,1,1])+Die(10),Die([0,0.5,0.5])+Die(10))

  def test_duplicate(self):
    self.assertEqual(Die(20).duplicate(0), Die.const(0))
    self.assertEqual(Die(20).duplicate(1), Die(20))
    self.assertEqual(Die(20).duplicate(2), Die(20)+Die(20))
    self.assertEqual(Die(8).duplicate(3), Die(8)+Die(8)+Die(8))

    a = Die(5).duplicate(20)
    b = Die(5)+Die(5).duplicate(19)
    self.assertTrue(a.similar_to(b))

    a = (Die(5) + Die(10)).duplicate(3)
    b = Die(5).duplicate(3) + Die(10).duplicate(3)
    self.assertTrue(a.similar_to(b))

  def test_probability(self):
    self.assertEquals(Die(4).probability(),[0.0, 0.25, 0.25, 0.25, 0.25])
    self.assertEquals(Die([]).probability(),[1.0])
    self.assertEquals(Die(5),Die([0.0, 0.2, 0.2, 0.2, 0.2, 0.2]))

    self.assertEqual(Die([0.0,1,1]),Die([0,0.5,0.5]))

  def test_probability_reach(self):
    self.assertEquals(Die(4).probability_reach(),[1.0,1.0,0.75,0.5,0.25])

  def test_probability_vs(self):
    p = 0.5*0.75 + 0.5*0.5
    self.assertEquals(Die(4).probability_vs(Die(2)),p)

    d0 = Die(4)+Die(6)+Die(8)+Die(8)
    d1 = Die(4)+Die(6)+Die(8)+Die(10)+Die(8)
    p = d0.probability_vs(d1) + d1.probability_vs(d0) + d0.probability_eq(d1)
    self.assertEquals(round(p,7),1.0)

  def test_probability_eq(self):
    self.assertEquals(Die(4).probability_eq(Die(4)),0.25)

    p = 0.5*0.25
    self.assertEquals(Die(4).probability_eq(Die(8)),p)
    self.assertEquals(Die(8).probability_eq(Die(4)),p)

  def test_roll(self):
    self.assertTrue(Die(10).roll() in range(1,11))

    self.assertEquals(Die(10).roll(0.09),1)
    self.assertEquals(Die(10).roll(0.59),6)

    self.assertEquals(Die([0.0,0.2,0.7,0.1]).roll(0),1)
    self.assertEquals(Die([0.0,0.2,0.7,0.1]).roll(0.000001),1)
    self.assertEquals(Die([0.0,0.2,0.7,0.1]).roll(0.199999),1)
    self.assertEquals(Die([0.0,0.2,0.7,0.1]).roll(0.200001),2)
    self.assertEquals(Die([0.0,0.2,0.7,0.1]).roll(0.899999),2)
    self.assertEquals(Die([0.0,0.2,0.7,0.1]).roll(0.900001),3)
    self.assertEquals(Die([0.0,0.2,0.7,0.1]).roll(0.999999),3)

    self.assertRaises(ValueError,Die(10).roll,-0.2)
    self.assertRaises(ValueError,Die(10).roll,1.0)

  def test_from_string(self):
    self.assertEquals(Die.from_string(""),None)
    self.assertEquals(Die.from_string(" "),None)
    self.assertEquals(Die.from_string("d4"),Die(4))
    self.assertEquals(Die.from_string("2d6"),Die(6).duplicate(2))
    self.assertEquals(Die.from_string(" D12"),Die(12))
    self.assertEquals(Die.from_string("13  "),Die.const(13))
    self.assertEquals(Die.from_string("13 2"),Die.const(13)+Die.const(2))
    self.assertEquals(Die.from_string("d20 d8 d4"),Die(20)+Die(8)+Die(4))
    self.assertEquals(Die.from_string("d4-d4"),Die(4))
    self.assertEquals(
        Die.from_string("d4-d20"),
        Die(4) + Die(6) + Die(8) + Die(10) + Die(12) + Die(20))

    self.assertRaises(DieParseException,Die.from_string,"12e3")
    self.assertRaises(DieParseException,Die.from_string,"h")
    self.assertRaises(DieParseException,Die.from_string,"3d3d2")


    self.assertEquals(
        Die.from_string("5d10",max_dice=5,max_sides=10),
        Die(10).duplicate(5))

    self.assertEquals(
        Die.from_string("2d10 3d10",max_dice=5,max_sides=10),
        Die(10).duplicate(2) + Die(10).duplicate(3))

    self.assertRaises(DieParseException,
        Die.from_string, "6d10", max_dice=5, max_sides=10)

    self.assertRaises(DieParseException,
        Die.from_string, "2d2 4d3", max_dice=5, max_sides=10)

    self.assertRaises(DieParseException,
        Die.from_string, "2d11", max_dice=5, max_sides=10)

  def test_max_side(self):
    self.assertRaises(StopIteration, Die([0]).max_side)
    self.assertRaises(StopIteration, Die([0,0,0,0]).max_side)
    self.assertEquals(Die([]).max_side(), 0)
    self.assertEquals(Die([1]).max_side(), 0)
    self.assertEquals(Die([1,0]).max_side(), 0)
    self.assertEquals(Die([0,1,2,3,4,5,1]).max_side(), 6)
    self.assertEquals(Die([0,2,2,3,4,9,0]).max_side(), 5)
    self.assertEquals(Die([0,9,0,2,1,0,0]).max_side(), 4)

