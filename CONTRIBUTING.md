# Contributing

## Branching

- `main`: stable branch
- Feature branches: `feature/<short-topic>`
- Fix branches: `fix/<short-topic>`

## Commit Style

Use clear imperative messages:
- `feat: add api v1 pagination envelope`
- `fix: prevent web login brute-force retries`
- `docs: add production deployment guide`

## Pull Request Checklist

- Code compiles and app starts.
- Tests added/updated for changed behavior.
- No secrets committed.
- Docs updated when behavior/config changed.

## Coding Standards

- Prefer small, focused functions.
- Keep API contracts explicit and versioned.
- Avoid breaking `/api` legacy clients; put new standards in `/api/v1`.
