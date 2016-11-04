#!/bin/bash

EXTRA_FLAGS="-DPRINT_LITS -DBDEBUG"

pushd ..
make clean

sed -i "s/^\(CFLAGS=-g -O0  -D_LARGEFILE64_SOURCE=1 -DHAVE_HIDDEN -DDEBREACH\).*$/\1 $EXTRA_FLAGS/" Makefile
sed -i "s/^\(SFLAGS=-g -O0  -fPIC -D_LARGEFILE64_SOURCE=1 -DHAVE_HIDDEN -DDEBREACH\).*$/\1 $EXTRA_FLAGS/" Makefile

make
popd
python validation_test.py
