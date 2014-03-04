#!/usr/bin/python

from utils import *
import sys

def format(categoryName, categoryList, version):
	return '[\n\t' + ',\n\t'.join(categoryList) + '\n]'

def main(sourceFile, version):
	dictionary = parseDatabase(sourceFile)
	for item in sorted(dictionary.items()):
		category = item[0]
		codePoints = map(str, item[1])
		result = format(category, codePoints, version)
		writeFile(version + '/categories/' + category + '-code-points.json', result)

if __name__ == '__main__':
	main(sys.argv[1], sys.argv[2])