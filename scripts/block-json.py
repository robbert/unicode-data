#!/usr/bin/python

from utils import *
import sys

def format(blockName, blockList, version):
	return '[\n\t' + ',\n\t'.join(blockList) + '\n]'

def main(sourceFile, version):
	dictionary = parseBlocks(sourceFile)
	for item in sorted(dictionary.items()):
		block = item[0].replace('_', ' ')
		codePoints = map(str, item[1])
		result = format(block, codePoints, version)
		writeFile(version + '/blocks/' + block.replace(' ', '-') + '-code-points.json', result)

if __name__ == '__main__':
	main(sys.argv[1], sys.argv[2])