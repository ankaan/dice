from nspdice_probability.die import Die, LazyDie
from nspdice_probability.die import DieParseException, from_string, pool_from_string, fastsum
from django.test import TestCase

class TestDie(TestCase):

  def test_init(self):
    for d in (Die,LazyDie):
      self.assertEquals(d(0).probability(),[1.0])

      self.assertEquals(d(4).probability(),[0.0, 0.25, 0.25, 0.25, 0.25])

      self.assertEquals(d([]).probability(),[1.0])
      self.assertEquals(d([0,0.5,0.5,0]).probability(),[0,0.5,0.5])
      self.assertEquals(d([0,0.5,0.5,0]),d([0,0.5,0.5]))
      self.assertEquals(d([0,1,1,1,1]),d([0,0.25,0.25,0.25,0.25]))

      seq = [0.0, 0.2, 0.3, 0.5]
      self.assertEquals(d(seq).probability(),seq)

      self.assertEquals(d(5),d([0.0, 0.2, 0.2, 0.2, 0.2, 0.2]))

      self.assertEquals(d(d(3)),d(3))

      self.assertRaises(TypeError,d,(1,2,3))
      self.assertRaises(ValueError,d,-1)

      self.assertEquals(d([d(4), d(6)]), d(4)+d(6))

    self.assertEquals(LazyDie([Die(4), Die(6)]), LazyDie(4)+LazyDie(6))

  def test_const(self):
    for d in (Die,LazyDie):
      self.assertEquals(d.const(0).probability(),[1.0])
      self.assertEquals(d.const(1).probability(),[0.0,1.0])
      self.assertEquals(d.const(2).probability(),[0.0,0.0,1.0])

  def test_add(self):
    for d in (Die,LazyDie):
      die = d(2)+d(2)
      self.assertEquals(die.probability(),[0.0, 0.0, 0.25, 0.5, 0.25])
      die = d(2)+d(4)
      self.assertEquals(
          die.probability(),
          [0.0, 0.0, 1./2/4, 1./4, 1./4, 1./4, 1./2/4])

      left  = (d(2) + d(10)) + d(20)
      right = d(2) + (d(10) + d(20))
      self.assertEquals(left,right)

      inc = d(8) + d(12)
      dec = d(12) + d(8)
      self.assertEquals(inc, dec)

      a = d(10) + d(10) 
      b = d(12) + d(8)
      self.assertNotEqual(a, b)

      a = d(20)
      b = d(10) + d(10)
      self.assertNotEqual(a, b)

  def test_eq(self):
    for d in (Die,LazyDie):
      self.assertEqual(d(2),d(2))
      self.assertEqual(d(2),d([0,0.5,0.5]))
      self.assertNotEqual(d(2),d(4))
      self.assertNotEqual(d(4),d(2))
      self.assertEqual(d([0.0,1,1]),d([0,0.5,0.5]))
      self.assertEqual(d([0.0,1,1])+d(10),d([0,0.5,0.5])+d(10))

  def test_cmp(self):
    for d in (Die,LazyDie):
      self.assertEqual(d(2).__cmp__(None),cmp(1,None))
      self.assertEqual(d(2).__cmp__(d(2)),0)
      self.assertEqual(d(2).__cmp__(d([0,0.5,0.5])),0)
      self.assertEqual(d(2).__cmp__(d(4)),1)
      self.assertEqual(d(4).__cmp__(d(2)),-1)
      self.assertEqual(d([0.0,1,1]).__cmp__(d([0,0.5,0.5])),0)
      self.assertEqual((d([0.0,1,1])+d(10)).__cmp__(d([0,0.5,0.5])+d(10)),0)

      self.assertEqual(d(2),d(2))
      self.assertNotEqual(d(4),d(2))

  def test_duplicate(self):
    for d in (Die,LazyDie):
      self.assertEqual(d(20).duplicate(0), d.const(0))
      self.assertEqual(d(20).duplicate(1), d(20))
      self.assertEqual(d(20).duplicate(2), d(20)+d(20))
      self.assertEqual(d(8).duplicate(3), d(8)+d(8)+d(8))

      self.assertEquals(d(5).duplicate(20), d(5)+d(5).duplicate(19))

      a = (d(5) + d(10)).duplicate(3)
      b = d(5).duplicate(3) + d(10).duplicate(3)
      self.assertEquals(a,b)

  def test_probability(self):
    for d in (Die,LazyDie):
      self.assertEquals(d(4).probability(),[0.0, 0.25, 0.25, 0.25, 0.25])
      self.assertEquals(d(5),d([0.0, 0.2, 0.2, 0.2, 0.2, 0.2]))

      self.assertEqual(d([0.0,1,1]),d([0,0.5,0.5]))

  def test_probability_reach(self):
    for d in (Die,LazyDie):
      self.assertEquals(d(4).probability_reach(),[1.0,1.0,0.75,0.5,0.25])

  def test_probability_vs(self):
    for d in (Die,LazyDie):
      p = 0.5*0.75 + 0.5*0.5
      self.assertEquals(d(4).probability_vs(d(2)),p)

      d0 = d(4)+d(6)+d(8)+d(8)
      d1 = d(4)+d(6)+d(8)+d(10)+d(8)
      p = d0.probability_vs(d1) + d1.probability_vs(d0) + d0.probability_eq(d1)
      self.assertEquals(round(p,7),1.0)

  def test_probability_eq(self):
    for d in (Die,LazyDie):
      self.assertEquals(d(4).probability_eq(d(4)),0.25)

      p = 0.5*0.25
      self.assertEquals(d(4).probability_eq(d(8)),p)
      self.assertEquals(d(8).probability_eq(d(4)),p)

  def test_roll(self):
    for d in (Die,LazyDie):
      self.assertTrue(d(10).roll() in range(1,11))

      self.assertEquals(d(10).roll(0.09),1)
      self.assertEquals(d(10).roll(0.59),6)

      self.assertEquals(d([0.0,0.2,0.7,0.1]).roll(0),1)
      self.assertEquals(d([0.0,0.2,0.7,0.1]).roll(0.000001),1)
      self.assertEquals(d([0.0,0.2,0.7,0.1]).roll(0.199999),1)
      self.assertEquals(d([0.0,0.2,0.7,0.1]).roll(0.200001),2)
      self.assertEquals(d([0.0,0.2,0.7,0.1]).roll(0.899999),2)
      self.assertEquals(d([0.0,0.2,0.7,0.1]).roll(0.900001),3)
      self.assertEquals(d([0.0,0.2,0.7,0.1]).roll(0.999999),3)

      self.assertRaises(ValueError,d(10).roll,-0.2)
      self.assertRaises(ValueError,d(10).roll,1.0)

  def test_from_string(self):
    for d in (Die,LazyDie):
      self.assertEquals(from_string(d,""),None)
      self.assertEquals(from_string(d," "),None)
      self.assertEquals(from_string(d,"d4"),d(4))
      self.assertEquals(from_string(d,"2d6"),d(6).duplicate(2))
      self.assertEquals(from_string(d," D12"),d(12))
      self.assertEquals(from_string(d,"13  "),d.const(13))
      self.assertEquals(from_string(d,"13 2"),d.const(13)+d.const(2))
      self.assertEquals(from_string(d,"d20 d8 d4"),d(20)+d(8)+d(4))
      self.assertEquals(from_string(d,"d4-d4"),d(4))
      self.assertEquals(
          from_string(d,"d4-d20"),
          d(4) + d(6) + d(8) + d(10) + d(12) + d(20))

      self.assertRaises(DieParseException,from_string,d,"12e3")
      self.assertRaises(DieParseException,from_string,d,"h")
      self.assertRaises(DieParseException,from_string,d,"3d3d2")


      self.assertEquals(
          from_string(d,"5d10",max_dice=5,max_sides=10),
          d(10).duplicate(5))

      self.assertEquals(
          from_string(d,"2d10 3d10",max_dice=5,max_sides=10),
          d(10).duplicate(2) + d(10).duplicate(3))

      self.assertRaises(DieParseException,
          from_string, d, "6d10", max_dice=5, max_sides=10)

      self.assertRaises(DieParseException,
          from_string, d, "2d2 4d3", max_dice=5, max_sides=10)

      self.assertRaises(DieParseException,
          from_string, d, "2d11", max_dice=5, max_sides=10)

      pool = d([7,4,1])
      self.assertEquals(from_string(d,"3p p"),pool.duplicate(3) + pool)
      self.assertEquals(from_string(d,"3p d4"),pool.duplicate(3) + d(4))

  def test_fastsum(self):
    self.assertEquals(fastsum([Die(10)]), Die(10))
    self.assertEquals(fastsum([Die(4),Die(6)]), Die(4)+Die(6))
    self.assertEquals(fastsum([Die(6),Die(4)]), Die(4)+Die(6))

  def test_pool_from_string(self):
    for d in (Die,LazyDie):
      pool = d([7,4,1])
      self.assertEquals(pool_from_string(d,""),[])
      self.assertEquals(pool_from_string(d," "),[])
      self.assertEquals(pool_from_string(d,"0"),[d([1])])
      self.assertEquals(pool_from_string(d,"1"),[pool])
      self.assertEquals(pool_from_string(d,"5"),[pool.duplicate(5)])
      self.assertEquals(pool_from_string(d,"3 4"),[pool.duplicate(3), pool.duplicate(4)])

      self.assertEquals(pool_from_string(d,"5",max_dice=5),[pool.duplicate(5)])

      self.assertRaises(DieParseException, pool_from_string, d, "-1")
      self.assertRaises(DieParseException, pool_from_string, d, "6", max_dice=5)
      self.assertRaises(DieParseException, pool_from_string, d, "4p")
      self.assertRaises(DieParseException, pool_from_string, d, "p")
