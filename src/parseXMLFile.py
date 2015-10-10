#!/usr/bin/env python
__author__ = 'NHS'

import sys
from StringIO import StringIO
from os import listdir,path
from os.path import isfile, join
from lxml import etree


if __name__ == '__main__':
    if len(sys.argv)==3 and sys.argv[1] == 'parser':
        parser = etree.XMLParser(ns_clean=True, recover=True)
        for f in listdir(sys.argv[2]):
            if isfile(join(sys.argv[2],f)):
                file_name = path.splitext(f)[0]
                file_ext = path.splitext(f)[1]
                if file_ext == '':
                    f_read = open(join(sys.argv[2],f), 'r')
                    data = f_read.read()
                    data = '<DOCXML>'+data+'</DOCXML>'
                    tree = etree.parse(StringIO(data), parser)
                    if len(parser.error_log) == 0:
                        print("Parse "+file_name+" OK")
                    else:
                        print('Erreurs '+file_name+"!")
                        errors = parser.error_log
                        print(len(errors))
                        for error in errors:
                            print(error.message)
                    f_read.close()
    else:
        print('Erreur!')

