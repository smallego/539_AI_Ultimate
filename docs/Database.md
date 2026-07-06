# Database

The project uses SQLite at:

```text
database/history.db
```

## Existing Runtime Tables

- `draw_history`: historical draw records.
- `prediction_history`: saved recommendation rows.
- `learning_history`: saved learning outcomes and weights JSON.

## Release Candidate Rule

V7.1.3 does not change the database schema.

## Local Development

The database is ignored by Git. Tests are smoke-oriented and should not require a committed SQLite file.
