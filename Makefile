# Local path to the documented v0.1 bar. Does not talk to GitHub or a Pi.

.PHONY: verify dress clean

verify:
	bash scripts/verify.sh

dress:
	docker build -t lucy-ghost-zero:dress -f Dockerfile .

clean:
	rm -rf .dress .pytest_cache src/lucy_ghost_zero.egg-info
