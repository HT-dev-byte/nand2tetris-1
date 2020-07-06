from tokenizer import JackTokenizer
from keywords import *
from grammar import *
import sys

"""
New Compilation Engine
"""
class Engine:
  def __init__(self, input_file):
    self.i = 0
    self.jt = JackTokenizer(input_file, False)
    self.file = open(self.xml_file(input_file), "w")

  def xml_file(self, input_file):
    return input_file + ".xml"

  """ Throughout the compilation engine, we work using atoms"""
  def atom(self):
    token = self.jt.tokenType()
    return Atom(token.value)

  def compileClass(self):
    self.compile(CLASS)

  def advance(self):
    self.jt.advance()

  def ZeroOrMany(self, grammarList, matchOnly):
    # print("ZOM called")
    ret = self.compile(grammarList[0], matchOnly)
    if matchOnly:
      return ret
    elif ret:
      # We now expect the whole of it
      for e in grammarList:
        self.compile(e)
      # We try for another list after this
      self.ZeroOrMany(grammarList, False)
      return True
    else:
      return False

  def write(self, line, end = "\n"):
    self.file.write(self.i*" " +  line + end)

  def MatchDict(self, dictionary, matchOnly):
    # Easy way out
    xml_rows_for_lookup_terms = [self.jt.xml_row()]
    lookup_keys = (self.atom(),)
    # How much to lookahead
    keys = list(dictionary.keys())
    lookahead = len(keys[0])

    # We don't have to move the cursor for LL0 grammar
    if matchOnly:
      assert(lookahead == 1)
      return lookup_keys in dictionary

    for _ in range(lookahead-1):
      self.advance()
      xml_rows_for_lookup_terms += [self.jt.xml_row()]
      lookup_keys = lookup_keys + (self.atom(),)

    if not lookup_keys in dictionary:
      return False

    grammar = el = dictionary[lookup_keys]

    # We must open this before we compile the remainder
    if isinstance(grammar, Element):
      self.open(el)
      grammar = grammar.grammar

    # Now we put the first X terms from the conditional
    for line in xml_rows_for_lookup_terms:
      self.write(line, end="")

    self.advance()
    for e in grammar:
      self.compile(e)

    if isinstance(el, Element):
      self.close(el)

    return True

  def ZeroOrOne(self, grammarTuple, matchOnly):
    ret = self.compile(grammarTuple[0], True)
    if matchOnly:
      return ret
    elif ret:
      for e in grammarTuple:
        self.compile(e)
      return True
    else:
      return None

  """ Has to MATCH """
  def MatchAtom(self, atom, matchOnly):
    expected = atom
    current = self.atom()
    # We use in here to accomodate for bitmasks
    match = current in expected
    if matchOnly:
      return match
    elif match:
      self.write(self.jt.xml_row(), end="")
      self.advance()
      return True
    else:
      # print("%s != %s" % (current, expected))
      return False

  def open(self, el):
    self.write("<%s>" % el.name)
    self.i+=2

  def close(self, el):
    self.i-=2
    self.write("</%s>" % el.name)

  """
  If you set matchOnly = true, the cursor will not move forward
  If it is forced to move forward (LL1 grammar for eg,) it will raise an error instead
  """
  def compile(self, thing, matchOnly = False):
    if isinstance(thing, Element):
      ret = self.compile(thing.grammar[0], True)
      if (matchOnly == False and ret) or thing.empty:
        self.open(thing)
        for e in thing.grammar:
          ret = self.compile(e)
        self.close(thing)
      return ret
    elif callable(thing):
      grammar = thing()
      return self.compile(grammar, matchOnly)
    else:
      grammar = thing
      grammarType = type(grammar)

      if grammarType == list:
        return self.ZeroOrMany(grammar, matchOnly)
      elif grammarType == dict:
        return self.MatchDict(grammar, matchOnly)
      elif grammarType == tuple:
        return self.ZeroOrOne(grammar, matchOnly)
      elif grammarType == Atom:
        return self.MatchAtom(grammar, matchOnly)
      else:
        raise Exception("Should not have reached here")
