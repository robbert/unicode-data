#!/usr/bin/python

import math#ias bynens
import re
import string
from collections import defaultdict

# http://mathiasbynens.be/notes/javascript-encoding#surrogate-formulae
def highSurrogate(codePoint):
	return int(math.floor((codePoint - 0x10000) / 0x400) + 0xD800)

def lowSurrogate(codePoint):
	return int((codePoint - 0x10000) % 0x400 + 0xDC00)

def codePointToString(codePoint):
	if (codePoint >= 0x41 and codePoint <= 0x5A) or (codePoint >= 0x61 and codePoint <= 0x7A) or (codePoint >= 0x30 and codePoint <= 0x39): # [a-zA-Z0-9]
		string = chr(codePoint)
	elif codePoint <= 0xFF: # http://mathiasbynens.be/notes/javascript-escapes#hexadecimal
		string = '\\x' + '%02X' % codePoint
	elif codePoint <= 0xFFFF: # http://mathiasbynens.be/notes/javascript-escapes#unicode
		string = '\\u' + '%04X' % codePoint
	else: # surrogate pairs
		string = '\\u' + '%04X' % highSurrogate(codePoint) + '\\u' + '%04X' % lowSurrogate(codePoint)
	return string

def hexify(codePoint):
	return '0x' + hex(codePoint)[2:].upper()

def createRange(codePointList):
	bmp = []
	supplementary = defaultdict(list)
	surrogates = []

	for codePoint in codePointList:
		if codePoint >= 0xD800 and codePoint <= 0xDBFF: # code points that are high surrogates go at the end
			surrogates.append(codePoint)
		elif codePoint <= 0xFFFF:
			bmp.append(codePoint)
		else: # supplementary code point
			supplementary[highSurrogate(codePoint)].append(lowSurrogate(codePoint))

	supplementaryDictByLowRanges = defaultdict(list)
	for hi, lo in supplementary.items():
		supplementaryDictByLowRanges[createBMPRange(lo)].append(hi)
	# `supplementaryDictByLowRanges` looks like this:
	# { 'low surrogate range': [list of high surrogates that have this exact low surrogate range] })

	buf = []
	if len(bmp):
		buf.append(createBMPRange(bmp))
	for lo, hi in supplementaryDictByLowRanges.items():
		buf.append(createBMPRange(hi) + lo)
	# individual code points that are high surrogates must go at the end
	if len(surrogates):
		buf.append(createBMPRange(surrogates))

	return '|'.join(buf)

def createBMPRange(r):
	if len(r) == 0:
		return ''

	buf = []
	start = r[0]
	end = r[0]
	predict = start + 1
	r = r[1:]

	counter = 0
	for code in r:
		if predict == code:
			end = code
			predict = code + 1
			continue
		else:
			if start == end:
				buf.append(codePointToString(start))
				counter += 1
			elif end == start + 1:
				buf.append('%s%s' % (codePointToString(start), codePointToString(end)))
				counter += 2
			else:
				buf.append('%s-%s' % (codePointToString(start), codePointToString(end)))
				counter += 2
			start = code
			end = code
			predict = code + 1

	if start == end:
		buf.append(codePointToString(start))
		counter += 1
	elif end == start + 1:
		buf.append('%s%s' % (codePointToString(start), codePointToString(end)))
		counter += 2
	else:
		buf.append('%s-%s' % (codePointToString(start), codePointToString(end)))
		counter += 2

	if counter == 1:
		return ''.join(buf)
	else:
		return '[' + ''.join(buf) + ']'

def parseDatabase(sourceFile, storeAsStrings=False):
	charDict = {}

	with open(sourceFile) as uni:
		flag = False
		first = 0
		for line in uni:
			d = string.split(line.strip(), ';')
			val = int(d[0], 16)
			if d[1][:1] == '<' and d[1][-1:] == '>':
				name = (d[1] + ' ' + d[10]).strip()
				# TODO: get aliases from NameAliases.txt too
				#print(val)
				#print(name)
			else:
				name = d[1]
			#print(name)
			if flag:
				if re.compile('<.+, Last>').match(d[1]):
					# print '%s: u%X' % (d[1], val)
					flag = False
					for t in range(first, val + 1):
						charDict[t] = str(d[2])
				else:
					raise 'Database exception'
			else:
				if re.compile('<.+, First>').match(d[1]):
					# print '%s: u%X' % (d[1], val)
					flag = True
					first = val
				else:
					charDict[val] = str(d[2])

	# http://unicode.org/reports/tr44/#GC_Values_Table
	# http://unicode.org/reports/tr18/#Categories
	categoryDict = defaultdict(list)
	for codePoint in range(0x10FFFF + 1):
		if charDict.get(codePoint) == None:
			categories = ['Any', 'C', 'Cn']
		else:
			tmp = charDict[codePoint]
			categories = ['Any', tmp, tmp[0], 'Assigned']
			if tmp in ['Ll', 'Lu', 'Lt']:
				categories.append('LC')
			if codePoint <= 0x7F:
				categories.append('ASCII')
		if storeAsStrings:
			tmp = codePointToString(codePoint)
		else:
			tmp = codePoint
		for category in categories:
			categoryDict[category].append(tmp)
	return categoryDict

def parseScriptsOrProps(sourceFile, storeAsStrings=False):
	dictionary = defaultdict(list)
	with open(sourceFile) as uni:
		for line in uni:
			if line.startswith('#') or not ' ; ' in line:
				continue
			data = string.split(line.strip(), ';')
			charRange = data[0].replace('..', '-').strip()
			script = data[1].split('#')[0].strip()
			rangeParts = charRange.split('-')
			if len(rangeParts) == 2:
				dictionary[script].extend(range(int(rangeParts[0], 16), int(rangeParts[1], 16) + 1))
			else:
				dictionary[script].append(int(charRange, 16))
	if (storeAsStrings):
		for script in dictionary:
			dictionary[script] = map(codePointToString, dictionary[script])
	return dictionary

def parseBlocks(sourceFile, storeAsStrings=False):
	dictionary = defaultdict(list)
	with open(sourceFile) as uni:
		for line in uni:
			if line.startswith('#') or not '; ' in line:
				continue
			data = string.split(line.strip(), ';')
			charRange = data[0].replace('..', '-').strip()
			script = data[1].split(';')[0].strip()
			rangeParts = charRange.split('-')
			if len(rangeParts) == 2:
				dictionary[script].extend(range(int(rangeParts[0], 16), int(rangeParts[1], 16) + 1))
			else:
				dictionary[script].append(int(charRange, 16))
	if (storeAsStrings):
		for script in dictionary:
			dictionary[script] = map(codePointToString, dictionary[script])
	return dictionary

def writeFile(filename, contents):
		print filename
		with open(filename, 'w') as f:
			f.write(contents)