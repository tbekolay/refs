#! /usr/bin/env python
#
# Display a summary of the reference types

# Copyright (c) 2007, Peter Corke
#
# All rights reserved.
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * The name of the copyright holder may not be used to endorse or
#	promote products derived from this software without specific prior
#	written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS ``AS IS''
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDERS AND CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF
# THE POSSIBILITY OF SUCH DAMAGE.

import Bibliography
import BibEntry
import BibTeX
import string
import sys
import optparse

## parse switches
usage = '''usage: %prog [options] [bibfiles]

:: Display a summary of the reference types'''
p = optparse.OptionParser(usage)
#p.add_option('--reverse', dest='reverseSort', action='store_true',
#             help='sort into ascending data order (old at top)')
#p.add_option('--resolve', dest='resolve', action='store_true',
#             help='resolve cross reference entries')
#p.set_defaults(reverseSort=False, resolve=False)
(opts, args) = p.parse_args()
globals().update(opts.__dict__)

if len(args) == 0 and sys.stdin.isatty():
	p.print_help()
	sys.exit(0)

## read the input files
bib = BibTeX.BibTeX()
if args:
	for f in args:
		bib.parseFile(f)
else:
	bib.parseFile()

count = {}
urlCount = 0


for be in bib:
	t = be.getRefType()
	if be.getField('Url'):
		urlCount += 1
	if t in count:
		count[t] += 1
	else:
		count[t] = 1

for k in count:
	print "  %15s: %4d" % (k, count[k])

if urlCount > 0:
	print "  %d with URL links" % urlCount
