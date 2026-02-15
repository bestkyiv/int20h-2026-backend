# Test Suite Documentation

This directory contains the comprehensive test suite for the int20h2026-backend application.

## Test Organization

Tests are organized by layer following Clean Architecture principles:

```
tests/
├── unit/                    # Unit tests (fast, isolated)
│   ├── domain/             # Domain model validation tests
│   │   └── test_validation.py
│   ├── db/                 # Database model and constraint tests
│   │   └── test_constraints.py
│   └── api/                # API layer tests
│       └── test_error_handlers.py
├── api/                    # Full-stack API endpoint tests
│   ├── test_endpoints.py
│   └── test_form_validation.py
├── integration/            # Integration and workflow tests
│   ├── test_teams.py
│   └── test_workflow.py
├── builders.py             # Test data builders (FormBuilder)
└── conftest.py            # Shared fixtures and configuration
```

## Running Tests

### Run All Tests

```bash
pytest
```

### Run Specific Test Suites

```bash
# Unit tests only (fastest)
pytest -m unit

# Integration tests
pytest -m integration

# Database tests
pytest -m db

# API tests
pytest -m api

# Slow tests (concurrency, bulk operations)
pytest -m slow
```

### Run Specific Test Files

```bash
# Domain validation tests
pytest tests/unit/domain/test_validation.py

# Database constraint tests
pytest tests/unit/db/test_constraints.py

# Team workflow tests
pytest tests/integration/test_teams.py

# All API endpoint tests
pytest tests/api/
```

### Run Specific Test Functions

```bash
# Run single test
pytest tests/unit/domain/test_validation.py::test_full_name_length_boundaries

# Run tests matching pattern
pytest -k "test_email"
```

### Run with Coverage

```bash
# Generate coverage report
pytest --cov=src --cov-report=html --cov-report=term-missing

# View HTML report
open htmlcov/index.html  # macOS/Linux
start htmlcov/index.html  # Windows

# Enforce minimum coverage
pytest --cov=src --cov-fail-under=90
```

### Run with Verbose Output

```bash
# Show test names and results
pytest -v

# Show full output (including print statements)
pytest -s

# Combination
pytest -vs
```

## Test Coverage

### Current Test Count

- **Total Tests**: ~100+ tests (up from 9)
- **Unit Tests**: ~70 tests
  - Domain validation: ~40 tests
  - Database constraints: ~20 tests
  - Error handlers: ~10 tests
- **API Tests**: ~20 tests
- **Integration Tests**: ~15 tests

### Coverage Goals

- **Target**: 90% line coverage, 85% branch coverage
- **Critical Paths**: 100% coverage for domain validation, database constraints
- **Business Logic**: Complete coverage of team creation/joining flows

## Test Patterns and Conventions

### Using Test Data Builders

The `FormBuilder` class provides a fluent interface for creating test data:

```python
from tests.builders import FormBuilder

# Simple usage
payload = FormBuilder().with_email("test@example.com").build()

# Student with team
payload = (
    FormBuilder()
    .with_email("student@example.com")
    .as_student(university_id=1, study_year=3)
    .with_team("TeamName", is_leader=True)
    .build()
)

# Job seeker
payload = (
    FormBuilder()
    .seeking_job(
        cv_url="https://example.com/cv.pdf",
        linkedin_url="https://linkedin.com/in/user",
        work_consent=True
    )
    .build()
)

# Test invalid data
payload = (
    FormBuilder()
    .with_full_name("A" * 101)  # Too long
    .build()
)
```

### Parametrized Tests

Use `pytest.mark.parametrize` for systematic boundary testing:

```python
@pytest.mark.parametrize(
    "full_name,should_pass",
    [
        ("AB", True),        # Min length
        ("A", False),        # Below min
        ("A" * 100, True),   # Max length
        ("A" * 101, False),  # Above max
    ],
)
def test_full_name_boundaries(full_name, should_pass):
    builder = FormBuilder().with_full_name(full_name)
    if should_pass:
        form = Form(**builder.build())
        assert form.full_name == full_name
    else:
        with pytest.raises(ValidationError):
            Form(**builder.build())
```

### Async Test Pattern

All API and database tests are async:

```python
@pytest.mark.asyncio
async def test_example(client: AsyncClient, session: AsyncSession):
    # Use await for async operations
    response = await client.post("/endpoint", json=payload)
    assert response.status_code == 200
```

### Database Test Pattern

Use factories from `conftest.py`:

```python
@pytest.mark.asyncio
async def test_with_db(session: AsyncSession, category_factory, university_factory):
    # Create test data
    category = await category_factory(session, name="Backend")
    uni = await university_factory(session, name="KPI", city="Kyiv")

    # Test logic...
```

### Error Message Testing

Verify Ukrainian error messages:

```python
@pytest.mark.asyncio
async def test_error_message(client: AsyncClient):
    response = await client.post("/form/", json=invalid_payload)
    assert response.status_code == 400

    error = response.json()
    # Check for Ukrainian text
    assert "університет" in error["detail"].lower()
    assert "знайдено" in error["detail"].lower()
```

## Test Categories

### Domain Validation Tests (`tests/unit/domain/`)

Tests all field boundaries and cross-field validation rules:

- String length boundaries (min/max)
- Enum value validation
- Phone number normalization
- Email format validation
- Cross-field constraints (cv requires work_consent, etc.)
- Personal data consent validation
- String stripping behavior

**Key Tests**:

- `test_full_name_length_boundaries`: Min/max length validation
- `test_wants_job_requires_cv`: Cross-field validation
- `test_cv_without_work_consent_fails`: Business rule enforcement

### Database Constraint Tests (`tests/unit/db/`)

Tests database-level integrity:

- Unique constraints (email, telegram, university name, category name)
- Composite unique constraints (team_name + category_id)
- Foreign key constraints
- Nullability rules
- Default values
- Cascade behavior

**Key Tests**:

- `test_participant_email_unique_constraint`: Email uniqueness
- `test_team_composite_unique_constraint`: Team name uniqueness per category
- `test_delete_team_participants_remain`: Cascade behavior

### API Validation Tests (`tests/api/`)

Tests API endpoint validation and error handling:

- Missing required fields
- Invalid field formats
- Foreign key validation (university_id, category_id)
- Duplicate detection (email, telegram)
- Team creation/joining rules
- Error message delivery

**Key Tests**:

- `test_submit_form_nonexistent_university_id`: FK validation
- `test_submit_form_duplicate_email`: Duplicate detection
- `test_submit_form_has_team_without_team_name`: Business rule validation

### API Endpoint Tests (`tests/api/test_endpoints.py`)

Tests GET endpoints and response structure:

- Skills endpoint
- Categories endpoint
- Universities endpoint
- Response schema validation
- Ordering verification
- Empty database handling

**Key Tests**:

- `test_get_categories_ordering`: Verify alphabetical ordering
- `test_get_unis_response_schema`: Schema validation

### Team Integration Tests (`tests/integration/`)

Tests team workflows and concurrency:

- Team creation as leader
- Joining existing teams
- Multiple members joining
- Same team name in different categories
- Concurrent team creation
- Race condition handling

**Key Tests**:

- `test_create_team_as_leader`: Team creation workflow
- `test_multiple_members_join_same_team`: Multi-member teams
- `test_concurrent_team_creation_same_name_category`: Concurrency handling

### Error Handler Tests (`tests/unit/api/test_error_handlers.py`)

Tests custom error handlers and messages:

- Ukrainian error message delivery
- Validation error formatting
- HTTP exception formatting
- Field-specific error messages
- Message cleanup (prefix removal)

**Key Tests**:

- `test_missing_required_field_returns_ukrainian_message`: Localization
- `test_validation_error_response_format`: Response structure

## Test Fixtures

### Common Fixtures (from `conftest.py`)

- `client`: Async HTTP client for API testing
- `session`: Async database session (in-memory SQLite)
- `category_factory`: Creates test categories
- `university_factory`: Creates test universities
- `team_factory`: Creates test teams

### Custom Fixtures

Create test-specific fixtures as needed:

```python
@pytest.fixture
async def participant_with_team(session, category_factory, team_factory):
    """Pre-created participant with team for testing."""
    category = await category_factory(session)
    team = await team_factory(session, category_id=category.id)
    # ... create participant
    return participant
```

## Debugging Tests

### Show Print Statements

```bash
pytest -s
```

### Show Full Traceback

```bash
pytest --tb=long
```

### Run Single Test in Debug Mode

```bash
pytest -s -v tests/unit/domain/test_validation.py::test_full_name_length_boundaries
```

### Use Python Debugger

```python
def test_something():
    import pdb; pdb.set_trace()
    # Test code...
```

## Continuous Integration

Tests are designed to run in CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: |
    pytest --cov=src --cov-report=xml --cov-fail-under=90

- name: Upload coverage
  uses: codecov/codecov-action@v3
```

## Writing New Tests

### Checklist for New Features

When implementing a new feature, ensure tests cover:

1. **Domain Layer**:
   - [ ] Field validation boundaries
   - [ ] Cross-field validation rules
   - [ ] Edge cases and null handling

2. **Database Layer**:
   - [ ] Unique constraints
   - [ ] Foreign key constraints
   - [ ] Default values

3. **API Layer**:
   - [ ] Happy path (200 response)
   - [ ] Invalid inputs (422 errors)
   - [ ] Business rule violations (400 errors)
   - [ ] Ukrainian error messages

4. **Integration**:
   - [ ] End-to-end workflow
   - [ ] Multi-step scenarios
   - [ ] Concurrency considerations

### Test Naming Conventions

- Test files: `test_<feature>.py`
- Test functions: `test_<what>_<condition>_<expected_result>`
- Examples:
  - `test_email_validation` (general)
  - `test_duplicate_email_returns_400` (specific)
  - `test_team_creation_as_leader_succeeds` (workflow)

### Documentation in Tests

- Use descriptive docstrings for test functions
- Comment complex test logic
- Reference business requirements where applicable

```python
def test_team_name_unique_per_category():
    """Team names must be unique within a category but can repeat across categories.

    Business requirement: Teams compete within categories, so same name
    is allowed in different categories (Backend vs Frontend).
    """
    # Test implementation...
```

## Troubleshooting

### Common Issues

**Import errors**: Ensure `pythonpath = src` in `pytest.ini`

**Async errors**: Use `@pytest.mark.asyncio` for async test functions

**Fixture not found**: Check `conftest.py` and fixture scope

**Database locked**: Tests use in-memory SQLite; ensure no lingering connections

**Test isolation**: Each test gets fresh database session; check factory implementations

## Additional Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [SQLModel Testing](https://sqlmodel.tiangolo.com/tutorial/fastapi/tests/)
