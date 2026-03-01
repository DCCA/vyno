.PHONY: test doctor live schedule logs bot web-api web-ui web-ui-build app docker-build docker-up docker-down docker-logs docker-ps docker-restart

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

doctor:
	$(DIGEST_CMD) --sources config/sources.yaml --sources-overlay data/sources.local.yaml --profile config/profile.yaml --profile-overlay data/profile.local.yaml --db digest-live.db doctor

live:
	$(DIGEST_CMD) --sources config/sources.yaml --profile config/profile.yaml --db digest-live.db run

schedule:
	$(DIGEST_CMD) --sources config/sources.yaml --profile config/profile.yaml --db digest-live.db schedule --time $(or $(TIME),07:00) --timezone $(or $(TZ),America/Sao_Paulo)

logs:
	tail -f logs/digest.log

bot:
	$(DIGEST_CMD) --sources config/sources.yaml --profile config/profile.yaml --db digest-live.db bot

web-api:
	$(DIGEST_CMD) --sources config/sources.yaml --sources-overlay data/sources.local.yaml --profile config/profile.yaml --profile-overlay data/profile.local.yaml --db digest-live.db web --host $(or $(HOST),127.0.0.1) --port $(or $(PORT),8787)

web-ui:
	npm --prefix web run dev

web-ui-build:
	npm --prefix web run build

app:
	./scripts/start-app.sh

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
