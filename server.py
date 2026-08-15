#!/usr/bin/env python3
# MCP server that lets an AI query SQL databases.
# Databases are listed in config.yaml, so adding a new one is just a new line
# there instead of new code.
#
# run it:     python server.py
# test it:    npx @modelcontextprotocol/inspector python server.py

import logging
import sys
import os
import yaml
import sqlparse

from sqlalchemy import create_engine, inspect, text
from mcp.server.fastmcp import FastMCP

# logging has to go to stderr, stdout is used by MCP itself
logging.basicConfig(stream=sys.stderr, level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("omniops_db_mcp")

mcp = FastMCP("omniops_db_mcp")

MAX_ROWS = 200

# load the databases from config.yaml
config_path = os.path.join(os.path.dirname(__file__), "config.yaml")

data_sources = {}
if os.path.exists(config_path):
    with open(config_path) as f:
        config = yaml.safe_load(f)
    if config and "data_sources" in config:
        data_sources = config["data_sources"]

log.info("loaded %d database(s) from config", len(data_sources))

# keep engines here so we don't reconnect every single time
engines = {}


def get_engine(name):
    if name not in data_sources:
        raise ValueError("no database called '" + name + "' in config.yaml")
    if name not in engines:
        engines[name] = create_engine(data_sources[name])
    return engines[name]


def is_select_only(sql):
    # sqlparse splits the string into statements. we only allow one, and it
    # has to be a SELECT. checking sql.startswith("select") is not enough
    # because "SELECT 1; DROP TABLE people" would pass that.
    statements = []
    for s in sqlparse.parse(sql):
        if s.token_first(skip_cm=True):
            statements.append(s)

    if len(statements) != 1:
        return False
    if statements[0].get_type() != "SELECT":
        return False
    return True


@mcp.tool()
async def list_data_sources():
    """List the databases that are set up in config.yaml."""
    log.info("list_data_sources")
    if len(data_sources) == 0:
        return "No databases configured. Add one to config.yaml."

    result = ""
    for name in data_sources:
        result = result + "- " + name + "\n"
    return result.strip()


@mcp.tool()
async def list_tables(data_source: str):
    """List the tables in a database. data_source is a name from list_data_sources."""
    log.info("list_tables on %s", data_source)
    try:
        engine = get_engine(data_source)
        tables = inspect(engine).get_table_names()
    except Exception as e:
        log.error("list_tables failed: %s", e)
        return "Error: " + str(e)

    if len(tables) == 0:
        return "No tables in '" + data_source + "'."

    result = ""
    for t in tables:
        result = result + "- " + t + "\n"
    return result.strip()


@mcp.tool()
async def describe_table(data_source: str, table: str):
    """Show the columns and types of a table. data_source is a name from list_data_sources."""
    log.info("describe_table on %s.%s", data_source, table)
    try:
        engine = get_engine(data_source)
        columns = inspect(engine).get_columns(table)
    except Exception as e:
        log.error("describe_table failed: %s", e)
        return "Error: " + str(e)

    if len(columns) == 0:
        return "No columns found for '" + table + "'."

    result = "# " + table + " (" + data_source + ")\n\n"
    for c in columns:
        result = result + "- " + c["name"] + ": " + str(c["type"]) + "\n"
    return result.strip()


@mcp.tool()
async def run_query(data_source: str, sql: str, limit: int = 25):
    """Run a read-only SELECT query on a database and return the rows.

    Only one SELECT statement is allowed. Anything that writes to the database
    is rejected. limit is the max rows to return, default 25.
    """
    # log the query so there's a record of what was run, but never log the
    # rows that come back, otherwise the log file becomes a copy of the data
    log.info("run_query on %s: %s", data_source, sql)

    if not is_select_only(sql):
        log.warning("blocked a non-select query on %s: %s", data_source, sql)
        return "Error: only a single read-only SELECT statement is allowed."

    if limit > MAX_ROWS:
        limit = MAX_ROWS
    if limit < 1:
        limit = 1

    # wrap the query in another SELECT so the row limit gets applied no matter
    # what the person asking wrote
    clean_sql = sql.strip()
    if clean_sql.endswith(";"):
        clean_sql = clean_sql[:-1]
    wrapped = "SELECT * FROM (" + clean_sql + ") AS t LIMIT " + str(limit)

    try:
        engine = get_engine(data_source)
        rows = []
        with engine.connect() as conn:
            for r in conn.execute(text(wrapped)):
                rows.append(dict(r._mapping))
    except Exception as e:
        log.error("run_query failed on %s: %s", data_source, e)
        return "Error: query failed (" + str(e) + ")"

    log.info("run_query got %d row(s) back", len(rows))

    if len(rows) == 0:
        return "No rows returned."

    # build a markdown table out of the rows
    columns = list(rows[0].keys())

    result = "# " + str(len(rows)) + " row(s) from " + data_source + "\n\n"
    result = result + " | ".join(columns) + "\n"

    dashes = []
    for c in columns:
        dashes.append("---")
    result = result + " | ".join(dashes) + "\n"

    for r in rows:
        values = []
        for c in columns:
            values.append(str(r[c]))
        result = result + " | ".join(values) + "\n"

    return result.strip()


if __name__ == "__main__":
    mcp.run()
