"""
 Copyright (C) 2009-2015 Alexandros Kanterakis

 This program is free software; you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation; either version 2 of the License, or
 (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License along
 with this program; if not, write to the Free Software Foundation, Inc.,
 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 http://www.gnu.org/copyleft/gpl.html
"""

import sys, imp, __builtin__
import pypmwclient
import inspect
import glob
import time
import ast
import re
import os

from datetime import datetime

#Check Version. Allow ONLY python 2.6 and 2.7
if sys.version[0:3] not in ["2.6", "2.7"]:
	raise Exception("Invalid Version. PyPedia can be imported only in Python v. 2.6 or v. 2.7")

#Python 2.7 contains a bug in httplib.py
#http://hg.python.org/cpython/raw-file/eb3c9b74884c/Misc/NEWS
#- httplib.HTTPConnection.putheader() now accepts an arbitrary number of values
#  for any header, matching what the documentation has claimed for a while.
if sys.version[0:4] == "2.7 ":
	print "Warning: Python 2.7 has been found. This versions contains a critical bug in httplib.py. Please update to python 2.7.2"

#Change siteDomain to the domain of your local installation of mediawiki
#For example:
siteDomain = "www.pypedia.com"

#Change sitePath to the path of your MediaWiki installation. For example if the mediawiki can
#be accessed through: http://192.168.0.4/PYP/index.php then sitePath should be:
sitePath = "/"

#The temporary directory to store the downloaded code
#tmpDirectory = "pypedia/pypCode/"
tmpDirectory = os.path.join(os.path.expanduser('~'), '.pypedia')
try:
	os.mkdir(tmpDirectory)
except OSError:
	pass # Directory already exists

#The preffix that every dowlnloaded file will have. 
functionPreffix = "pyp_"

#The file that contains the article prefilled text
#prefilled = "pypedia/prefilled.txt"
from prefilled import prefilled_text

sys.path.append(tmpDirectory)

#In case we only want to download code instead of importing it to the namespace, set the following to True
#This is useful when the imported code requires packages that are not available. 
importDumpFunction = False

#Set true to download a new version only if there isn't one already downladed
enable_cache = True

#For debug information
debug = False

#Print warnings
warnings = True

#By default pypedia checks for modification dates before downloading articles from pypedia.com
#If a file has been modified locally an exception is generated. This can be overriden by setting True the force_imports variable
force_imports = False

#The object to manage the connection
site = None

#The before timestamp. If set then the library will download the first revision of the method BEFORE this date.
#The format should be string: "YYYYMMDDHHMMSS"
before_timestamp = None

#This is a list of keywords that have been queried to the wiki but does not exist
#By checking this list before querying the wiki we improve import time
non_existent_keywords = []

#Get username and password of the account in pypedia
#If the file ~/.pyp exists then get the username from this file
pyp_config = os.path.join(os.getenv("HOME"), ".pyp")
if os.path.exists(pyp_config):
	execfile(pyp_config)
else:
	username = "pypediauser"
	password = "pypediauserpw"

#Connect to mediawiki..
def pypedia_connect():
	global site

	print_debug("Connecting to www.pypedia.com..")
	site = pypmwclient.Site(siteDomain, path = sitePath)
	site.login(username, password) # Optional
	print_debug("Done connecting to www.pypedia.com")

reservedWords = ["abs", "all", "and", "any" "as", "assert", "basestring", "bin", "bool", "break", "callable", "chr", "class", "classmethod", "cmp", "compile",
			"complex", "continue", "def", "del", "delattr", "dict", "dir", "divmod", 
			"elif", "else", "enumerate", "eval", "except", "Exception", "exec", "execfile", "file", "filter", "finally", "float", "for", "format",
			"from", "frozenset", "getattr", "global", "globals", "hasattr", "hash", "help", "hex", "id", "if",  
			"import", "in", "input", "int", "is", "isistance", "issubclass", "iter", "lambda", "len", "list", "locals", "long", "map", "max", 
			"memoryview", "min", "next", "not", "object", "oct", "or", "open", "ord", "pass", "pow", "print", "property", "raise", "range", 
			"raw_inpute", "reduce", "reload", "repr", "return", "reversed", "round", "set", "setattr", "slice", "sorted", "staticmethod", "str", 
			"sum", "super", "try", "tuple", "type", "unichr", "unicode", "vars", "while", "with", "xrange", "yield", "zip"];


def print_debug(to_print):
	"""Prints debug information"""

	if debug:
		print "PYPEDIA_DEBUG:", to_print

def print_warning(to_print):
	"""Prints warnings"""

	if warnings:
		print "PYPEDIA WARNING:", to_print

def import_file(filename, level):
	caller_locals = inspect.currentframe(level).f_locals
	caller_globals = inspect.currentframe(level).f_globals

	execfile(filename, caller_locals, caller_globals)

def imported_file_time_diff(filename):
	"""
	Gets the differences in seconds of time between the last time a file was modified and the time it was retrieved from pypedia
	"""
	
	file_content = open(filename).read()

	#Get the date it was retrieved
	local_retrieve_date = re.search(r"Local retrieve date: (.*)", file_content).group(1)
	local_retrieve_time = time.strptime(local_retrieve_date, "%Y-%m-%dT%H:%M:%S%Z") #TODO: Make this universal

	#Get the date when the file was list time edited:
	last_edited = time.localtime(os.path.getmtime(filename))

	difference = datetime.fromtimestamp(time.mktime(last_edited)) - datetime.fromtimestamp(time.mktime(local_retrieve_time))
	return (difference.total_seconds(), local_retrieve_time, last_edited)

def change_local_retrieve_date(filename):
	"""
	Changes the local retrieve date of a file to now
	"""
	file_content = open(filename).read()
	file_content = re.sub(r"Local retrieve date: .*", "Local retrieve date: %s" % (time.strftime("%Y-%m-%dT%H:%M:%S%Z", time.localtime())), file_content)
	open(filename, "w").write(file_content)

def importString(aName, astr, level, redirectedFrom = None):

	#tmpName = "%s%s%s.py" % (tmpDirectory, functionPreffix, aName)
	tmpName = os.path.join(tmpDirectory, functionPreffix + aName + ".py")

	if (not enable_cache) or (not os.path.isfile(tmpName)):
	
		#Does this file exists?
		if os.path.exists(tmpName):
						
			#Check if the file has been edited AFTER it was downloaded from pypedia.com (We allow one second interval)
			difference, local_retrieve_time, last_edited = imported_file_time_diff(tmpName)
			if difference > 1:
				if not force_imports:
					raise Exception("%s cannot be imported because the file %s has been edited locally. Set pypedia.force_imports=True to override.\nLast edit time:%s\nRetrieve time:%s\n" % (aName, tmpName, str(last_edited), str(local_retrieve_time)))
	
		f = open(tmpName, "w")
		f.write(astr.replace("@PYPEDIALOCALRETRIEVETIME@", time.strftime("%Y-%m-%dT%H:%M:%S%Z", time.localtime())))
		f.close()

	#We import ONLY ONE function on the current scope. The imported function.
	#Check documentation if you want to import the whole function tree
	if level == 1:

		#rootFilename = "%s%s_.py" % (tmpDirectory, functionPreffix)
		rootFilename = os.path.join(tmpDirectory, functionPreffix + '_.py')
		#fakeFilename = "%s%s_fake.py" % (tmpDirectory, functionPreffix)
		fakeFilename = os.path.join(tmpDirectory, functionPreffix + '_fake.py')

		f = open(rootFilename, "w")
		f_fake = open(fakeFilename, "w")

		functionName = redirectedFrom if redirectedFrom else aName

		f.write("from %s%s import *\n" % (functionPreffix, functionName));
		f_fake.write("def %s(): pass\n" % (functionName));

		f.close()
		f_fake.close()

		if importDumpFunction:
			import_file(fakeFilename, level)
		else:
			import_file(rootFilename, level)

def removeComments(code):
	asplit = code.split("\n")
	ret = ""

	for line in asplit:
		line.replace("\n", "")
		pos = line.find("#")
		if pos > -1:
			line = line[0:pos]
		ret += line + "\n"

	return ret

def removeConstants(code):
	asplit = code.split("\n")
	ret = ""

	for line in asplit:
		line.replace("\n", "")

		toDelete =  re.findall("\"\"\".*\"\"\"", line)
		toDelete += re.findall("\'[^\']*\'", line)
		toDelete += re.findall("\"[^\"]*\"", line)

		for constant in toDelete:
			line = line.replace(constant, "")

		ret += line + "\n"
	
	return ret

def push(article_name=None, summary=''):
	"""
	If article_name is None, uploads all the articles that have been locally edited
	if article_name is a string: Takes a local version of an article and uploads it on the server (default www.pypedia.com)
	"""
	
	if not article_name:
		#Get all local articles:
		local_filenames = glob.glob(os.path.join(tmpDirectory, functionPreffix + "*.py"))
		
		for local_filename in local_filenames:
			if local_filename.find("/pyp__.py") > -1: continue
			if local_filename.find("/pyp__fake.py") > -1: continue
			
			if imported_file_time_diff(local_filename)[0] > 1:
				to_upload = os.path.split(local_filename)[1][len(functionPreffix):-3]
				print "Local filename: %s has been edited locally." % (local_filename)
				print "Uploading to article: %s" % (to_upload)
				push(to_upload, summary)
				change_local_retrieve_date(local_filename)
				print "..........DONE"
		return
	
	filename = os.path.join(tmpDirectory, functionPreffix + article_name + ".py")
	#does this file exist?
	if not os.path.exists(filename):
		raise Exception("Filename: %s does not exist" % (filename))

	#Read the file
	content = open(filename).read()

	#Remove the import statements
	content = re.sub(r"from pyp_.*\n", "", content)

	#Remove the docstring. Doscstring is constructed automatically
	c_from = content.find('Link: http://www.pypedia.com/index.php/%s' % (article_name))
	c_to = content.find('"""', c_from)
#	code = content[0:c_from-6] + content[c_to+3:]
	code = content[1:c_from-6] + content[c_to+3:-1]
	docstring = content[c_from:c_to]
	
	#From docstring remove the first 5 lines
	docstring = str.join('\n', docstring.split('\n')[5:])

	#Form it as a wiki section
	code = """==Code==
<source lang="py">%s</source>""" % (code)

	if not site:
		pypedia_connect()

	#Get article object
	page = site.Pages[article_name]
	#Save the code
	page.save(code, summary=summary, section=5)
	#Save the documentation
	page.save(docstring, summary=summary, section=1)
	
	#Update the local retriece date
	change_local_retrieve_date(os.path.join(tmpDirectory, functionPreffix + article_name + ".py"))

def add(article_name):
	'''
	Creates a new article
	'''

	global tmpDirectory, functionPreffix

	if not site:
		pypedia_connect()
		
	page = site.Pages[article_name]
	text = page.edit()
	
	#text should be empty
	if text:
		raise Exception("Article %s already exists" % (article_name))

#	with open(prefilled) as prefilled_f:
#		prefilled_text = prefilled_f.read()
	
	#Make substitutions
	text_to_save = prefilled_text.replace("@PYPEDIAUSERNAME@", username).replace("@PYPEDIAARTICLENAME@", article_name).replace("@PYPEDIAARTICLENAMENOUS@", article_name.replace("_", " "))

	#Save the article to pypedia.com	
	page.save(text_to_save)
	print 'Article %s saved' % (article_name)
	print 'Next: '
	print '  Edit the article online: http://www.pypedia.com/index.php/%s' % (article_name)
	print '  Or edit the article locally: %s' % os.path.join((os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), tmpDirectory, functionPreffix + article_name + '.py' )
	print '    To push the changes to pypedia.com run: pypedia.push()'


	#Download and import the article
	import_PYP_article(article_name, 1)

def traverse_nodes(node, level, to_ret):
	'''
	Traverse recursively all nodes staring from node.
	Node is a ast compiled object
	If the node is referred to a function called then stored the function name in the to_ret list
	'''

	#Is this a function call?
	if node.__class__.__name__ == 'Call':
		#Take the first child
		first_child = ast.iter_child_nodes(node).next()

		#Is this a Name node?
		if first_child.__class__.__name__ == 'Name':
			to_ret += [first_child.id]
	
	#Continue recusively for all childs
	for child in ast.iter_child_nodes(node):
		traverse_nodes(child, level+1, to_ret)


def importFunctionsFromCode(code, thisFunctionName, level):
	'''
	Try to import the functions that are included in thisFunctionName
	'''

	#Remove Comments
	#thisCode = removeComments(code)

	#Remove Constants
	#thisCode = removeConstants(thisCode)

	#find all functions that are in code. 
	ret = []

	#This is the regular expression to recognize function calls
	#allFunctions = re.findall('(?<![\.a-zA-Z0-9])[a-zA-Z][a-zA-Z0-9\_]*[ \t]*\(', thisCode)
	#allFunctions = re.findall('pyp_[a-zA-Z0-9\_]*[ \t]*\(', thisCode)

	code_ast = ast.parse(code)
	function_calls = []
	traverse_nodes(code_ast, 1, function_calls)

	for function_call in function_calls:

		if function_call in thisFunctionName:
			continue

		if function_call in reservedWords:
			continue

		included = True
		try:
			a = eval("type(%s).__name__" % function_call)
		except NameError:
			included = False
		
		#TODO. FIX. REMOVE THIS
		included = False

		if (not included) and (function_call not in ret):
			#This Function is not included. Try to include it from wiki
			if import_PYP_article(function_call, level+1):
				ret += [function_call]
	
	return ret

#Checks the title of an article if it belongs to the User category
def is_user_article(wikiTitle):
    s = wikiTitle.split("_")

    if len(s) < 3: return False

    return s[-2] == "user"

def importCodeFromArticle(wikiTitle, wikiArticle, level, redirectedFrom, revision, touched):
	'''
	Imports the code and the documentation from a wiki article.
	'''

	#Make documentation header
	theDocumentation = ""
	theDocumentation += "Link: http://www.pypedia.com/index.php/%s\n" % (wikiTitle)
	theDocumentation += "Local retrieve date: @PYPEDIALOCALRETRIEVETIME@\n"
	theDocumentation += "PyPedia touched date: %s\n" % (touched)
	theDocumentation += "PyPedia revision: %s\n\n" % (revision)

	#Add the documentation from the wiki
	theDocumentation += re.search(r"(==Documentation==.+)==Code==", wikiArticle, re.DOTALL).group(1)

	#Remove from the documentation the Simple Forms part
	to_remove = re.search(r"\<\!-- DO NOT EDIT HERE! AUTOMATICALLY GENERATED --\>.+\<\!-- EDIT HERE\! --\>", theDocumentation, re.DOTALL)
	theDocumentation = theDocumentation.replace(to_remove.group(0), '')

	#Take the code
	theCode = re.search(r"==Code==(.+)\n==Unit Tests==", wikiArticle, re.DOTALL).group(1)

	#Remove the source tags from the code
	theCode = theCode.replace('<source lang="py">', '').replace('</source>', '')

	#Insert the documentation
	theCode = re.sub(r'\)\s*:\s*\n+([ \t]+)(\S)', r'):\n\1"""\n' + theDocumentation + r'\1"""\n\1\2', theCode, 1)
	
	#Import all functions within the article's code
	importedFunctions = importFunctionsFromCode(theCode, [wikiTitle, redirectedFrom], level)

	#Put code from redirection
	if redirectedFrom != None:
		#theCode += "\n" + redirectedFrom + " = " + wikiTitle + "\n"

		#Create redirection python file
		#tmpFile = open("%s%s%s.py" %(tmpDirectory, functionPreffix, redirectedFrom) , "w")
		tmpFile = open(os.path.join(tmpDirectory, functionPreffix + ".py"), "w")
		tmpFile.write("from %s%s import *\n" % (functionPreffix, wikiTitle) )
		tmpFile.write(redirectedFrom + " = " + wikiTitle + "\n")
		tmpFile.close()

	#Insert from/import statements at the beginning of the code
	for function in importedFunctions:
		theCode = "from %s%s import *\n" % (functionPreffix, function) + theCode
	
	#Next, import the code from this article
	importString(wikiTitle, theCode, level, redirectedFrom)
			
#Called from import hook
def import_PYP_article(wikiTitle, level, redirectedFrom = None):

	global non_existent_keywords

	#Have we queried the wiki before for this title?
	if wikiTitle in non_existent_keywords:
		return False

	print_debug("Importing: " + wikiTitle + " level:" + str(level))

	#Check if this is a User_ article
        if is_user_article(wikiTitle):
		print_warning("%s is a User article that may contain harmfull code." % wikiTitle)

	#Is cache enabled?
	if enable_cache:
		#Does the file exist?
		#code_filename = "%s%s%s.py" % (tmpDirectory, functionPreffix, wikiTitle)
		code_filename = os.path.join(tmpDirectory, functionPreffix + ".py")
		if os.path.exists(code_filename) and not redirectedFrom:
			print_debug(wikiTitle + " exists in the cache")
			importString(wikiTitle, None, level, redirectedFrom)
			return True

	#If we are not connected, connect	
	if not site:
		pypedia_connect()

	#Get the article from pypedia	
	page = site.Pages[wikiTitle]
	text = page.edit(start_timestamp = before_timestamp)

	#Get revision data
	revision = page.revision
	touched = time.strftime("%Y-%m-%dT%H:%M:%SZ", page.touched) if type(page.touched).__name__ == "struct_time" else None

	if not len(text):
		print_debug('     ' + wikiTitle + ' does not exist in www.pypedia.com')
		non_existent_keywords += [wikiTitle]
		return False

	#Is it a redirect page?
	redirects = re.findall("\#REDIRECT[ \t]+\[\[[a-zA-Z0-9\_\ ]+\]\]", text)
	if len(redirects) > 0:
		#This is a redirect page. Find the target.
		start = text.find("[[")
		end = text.find("]]")
		newArticle = text[start+2:end].replace(" ", "_")
		print_debug(wikiTitle + " is a redirect to " + newArticle)
		import_PYP_article(newArticle, level, wikiTitle)

	else:
		#Import the article
		importCodeFromArticle(wikiTitle, text, level, redirectedFrom, revision, touched)

	return True

# Replacement for __import__()

#TODO: Replace import_hook function with suitable for Python 2.6
#NOTE: Done by checking level argument
def import_hook(name, globals=None, locals=None, fromlist=None, level=None):

	if name == "pypedia":
		#If we importing pypedia for the second time. Just ignore..
		if fromlist == None: return
		
		for toImport in fromlist:
			#Import this article
			import_PYP_article(toImport, 1)
	
	if level is None:
		return original_import(name, globals, locals, fromlist)
	else:
		return original_import(name, globals, locals, fromlist, level)

#	parent = determine_parent(globals)
#	q, tail = find_head_package(parent, name)
#	m = load_tail(q, tail)
#	if not fromlist:
#		return q
#	if hasattr(m, "__path__"):
#		ensure_fromlist(m, fromlist)
#	return m

def determine_parent(globals):
    if not globals or  not globals.has_key("__name__"):
        return None
    pname = globals['__name__']
    if globals.has_key("__path__"):
        parent = sys.modules[pname]
        assert globals is parent.__dict__
        return parent
    if '.' in pname:
        i = pname.rfind('.')
        pname = pname[:i]
        parent = sys.modules[pname]
        assert parent.__name__ == pname
        return parent
    return None

def find_head_package(parent, name):
    if '.' in name:
        i = name.find('.')
        head = name[:i]
        tail = name[i+1:]
    else:
        head = name
        tail = ""
    if parent:
        qname = "%s.%s" % (parent.__name__, head)
    else:
        qname = head
    q = import_module(head, qname, parent)
    if q: return q, tail
    if parent:
        qname = head
        parent = None
        q = import_module(head, qname, parent)
        if q: return q, tail
    raise ImportError, "No module named " + qname

def load_tail(q, tail):
    m = q
    while tail:
        i = tail.find('.')
        if i < 0: i = len(tail)
        head, tail = tail[:i], tail[i+1:]
        mname = "%s.%s" % (m.__name__, head)
        m = import_module(head, mname, m)
        if not m:
		raise ImportError, "No module named " + mname
    return m

def ensure_fromlist(m, fromlist, recursive=0):
    for sub in fromlist:
        if sub == "*":
            if not recursive:
                try:
                    all = m.__all__
                except AttributeError:
                    pass
                else:
                    ensure_fromlist(m, all, 1)
            continue
        if sub != "*" and not hasattr(m, sub):
            subname = "%s.%s" % (m.__name__, sub)
            submod = import_module(sub, subname, m)
            if not submod:
		raise ImportError, "No module named " + subname

def import_module(partname, fqname, parent):
    try:
        return sys.modules[fqname]
    except KeyError:
        pass
    try:
        fp, pathname, stuff = imp.find_module(partname,
                                              parent and parent.__path__)
    except ImportError:
	return None
    try:
        m = imp.load_module(fqname, fp, pathname, stuff)
    finally:
        if fp: fp.close()
    if parent:
        setattr(parent, partname, m)
    return m


# Replacement for reload()
def reload_hook(module):
    name = module.__name__
    if '.' not in name:
        return import_module(name, name, None)
    i = name.rfind('.')
    pname = name[:i]
    parent = sys.modules[pname]
    return import_module(name[i+1:], name, parent)

# Save the original hooks
original_import = __builtin__.__import__
#original_reload = __builtin__.reload

# Now install our hooks
__builtin__.__import__ = import_hook
#__builtin__.reload = reload_hook

