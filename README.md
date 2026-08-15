# omniops_db_mcp

An MCP server for querying SQL databases. Add a database to `config.yaml` and
it becomes queryable through the tools below. The same tools work no matter
which database is configured, so supporting a new one means adding a line of
config rather than writing new code.

See `WRITEUP.pdf` for architecture, design decisions and known limitations.

## Tools

| Tool | Arguments | Returns |
|---|---|---|
| `list_data_sources` | none | the databases in config.yaml |
| `list_tables` | `data_source` | table names |
| `describe_table` | `data_source`, `table` | column names and types |
| `run_query` | `data_source`, `sql`, `limit` | query results |

`run_query` accepts a single SELECT statement only. Anything else (INSERT,
UPDATE, DELETE, DROP, or several statements at once) is rejected before it
reaches the database, and the number of rows returned is capped server-side.

## Setup

Requires Python 3.10 or newer.

```bash
pip install -r requirements.txt
python make_synthetic_db.py
```

`make_synthetic_db.py` builds `synthetic.db`, a small database of invented
data used for testing. It contains no real records.

## Running it

```bash
python server.py
```

The server communicates over stdio and waits for a client to connect, so it
will not print anything on its own. That is expected.

## Testing

```bash
python test_server.py
```

Runs 18 checks covering all four tools, error handling, and the query
restrictions. Should report `18 passed, 0 failed`.

To try it by hand:

```bash
npx @modelcontextprotocol/inspector python server.py
```

This opens a browser window. Click List Tools, choose one, fill in the fields
and run it. For `run_query`, use `busfactor_test` as the data source and
`SELECT * FROM people` as the query.

## Connecting it to Claude Desktop

Add this to `claude_desktop_config.json`, found at
`~/Library/Application Support/Claude/` on macOS or `%APPDATA%\Claude\` on
Windows:

```json
{
  "mcpServers": {
    "omniops-db": {
      "command": "python",
      "args": ["/absolute/path/to/server.py"]
    }
  }
}
```

Use the absolute path. Restart Claude Desktop afterwards.

## Adding a database

```yaml
data_sources:
  busfactor_test: "sqlite:///synthetic.db"
  reporting: "postgresql://readonly_user:password@host/dbname"
```

Use a database account with read-only permission. The server blocks writes on
its own, but a read-only account means a bug in that logic still cannot modify
anything.
