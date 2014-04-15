from django.test import TestCase

from doc import docfrom, inheritdoc

class TestDoc(TestCase):
  def test_docfrom(self):
    class A(object):
      def fun(self):
        """docfrom A fun"""
        return 0

    class B(object):
      @docfrom(A.fun)
      def otherfun(self):
        return 1

    self.assertEquals(B.otherfun.__doc__, "docfrom A fun")

  def test_inheritdoc(self):
    class A(object):
      def fun(self):
        """inheritdoc A fun"""
        return 0

    class B(object):
      @inheritdoc(A)
      def fun(self):
        return 1

    self.assertEquals(B.fun.__doc__, "inheritdoc A fun")
