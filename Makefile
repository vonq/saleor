subtree-setup:
	git remote add -f pkb git@github.com:vonq/pkb.git
	git subtree add --prefix=api/ pkb pkb-saleor

pkb-pull:
	git subtree pull --prefix=api/ pkb pkb-saleor

pkb-push:
	git subtree push --prefix=api/ pkb pkb-saleor
