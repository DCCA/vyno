.PHONY: test live schedule logs bot admin admin-ui admin-ui-prototype

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

bot:
	$(DIGEST_CMD) --sources config/sources.yaml --profile config/profile.yaml --db digest-live.db bot

admin:
	$(DIGEST_CMD) --sources config/sources.yaml --profile config/profile.yaml --db digest-live.db admin --host 127.0.0.1 --port 8787

admin-ui:
	$(DIGEST_CMD) --sources config/sources.yaml --profile config/profile.yaml --db digest-live.db admin-streamlit --host 127.0.0.1 --port 8788

admin-ui-prototype:
	$(DIGEST_CMD) admin-streamlit-prototype --host 127.0.0.1 --port 8790
