#!/usr/bin/python

from utils import *
import sys

def format(propName, propList, version):
	return '[\n\t' + ',\n\t'.join(propList) + '\n]'

def main(sourceFile, version):
	dictionary = parseScriptsOrProps(sourceFile)
	for item in sorted(dictionary.items()):
		prop = item[0]
		codePoints = map(str, item[1])
		result = format(prop, codePoints, version)
		writeFile(version + '/properties/' + prop + '-code-points.json', result)

if __name__ == '__main__':
	main(sys.argv[1], sys.argv[2])