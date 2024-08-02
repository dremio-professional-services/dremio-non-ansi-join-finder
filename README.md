# Dremio Non-ANSI Join Finder

Dremio Non-ANSI Join Finder is a python-based utility for Dremio Enterprise. 
It enables a user to enter either a SQL statement, or a collection of SQL statements in a JSON format, exported from select * FROM sys.views WHERE ... in Dremio, and it will detect if the SQL contains a non-ansi SQL join e.g. SELECT * FROM a, b rather than SELECT * FROM a INNER JOIN b.

usage: python dremio-non-ansi-join-finder.py [-h] [--sql SQL] [--sql-json-file SQL_JSON_FILE] [--output-file OUTPUT_FILE]
                                      [--error-file ERROR_FILE] [--log-file LOG_FILE]
									  
If not supplied, the defaults for the above parameters are as follows:
OUTPUT_FILE = "./non-ansi-sqls.json"
ERROR_FILE = "./error-sqls.json"
LOG_FILE = "./dremio-non-ansi-join-finder.log"