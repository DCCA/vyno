.PHONY: setup test doctor live schedule logs bot web-api web-ui web-ui-build web-screenshots app security-check security-check-extended docker-build docker-up docker-down docker-logs docker-ps docker-restart docker-deploy docker-scheduler-build docker-scheduler-up docker-scheduler-down docker-scheduler-logs docker-scheduler-ps docker-scheduler-restart docker-scheduler-deploy

HAS_UV := $(shell command -v uv >/dev/null 2>&1 && echo 1 || echo 0)

ifeq ($(HAS_UV),1)
PYTHON_CMD := uv run python
DIGEST_CMD := uv run digest
else
PYTHON_CMD := PYTHONPATH=src python3
DIGEST_CMD := PYTHONPATH=src ./bin/digest
endif

setup:
	./scripts/setup.sh

test:
	$(PYTHON_CMD) -m unittest discover -s tests -p 'test_*.py' -v

doctor:
	$(DIGEST_CMD) --sources config/sources.yaml --sources-overlay data/sources.local.yaml --profile config/profile.yaml --profile-overlay data/profile.local.yaml --db digest-live.db doctor

live:
	$(DIGEST_CMD) --sources config/sources.yaml --sources-overlay data/sources.local.yaml --profile config/profile.yaml --profile-overlay data/profile.local.yaml --db digest-live.db run

schedule:
	$(DIGEST_CMD) --sources config/sources.yaml --sources-overlay data/sources.local.yaml --profile config/profile.yaml --profile-overlay data/profile.local.yaml --db digest-live.db schedule --time $(or $(TIME),07:00) --timezone $(or $(TZ),America/Sao_Paulo)

logs:
	tail -f logs/digest.log

bot:
	$(DIGEST_CMD) --sources config/sources.yaml --sources-overlay data/sources.local.yaml --profile config/profile.yaml --profile-overlay data/profile.local.yaml --db digest-live.db bot

web-api:
	$(DIGEST_CMD) --sources config/sources.yaml --sources-overlay data/sources.local.yaml --profile config/profile.yaml --profile-overlay data/profile.local.yaml --db digest-live.db web --host $(or $(HOST),127.0.0.1) --port $(or $(PORT),8787)

web-ui:
	npm --prefix web run dev

web-ui-build:
	npm --prefix web run build

web-screenshots:
	npm --prefix web run screenshot

app:
	./scripts/start-app.sh

security-check:
	./scripts/security-check.sh local

security-check-extended:
	./scripts/security-check.sh extended

docker-build:
	docker compose build digest-bot digest-scheduler

docker-up:
	mkdir -p logs .runtime obsidian-vault
	touch digest-live.db
	docker compose up -d digest-bot digest-scheduler

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f digest-bot

docker-ps:
	docker compose ps

docker-restart:
	docker compose restart digest-bot

docker-deploy:
	mkdir -p logs .runtime obsidian-vault
	touch digest-live.db
	docker compose up -d --build digest-bot digest-scheduler

docker-scheduler-build:
	docker compose build digest-scheduler

docker-scheduler-up:
	mkdir -p logs .runtime obsidian-vault
	touch digest-live.db
	docker compose up -d digest-scheduler

docker-scheduler-down:
	docker compose stop digest-scheduler

docker-scheduler-logs:
	docker compose logs -f digest-scheduler

docker-scheduler-ps:
	docker compose ps digest-scheduler

docker-scheduler-restart:
	docker compose restart digest-scheduler

docker-scheduler-deploy:
	mkdir -p logs .runtime obsidian-vault
	touch digest-live.db
	docker compose up -d --build digest-scheduler
