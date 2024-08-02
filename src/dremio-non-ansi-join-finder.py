########
# Copyright (C) 2019-2024 Dremio Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
########

import argparse
import json
import logging
import sys

import sqlglot
from sqlglot import parse_one
from sqlglot import exp


def cleanse_sql(sql):
    # change comments from // to -- because parser doesn't accept //
    sql = sql.replace(r'//', '--')
    # remove d and ts before a date or timestamp because parser doesn't accept them
    sql = sql.replace("{d '", "'")
    sql = sql.replace("{ts '", "'")
    sql = sql.replace("'}", "'")
    # Remove use of Postgres Unicode identifier because the parser doesn't like it
    sql = sql.replace("U&", "")
    # remove specification of 'yyyy' when using year function because the parser doesn't like it
    sql = sql.replace("'yyyy'", "")
    # Parser doesn't like Dremio's optional positional parameter in regexp_split so remove it for processing purposes
    # Note: Could alter sqlglot.expressions.RegexpSplit class (line 5776 in expressions.py to handle the extra param)
    sql = sql.replace("'FIRST',", "")
    sql = sql.replace("'LAST',", "")
    sql = sql.replace("'ALL',", "")
    return sql


def main():
    logging.basicConfig(format="%(levelname)s:%(asctime)s:%(message)s", level=logging.INFO)
    if log_file:
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.INFO)
        fh.setFormatter(logging.Formatter("%(levelname)s:%(asctime)s:%(message)s"))
        logging.getLogger().addHandler(fh)

    # open queries.json and filter out unwanted records
    logger.info('Scanning view definitions for non-ansi joins')
    if sys.version_info.major > 2:
        f_open_read = lambda filename: open(filename, "r", encoding='utf-8')
        f_open_write = lambda filename: open(filename, "wt", encoding='utf-8')
    else:
        f_open_read = lambda filename: open(filename, "r")
        f_open_write = lambda filename: open(filename, "wt")

    infile = f_open_read(sql_file)
    nonAnsiSQLFile = f_open_write(output_file)
    errorFile = f_open_write(error_file)
    nonAnsiCount = 0
    parseErrorCount = 0
    sql = ''
    view_id = ''
    try:
        data = [json.loads(line) for line in infile]

        for viewEntry in data:
            try:
                view_id = viewEntry['view_id']
                view_path = viewEntry['path']
                sql = viewEntry['sql_definition']
                cleansed_sql = cleanse_sql(sql)
                ast = parse_one(cleansed_sql)
                joinList = list(ast.find_all(exp.Join))
                containsNonAnsiJoin = False
                for join in joinList:
                    if 'on' not in join.args:
                        containsNonAnsiJoin = True
                        nonAnsiCount = nonAnsiCount + 1
                        break

                if containsNonAnsiJoin:
                    logging.warning("NON-ANSI JOIN: view_id {} with view_path {}".format(view_id, view_path))
                    nonAnsiSQLFile.write(json.dumps(viewEntry) + '\n')
                else:
                    logging.info("PASS (not non-ansi): view_id {} with view_path {}".format(view_id, view_path))
            except Exception as e:
                logging.error("Error parsing view_id: {}. SQL: {}".format(view_id, sql))
                logging.error("Error reason: " + str(e))
                errorFile.write(json.dumps(viewEntry) + '\n')
                parseErrorCount = parseErrorCount + 1
    except Exception as e:
        logging.fatal(sql)
        logging.fatal(e)
    infile.close()
    nonAnsiSQLFile.close()
    errorFile.close()

    logging.info("Num queries with non-ansi join: {}".format(str(nonAnsiCount)))
    logging.info("Num queries that failed to parse: {}".format(str(parseErrorCount)))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Script to find non-ansi joins in SQL text')
    parser.add_argument('--sql', type=str, help='SQL to parse', required=False)
    parser.add_argument('--sql-json-file', type=str, help='Path to SQL file containing SQLs to check', required=False)
    parser.add_argument('--output-file', type=str, help='File containing the SQLs that DO contain non-ansi SQL and its location in Dremio', required=False, default="./non-ansi-sqls.json")
    parser.add_argument('--error-file', type=str, help='File containing SQLs that the program could not parse, need to check these SQLs manually.', required=False, default="./error-sqls.json")
    parser.add_argument('--log-file', type=str, help='Location of log file', required=False, default='./dremio-non-ansi-join-finder.log')

    args = parser.parse_args()
    sql = args.sql
    sql_file = args.sql_json_file
    log_file = args.log_file
    output_file = args.output_file
    error_file = args.error_file

