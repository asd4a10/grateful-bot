.PHONY: build test test-unit test-integration tdd run clean lint format

# Build Docker image
build:
	docker compose build

# Run all tests
test:
	docker compose -f docker compose.test.yml run --rm test-all

# Run unit tests only
test-unit:
	docker compose -f docker compose.test.yml run --rm test-unit

# Run integration tests only
test-integration:
	docker compose -f docker compose.test.yml run --rm test-integration

# TDD mode - watch and re-run tests
tdd:
	docker compose --profile tdd up tdd

# Run the bot
run:
	docker compose up grateful-bot

# Format code
format:
	docker compose run --rm grateful-bot black src/ tests/

# Lint code
lint:
	docker compose run --rm grateful-bot flake8 src/ tests/

# Type check
typecheck:
	docker compose run --rm grateful-bot mypy src/

# Clean up containers and images
clean:
	docker compose down -v
	docker system prune -f

# Setup development environment
setup: build
	@echo "Docker environment is ready!"
	@echo "Run 'make tdd' to start TDD development"
	@echo "Run 'make test' to run all tests"
	@echo "Run 'make run' to start the bot" 