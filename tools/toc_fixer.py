import argparse
import logging
import os
import re
import shutil
import sqlite3

logger = logging.getLogger(__name__)
PATH_TO_INDEX_FILE = "Contents/Resources"
DOCSET_INDEX_FILE = "docSet.dsidx"
DOCSET_INDEX_TABLE = "searchIndex"
LOG_FILE = "toc_fixer.log"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="toc-fixer")
    parser.add_argument("docset", help="path to root of docset to fix")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def setup_logging():
    handler = logging.FileHandler(LOG_FILE, mode="w")  # create a new log file each time
    logging.getLogger().addHandler(handler)
    logging.getLogger().setLevel(logging.INFO)


def main():
    args = parse_args()
    setup_logging()

    idx_file = f"{args.docset}/{PATH_TO_INDEX_FILE}/{DOCSET_INDEX_FILE}"
    backup_idx = f"{idx_file}.backup"
    if not args.dry_run and not os.path.exists(backup_idx):
        logger.info(f"backing up index file to {backup_idx}")
        shutil.copy(idx_file, backup_idx)

    conn = sqlite3.connect(idx_file)
    cursor = conn.cursor()

    cursor.execute(f"select id,path from {DOCSET_INDEX_TABLE}")
    rows = cursor.fetchall()

    for row in rows:
        row_id, path = row
        if m := re.match("^<.*>(.*)", path):
            new_path = m.group(1)
            logger.info(f"Rewriting {path} to {new_path}")
            if not args.dry_run:
                cursor.execute(f"update {DOCSET_INDEX_TABLE} set path=? where id=?", (new_path, row_id))

    if not args.dry_run:
        conn.commit()

    print(f"All done!  If everything looks good, please delete the backup file at {backup_idx}")


if __name__ == "__main__":
    main()
