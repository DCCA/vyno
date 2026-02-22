.PHONY: test live schedule

test:
	PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_*.py' -v

live:
	PYTHONPATH=src ./bin/digest --sources config/sources.yaml --profile config/profile.yaml --db digest-live.db run

schedule:
	PYTHONPATH=src ./bin/digest --sources config/sources.yaml --profile config/profile.yaml --db digest-live.db schedule --time $(or $(TIME),07:00) --timezone $(or $(TZ),America/Sao_Paulo)
