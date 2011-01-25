#! /usr/bin/env python

import sys

open("test.log","a").write("%s\n" % " ".join(sys.argv))
