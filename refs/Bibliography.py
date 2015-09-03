# Bibliography class
#   - essentially a container for many BibEntry objects
#   - provides methods for reading/writing the bibliography
#   - provides iterators, sorting etc


import string
import BibEntry
import urllib
import urlparse
import os
import os.path
import sys

NoSuchFile = "No such file"

class Bibliography:

	def __init__(self):
		self.keyList = []
		self.abbrevDict = {}

	def open(self, filename):
		if filename == '-':
			self.filename = "stdin"
			return sys.stdin
		urlbits = urlparse.urlparse('~/lib/bib/z.bib')
		if urlbits[0]:
			# path is a URL
			fp = urllib.urlopen(filename)
			self.filename = filename
		else:
			# path is a local file
			path = os.environ['BIBPATH']
			for p in string.split(path, os.pathsep):
				f = os.path.join(p, filename)
				if os.path.isfile(f):
					break
			else:
				raise NoSuchFile

			fp = open(f, "r")
			home = os.path.expanduser('~')
			f2 = os.path.abspath(f)
			common = os.path.commonprefix([home, f2])
			if common:
				self.filename = "~" + f2[len(common):]
			else:
				self.filename = f

			return fp

	def close(self, fp):
		fp.close()

	# resolve all abbreviations found in the value fields of all entries
	def resolveAbbrev(self):
		#print >> sys.stderr, len(self.abbrevDict)
		for be in self:
			for f in be:
				v = be.getField(f)
				if isinstance(v,str):
					if v in self.abbrevDict:
						if self.abbrevDict[v]:
							be.setField(f, self.abbrevDict[v])

	def insertEntry(self, be, ignore=False):
		#print >> sys.stderr, "inserting key ", be.getKey()
		# should check to see if be is of BibEntry type
		key = be.getKey()
		if key in [x.key for x in self.keyList]:
			if not ignore:
				print >> sys.stderr, "key %s already in dictionary" % (key)
			return False
		self.keyList.append(be)
		return True

	def insertAbbrev(self, abbrev, value):
		#print >> sys.stderr, "inserting abbrev ", abbrev
		if abbrev in self.abbrevDict:
			#print >> sys.stderr, "abbrev %s already in list" % (abbrev)
			return False
		self.abbrevDict[abbrev] = value
		#be.brief()
		return True

	def __repr__(self):
		print >> sys.stderr

	def brief(self):
		for be in self:
			be.brief()

	def getFilename(self):
		return self.filename

	def getAbbrevs(self):
		return self.abbrevDict


	def display(self):
		for be in self:
			be.display()
			print >> sys.stderr

	def __contains__(self, key):
		return key in [x.key for x in self.keyList]

	def __getitem__(self, i):
		if type(i) is str:
			index = [x.key for x in self.keyList].index(i)
			return self.keyList[index]
		elif type(i) is int:
			return self.keyList[i]
		else:
			raise

	def __len__(self):
		return len(self.keyList)


	def sort(self, sortfunc):
		# turn the dictionary of entries into a list so we can sort it
		self.keyList.sort(sortfunc)


	# return list of all bibentry's that match the search spec
	def search(self, key, str, type="all", caseSens=0):
		if str == '*':
			return self.keyList

		result = []
		if string.lower(type) == "all":
			for be in self:
				if be.search(key, str, caseSens):
					result.append(be)
		else:
			for be in self:
				if be.isRefType(type) and be.search(key, str, caseSens):
					result.append(be)
		return result
