SHELL := /bin/bash

help: ## show this message
	@IFS=$$'\n' ; \
	help_lines=(`fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sed -e 's/\\$$//' | sed -e 's/##/:/'`); \
	printf "%-30s %s\n" "target" "help" ; \
	printf "%-30s %s\n" "------" "----" ; \
	for help_line in $${help_lines[@]}; do \
		IFS=$$':' ; \
		help_split=($$help_line) ; \
		help_command=`echo $${help_split[0]} | sed -e 's/^ *//' -e 's/ *$$//'` ; \
		help_info=`echo $${help_split[2]} | sed -e 's/^ *//' -e 's/ *$$//'` ; \
		printf '\033[36m'; \
		printf "%-30s %s" $$help_command ; \
		printf '\033[0m'; \
		printf "%s\n" $$help_info; \
	done

fix-black: ## automatically fix all black errors
	@poetry run black .

fix-isort: ## automatically fix all isort errors
	@poetry run isort .

lint: lint-isort lint-black lint-pyright lint-flake8 lint-pylint ## run all linters

lint-black: ## run black
	@echo "Running black... If this fails, run 'make fix-black' to resolve."
	@poetry run black . --check --color --diff
	@echo ""

lint-flake8: ## run flake8
	@echo "Running flake8..."
	@poetry run flake8 --config=setup.cfg
	@echo ""

lint-isort: ## run isort
	@echo "Running isort... If this fails, run 'make fix-isort' to resolve."
	@poetry run isort . --check-only
	@echo ""

lint-pylint: ## run pylint
	@echo "Running pylint..."
	@poetry run pylint troposphere tests --rcfile=pyproject.toml
	@echo ""

lint-pyright: ## run pyright
	@echo "Running pyright..."
	@npx pyright --venv-path ./
	@echo ""

run-pre-commit: ## run pre-commit for all files
	@poetry run pre-commit run -a

setup: setup-poetry setup-pre-commit setup-npm ## setup development environment

setup-npm: ## install node dependencies with npm
	@npm ci

setup-poetry: ## setup python virtual environment
	@poetry install \
		--remove-untracked

setup-pre-commit: ## install pre-commit git hooks
	@poetry run pre-commit install

spellcheck: ## run cspell
	@echo "Running cSpell to checking spelling..."
	@npx cspell "**/*" \
		--color \
		--config .vscode/cspell.json \
		--must-find-files \
		--no-progress \
		--relative \
		--show-context
