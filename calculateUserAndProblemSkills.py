import ast
from collections import defaultdict

################################################################################
# Constructs
#
# 'constructs' code features correspond to various programming constructs, such
# as slicing, list comprehension, keyword argument usage, etc.
# Note that not all constructs are independent from each other and there may
# be some overlap between them. In particular, some constructs are specialized
# versions of broader constructs. For example, there is a general construct
# 'Comprehension' and its specialized versions 'ListComprehension',
# 'SetComprehension', 'DictionaryComprehension' and 'GeneratorExpression'. Thus
# a list comprehension is counted both as a 'Comprehension' construct and as a
# 'ListComprehension' construct. Similarly a multi-target assignment
# (e.g. "a, b = 1, 2") is counted both as an 'Assignment' construct and as a
# 'MultiTargetAssignment' construct.
#
# Currently detected/recognized constructs are:
#
# Assignment                Corresponds to an assignment statement.
#
# MultiTargetAssignment     Corresponds to an assignment statement with
#                           multiple targets.
#                           Example:
#                                       a, b = 1, 2
#                           Also counts as an Assignment construct.
#
# ChainedCompare            Corresponds to a chained sequence of comparison
#                           expressions.
#                           Example:
#                                       1 < x <= y < 10
#
# KeywordArgumentUsage      Corresponds to a function call with a keyword
#                           argument (argname=value syntax).
#                           Example:
#                                       print('abc', end='')
#
# Subscription              Referring to an item (or multiple items) of a
#                           sequence or mapping object.
#                           Example:
#                                       a[1]
#                                       line[4:-2]
#                                       table['abc']
#
# Slicing                   Usage of slicing ( [start?:end?:stride?] ) in
#                           subscription.
#                           Example:
#                                       items[:]
#                                       line[1:-1]
#                                       array[::2]
#
# IfExpression              Usage of an if-expression.
#                           Example:
#                                       a if a > b else b
#
# Comprehension             Corresponds to any usage of list, set or dictionary
#                           comprehension or generator expression.
#
# FilteredComprehension     Corresponds to a comprehension containing one
#                           or more if's.
#                           Example:
#                                       [x for x in xlist if x > 0]
#                           Also counts as a Comprehension construct.
#
# MultilevelComprehension   Corresponds to a comprehension containing two
#                           or more for's.
#                           Examples:
#                                       [(x,y) for x in xlist for y in ylist]
#                                       [x for y in z for x in y]
#                           Also counts as a Comprehension construct.
#
# ListDisplay               Corresponds to a new list object, specified by
#                           either a list of expressions or a comprehension
#                           enclosed in square brackets.
#                           Examples:
#                                       [1, 2, 3]
#                                       [2*x for x in y]
#
# ListComprehension         A specialized form of a ListDisplay construct. Also
#                           counts as a Comprehension construct.
#
# SetDisplay                Corresponds to a new set object, specified by
#                           either a list of expressions or a comprehension
#                           enclosed in curly braces.
#                           Examples:
#                                       {1, 2, 3}
#                                       {x**2 for x in y}
#
# SetComprehension          A specialized form of a SetDisplay construct. Also
#                           counts as a Comprehension construct.
#
# DictionaryDisplay         Corresponds to a possibly empty series of key:datum
#                           pairs (possibly produced through a comprehension)
#                           enclosed in curly braces, defining a new dictionary
#                           object.
#                           Examples:
#                                       {1:'a', 2:'b', 3:'c'}
#                                       {x:bin(x) for x in y}
#
# DictionaryComprehension   A specialized form of a DictionaryDisplay construct.
#                           Also counts as a Comprehension construct.
#
# GeneratorExpression       A comprehension enclosed in parentheses, producing
#                           a new generator object. Also counts as a
#                           Comprehension construct.
#
# FunctionDef               Definition of a function.
#
# ClassDef                  Definition of a class.
#
################################################################################

################################################################################
# Construct tester functions
################################################################################

def MultiTargetAssignment(ast_node):
    '''
    Detects usage of an assignment with multiple targets
    Example:
        a, b = 1, 2
    '''
    return isinstance(ast_node.targets[0], ast.Tuple)

def FilteredComprehension(ast_node):
    '''
    Detects usage of a comprehension construct with 1 or more if's.
    Example:
        [x for x in xlist if x > 0]
    '''
    for c in ast_node.generators:
        if len(c.ifs) > 0:
            return True
    return False

def MultilevelComprehension(ast_node):
    '''
    Detects usage of a comprehension construct with 2 or more for's.
    Example:
        [(x,y) for x in xlist for y in ylist]
    '''
    return len(ast_node.generators) > 1

def ChainedCompare(ast_node):
    '''
    Detects usage of a chained sequence of comparisons.
    Example:
        1 < x < y <= 5
    '''
    return len(ast_node.ops) > 1

def KeywordArgumentUsage(ast_node):
    '''
    Detects usage of a keyword argument in a function call.
    Example:
        print('abc', end='')
        #            ^^^^^^
    '''
    return len(ast_node.keywords) > 0


################################################################################
# End of construct tester functions
################################################################################


comprehension = 'Comprehension', FilteredComprehension, MultilevelComprehension

# A helper function
def makeComprehensionSpec(collection_type):
    return (collection_type + 'Comprehension',
            collection_type + 'Display',
            *comprehension)

# A map defining construct names for listed AST node types and/or checks
# that must be performed on such AST nodes. In the latter case, if a node
# satisfies the test, the name of the test function is used as the detected
# construct name.
construct_def_map = {
    ast.FunctionDef :   ('FunctionDef',),
    ast.ClassDef :      ('ClassDef',),
    ast.IfExp :         ('IfExpression',),
    ast.Assign :        ('Assignment', MultiTargetAssignment ),
    ast.AugAssign :     ('AugmentedAssignment',),
    ast.List :          ('ListDisplay',),
    ast.ListComp :      makeComprehensionSpec('List'),
    ast.Set :           ('SetDisplay',),
    ast.SetComp :       makeComprehensionSpec('Set'),
    ast.Dict :          ('DictionaryDisplay',),
    ast.DictComp :      makeComprehensionSpec('Dictionary'),
    ast.GeneratorExp :  ('GeneratorExpression', *comprehension),
    ast.Compare :       (ChainedCompare,),
    ast.Subscript :     ('Subscription',),
    ast.Slice :         ('Slicing',),
    ast.Call :          (KeywordArgumentUsage,)
}

def getAllConstructs(tree):
    result = defaultdict(int)

    for node in ast.walk(tree):
        if type(node) in construct_def_map:
            for x in construct_def_map[type(node)]:
                if isinstance(x, str):
                    result[x] += 1
                elif x(node):
                    result[x.__name__] += 1

    return dict(result)


################################################################################
# Statements
################################################################################

def countNodesOfGivenTypes(tree, node_types):
    result = defaultdict(int)

    for node in ast.walk(tree):
        if type(node) in node_types:
            result[type(node).__name__] += 1

    return dict(result)

statementNodeTypes = frozenset([ast.While,
                                ast.For,
                                ast.Return,
                                ast.If,
                                ast.Continue,
                                ast.Break,
                                ast.Try,
                                ast.With,
                                ast.Raise,
                                ast.Pass,
                                ast.Assert,
                                ast.Del,
                                ast.Yield])

# Collect all statements
def getAllStatements(tree):
    return countNodesOfGivenTypes(tree, statementNodeTypes)

################################################################################
# Expressions
################################################################################

# NOTE: An implementation of getAllExpr() based on countNodesOfGivenTypes()
# NOTE: is also possible.

def getAllExpr(tree):
  result = defaultdict(int)
  for node in ast.walk(tree):
    if isinstance(node, ast.UnaryOp) or isinstance(node, ast.BinOp) or isinstance(node, ast.BoolOp):
      result[type(node.op).__name__] += 1
    elif isinstance(node, ast.Compare):
      for op in node.ops:
        result[type(op).__name__] += 1

  return dict(result)

################################################################################
# Functions
################################################################################

'''
Get all function calls from a python file
The MIT License (MIT)
Copyright (c) 2016 Suhas S G <jargnar@gmail.com>
'''
from collections import deque


class FuncCallVisitor(ast.NodeVisitor):
    def __init__(self):
        self._name = deque()

    @property
    def name(self):
        #print(self._name)
        return ''.join(self._name) # was ".".join() removing . option


    @name.deleter
    def name(self):
        self._name.clear()

    # Updating to only show obj for ids
    def visit_Name(self, node):
        self._name.appendleft(node.id)


    def visit_Attribute(self, node):
        try:
            self._name.appendleft(node.attr)
            # hacking for demonstration list of functions
            #self._name.appendleft(node.value.id)
            self._name.appendleft("")

            #print(node.value.id)
        except AttributeError:
            self.generic_visit(node)


def getFuncCalls(tree):
    func_calls = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            callvisitor = FuncCallVisitor()
            callvisitor.visit(node.func)
            func_calls.append(callvisitor.name)
    result = defaultdict(int)
    for item in func_calls:
      result[item] += 1
    return dict(result)

################################################################################
# Imports
################################################################################

def getAllImports(a):
    """Gather all imported module names"""
    if not isinstance(a, ast.AST):
        return set()
    imports = set()
    for child in ast.walk(a):
        if type(child) == ast.Import:
            for alias in child.names:
                imports.add(alias.asname if alias.asname != None else alias.name)
        elif type(child) == ast.ImportFrom:
            for alias in child.names: # these are all functions
                imports.add(alias.asname if alias.asname != None else alias.name)


    result = {}
    for item in imports:
        result[item] = True
    return result

################################################################################
# code_features()
################################################################################

def code_features(src):
  tree = ast.parse(src)

  result = {
            "statements":  getAllStatements(tree),
            "functions":   getFuncCalls(tree),
            "imports":     getAllImports(tree),
            "expressions": getAllExpr(tree),
            "constructs" : getAllConstructs(tree)
           }

  return result

# And finally, we want to send back a dictionary of aggregate results rather than just the analysis of each solution.

def solution_features(solutions):

  """
  problemSkills -> ProblemKey -> featureType -> feature -> userKey -> True
  userSkills       -> UserKey -> featureType -> feature -> problemKey -> True

  """

  problemSkills = {}
  userSkills = {}

  for problemKey in solutions.keys():
    for userKey in solutions[problemKey]:
      src = solutions[problemKey][userKey]
      analysis = code_features(src)
      #print(src)
      #print(analysis)
      for featureType in analysis:
        #print(problemKey, userKey, featureType, analysis[featureType])
        for feature in analysis[featureType]:
          #Add the analysis to the problemSkills dictionary.
          if not problemKey in problemSkills:
            problemSkills[problemKey] = {}
          if not featureType in problemSkills[problemKey]:
            problemSkills[problemKey][featureType] = {}
          if not feature in problemSkills[problemKey][featureType]:
            problemSkills[problemKey][featureType][feature] = {}

          # Add userKey true to feature dictionary.
          problemSkills[problemKey][featureType][feature][userKey] = True

          # Add the same data to userSkills
          if not userKey in userSkills:
            userSkills[userKey] = {}
          if not featureType in userSkills[userKey]:
            userSkills[userKey][featureType] = {}
          if not feature in userSkills[userKey][featureType]:
            userSkills[userKey][featureType][feature] = {}

          # Add problemKey true to feature dictionary.
          userSkills[userKey][featureType][feature][problemKey] = True

  return {"problemSkills":problemSkills, "userSkills": userSkills}


import json

# event is a dict
def lambda_handler(event, context):

    if event['httpMethod'] == 'GET':
        dummy['httpMethod'] = 'GET'
    else:
        if event["body"]:
            dummy = json.loads(event["body"])
        else:
            dummy['httpMethod'] = 'POST'

    result = {
        "isBase64Encoded": False,
        "statusCode": 200,
        "headers": {},
        "body": json.dumps(solution_features(dummy))
    }
    return result
