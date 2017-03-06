# This file is part of ntpmon - see COPYING.txt for license.

test: pytest datatest

pytest:
	python3 -m unittest -b unit_tests/test_classifier.py unit_tests/test_peers.py

datatest:
	./testdata.sh

push:
	git push github
	git push launchpad

clean:
	find . -type f -name '*.pyc' -print0 | xargs --null rm -f
