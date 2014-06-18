#!/usr/bin/python
# Filename: parsers.py

import argparse
import sys

def createparser():
    """Method to parse string"""
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--directory', default='img')
    parser.add_argument('-f', '--file', default='test.json')

    return parser

PARSER = createparser()
NAMESPACE = PARSER.parse_args(sys.argv[1:])

CURRENTPATH = format(NAMESPACE.directory)

#End of parsers.py