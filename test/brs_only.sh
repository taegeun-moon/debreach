#!/bin/bash

pushd ..
make clean

sed -i 's/^\(CFLAGS=-g -O0  -D_LARGEFILE64_SOURCE=1 -DHAVE_HIDDEN -DDEBREACH\).*$/\1 -DBRS_ONLY/' Makefile
sed -i 's/^\(SFLAGS=-g -O0  -fPIC -D_LARGEFILE64_SOURCE=1 -DHAVE_HIDDEN -DDEBREACH\).*$/\1 -DBRS_ONLY/' Makefile

make
popd
python validation_test.py -b