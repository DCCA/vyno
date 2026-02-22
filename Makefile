.PHONY: test live schedule logs bot docker-build docker-up docker-down docker-logs docker-ps docker-restart

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

docker-build:
	docker compose build digest-bot

docker-up:
	mkdir -p logs .runtime obsidian-vault
	touch digest-live.db
	docker compose up -d digest-bot

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f digest-bot

docker-ps:
	docker compose ps

docker-restart:
	docker compose restart digest-bot
