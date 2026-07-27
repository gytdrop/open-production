.PHONY: demo web-demo test install clean

demo:
	python scripts/run_demo.py --topic "The future of AI in creative industries" --no-confirm

web-demo:
	python scripts/run_web_demo.py --open-browser

demo-interactive:
	python scripts/run_demo.py --topic "The future of AI in creative industries"

test:
	pytest -v

install:
	pip install -e .

clean:
	rm -rf __pycache__ .pytest_cache
	find . -type d -name __pycache__ -exec rm -rf {} +
