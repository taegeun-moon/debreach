#!/bin/bash

for testcase in testcases/*; do
    arg=$(cat $testcase)
	in_file=${testcase/testcases/input}
	echo "../timeit $arg $in_file"
	../timeit $arg $in_file
	# fuck bash
	zero=0
	if [ $? -ne $zero ]; then
		echo "timeit has non-zero return: $?"
		exit 1
	fi
done
