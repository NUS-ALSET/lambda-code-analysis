from botocore.vendored import requests
#import requests
import json
import time

import ast
from collections import deque

# Collect all statements
def getAllStat(tree):
  stat = {}
  for node in ast.walk(tree):
    if isinstance(node, ast.While):
      stat["While"] = True
    elif isinstance(node, ast.For):
      stat["For"] = True
    elif isinstance(node, ast.Return):
      stat["Return"] = True
    elif isinstance(node, ast.If):
      stat["If"] = True
    #else:
    #  print(node)
    
  return stat


class FuncCallVisitor(ast.NodeVisitor):
    def __init__(self):
        self._name = deque()

    @property
    def name(self):
        #print(self._name)
        return '-'.join(self._name)
      

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


def get_func_calls(tree):
    func_calls = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            callvisitor = FuncCallVisitor()
            callvisitor.visit(node.func)
            func_calls.append(callvisitor.name)
    result = {}
    for item in func_calls: 
      result[item] = True
    #return sorted(list(set(func_calls)))
    return result

  # Collect all imports
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

	#return sorted(list(imports))
  
# Collect all expressions
def getAllExpr(tree):
  expr = []
  for node in ast.walk(tree):
    if isinstance(node, ast.Add):
      expr.append("+")
    if isinstance(node, ast.Eq):
      expr.append("==")
    if isinstance(node, ast.Sub):
      expr.append("-")
    if isinstance(node, ast.Mult):
      expr.append("*")
    if isinstance(node, ast.Div):
      expr.append("/")
    if isinstance(node, ast.Lt):
      expr.append("<")
    if isinstance(node, ast.Gt):
      expr.append(">")
      
  result = {}
  for item in expr: 
    result[item] = True
  return result    
  
  #return sorted(list(set(expr)))
  
def code_features(src):
  tree = ast.parse(src)
  result = {
        "statements":{},
        "functions":{},
        "imports":{},
        "expressions":{}
    }  
  result["imports"] = getAllImports(tree)
  result["expressions"] =getAllExpr(tree)
  result["functions"] = get_func_calls(tree)
  result["statements"] = getAllStat(tree)
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
        

#solution_features(solutions)

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
