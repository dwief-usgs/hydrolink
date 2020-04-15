docs: ## generate Sphinx HTML documentation, including API docs
	rm -rf docs/_build
	rm -f docs/modules.rst
	sphinx-apidoc -o docs/ hydrolink
	$(MAKE) -C docs clean
	$(MAKE) -C docs html