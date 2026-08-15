# Checks that the four tools do what they are supposed to.
# Run make_synthetic_db.py first, then:  python test_server.py

import asyncio
import server

passed = 0
failed = 0


def check(name, ok, output=""):
    global passed, failed
    if ok:
        passed = passed + 1
        print("  ok    " + name)
    else:
        failed = failed + 1
        print("  FAIL  " + name + "  got: " + output)


async def main():
    print("list_data_sources")
    out = await server.list_data_sources()
    check("shows the test database", "busfactor_test" in out, out)

    print("list_tables")
    out = await server.list_tables("busfactor_test")
    check("finds people", "people" in out, out)
    check("finds comms_metadata", "comms_metadata" in out, out)

    out = await server.list_tables("database_that_does_not_exist")
    check("bad database name gives an error", out.startswith("Error:"), out)

    print("describe_table")
    out = await server.describe_table("busfactor_test", "people")
    for column in ["id", "name", "role", "dept"]:
        check("shows the " + column + " column", column in out, out)

    print("run_query")
    out = await server.run_query("busfactor_test", "SELECT * FROM people")
    check("gets all 5 people", "5 row(s)" in out, out)

    out = await server.run_query("busfactor_test", "SELECT name FROM people WHERE dept = 'Finance'")
    check("finds the finance people", "Fake Bob" in out and "Fake Elena" in out, out)
    check("leaves out everyone else", "Fake Alice" not in out, out)

    out = await server.run_query("busfactor_test", "SELECT * FROM people", 2)
    check("limit works", "2 row(s)" in out, out)

    print("run_query blocks anything that writes")
    bad_queries = [
        "DROP TABLE people",
        "DELETE FROM people",
        "UPDATE people SET name = 'x'",
        "INSERT INTO people VALUES (6, 'x', 'y', 'z')",
        "SELECT * FROM people; DROP TABLE people",
    ]
    for q in bad_queries:
        out = await server.run_query("busfactor_test", q)
        check("blocks " + q, "only a single read-only SELECT" in out, out)

    print("nothing got deleted by any of that")
    out = await server.run_query("busfactor_test", "SELECT COUNT(*) AS n FROM people")
    check("still 5 people in the table", "\n5" in out, out)

    print("")
    print(str(passed) + " passed, " + str(failed) + " failed")

    if failed > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
