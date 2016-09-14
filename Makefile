.PHONY: server

publish-gh-pages:
	git subtree split --prefix static -b gh-pages
	git push -f origin gh-pages:gh-pages
	git branch -D gh-pages
