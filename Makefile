PYTHON ?= python
API_URL ?= http://localhost:8000

.PHONY: install backend frontend test lint typecheck build validate k8s-validate helm-validate demo-record clean

install:
	$(PYTHON) -m pip install -e "backend[test,quality]"
	cd frontend && npm install --no-audit --no-fund

backend:
	PYTHONPATH=backend $(PYTHON) -m uvicorn app.main:app --app-dir backend --reload

frontend:
	cd frontend && npm run dev

test:
	$(PYTHON) -m pytest -q

lint:
	$(PYTHON) -m ruff check backend

typecheck:
	cd frontend && npm run typecheck

build:
	cd frontend && npm run build

validate:
	$(PYTHON) scripts/validate_readme.py

k8s-validate:
	$(PYTHON) scripts/validate_kubernetes.py

helm-validate:
	$(PYTHON) scripts/validate_helm.py

demo-record:
	node scripts/record_demo.mjs

clean:
	$(PYTHON) scripts/reset_demo.py
