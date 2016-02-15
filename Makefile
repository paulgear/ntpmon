# This file is part of check_ntpmon - see COPYING.txt for license.

test: pytest datatest

pytest:
	python -m unittest -b test_check_ntpmon

datatest:
	./testdata.sh

push:	pytest
	git push
