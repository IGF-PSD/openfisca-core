## Install project dependencies.
install:
	@$(call print_help,$@:)
	@pip install --upgrade pip twine wheel
	@pip install --editable ".[dev]" --upgrade

## Uninstall project dependencies.
uninstall:
	@$(call print_help,$@:)
	@pip freeze | grep -v "^-e" | sed "s/@.*//" | xargs pip uninstall -y

## Delete builds and compiled python files.
clean:
	@$(call print_help,$@:)
	@find . -name "*.pyc" | xargs rm -rf
	@rm -rf build
	@rm -rf dist
