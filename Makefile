# This file is part of ntpmon - see COPYING.txt for license.
PYTHONPATH=$(PWD)/src

test: pytest datatest

pytest:
	python3 -m unittest -b unit_tests/test_classifier.py unit_tests/test_peers.py

datatest:
	./testdata/testdata.sh

push:
	git push github

clean:
	find . -type f -name '*.pyc' -print0 | xargs --null rm -f
