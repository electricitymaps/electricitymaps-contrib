.PHONY: server

publish-gh-pages:
	git subtree split --prefix api/static -b gh-pages
	git push -f origin gh-pages:gh-pages
	git branch -D gh-pages
