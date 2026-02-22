.PHONY: test live schedule logs

HAS_UV := $(shell command -v uv >/dev/null 2>&1 && echo 1 || echo 0)

ifeq ($(HAS_UV),1)
PYTHON_CMD := uv run python
DIGEST_CMD := uv run digest
else
PYTHON_CMD := PYTHONPATH=src python3
DIGEST_CMD := PYTHONPATH=src ./bin/digest
endif

test:
	$(PYTHON_CMD) -m unittest discover -s tests -p 'test_*.py' -v

live:
	$(DIGEST_CMD) --sources config/sources.yaml --profile config/profile.yaml --db digest-live.db run

schedule:
	$(DIGEST_CMD) --sources config/sources.yaml --profile config/profile.yaml --db digest-live.db schedule --time $(or $(TIME),07:00) --timezone $(or $(TZ),America/Sao_Paulo)

logs:
	tail -f logs/digest.log
