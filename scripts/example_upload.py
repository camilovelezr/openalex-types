from pathlib import Path
import psycopg
import gzip
import orjson
import tqdm
import logging
from isal import igzip_threaded
import time
from openalex_types.works import Work
import time
import psycopg
import orjson
import tqdm
from concurrent.futures import ThreadPoolExecutor
from psycopg_pool import ConnectionPool
logger = logging.getLogger("openalex-types.works")
logger.setLevel(logging.DEBUG)
data_dir = Path(".").absolute().parent.joinpath("openalex-snapshot", "data")
def get_parent_dirs(s: str) -> list[str]:
    dir_ = data_dir.joinpath(s)
    l = list(dir_.glob("updated_date*"))
    return l
def get_content_gz(parent_dir: str | Path) -> list[str]:
    parent_dir = Path(parent_dir)
    l = list(parent_dir.glob("*.gz"))
    return l

def gz_to_lines(gz_file: str | Path) -> list[dict]:
    with gzip.open(gz_file, "rb") as f:
        lines = f.readlines()
    return lines
work_files = get_content_gz(get_parent_dirs("works")[0])
with igzip_threaded.open(work_files[3], "rb") as f:
    work_lines1 = f.readlines()
wks = work_lines1
pool = ConnectionPool("dbname=db user=user port=5432 host=localhost password=password")

def process_work_item(work_item):
    with pool.connection() as conn:
        try:
            with conn.cursor() as cur:
                try:
                    work_ = Work(**(orjson.loads(work_item)))
                    cur.execute(
                        f"INSERT INTO {work_._sql_table_name} {work_.sql_columns} VALUES {work_.sql_values}")
                    
                    for subtable in work_._sql_subtables:
                        try:
                            attr_ = getattr(work_, subtable)
                            if attr_ is None:
                                continue
                            if isinstance(attr_, list):
                                for a in attr_:
                                    cur.execute(
                                        f"INSERT INTO {a._sql_table_name} {a.sql_columns} VALUES {a.sql_values}")
                            else:
                                cur.execute(
                                    f"INSERT INTO {attr_._sql_table_name} {attr_.sql_columns} VALUES {attr_.sql_values}")
                        except Exception as e:
                            print(f"Error with {subtable}: {e}")
                            raise e
                    
                    conn.commit()
                except Exception as e:
                    print(f"Error with {work_.id}: {e}")
                    raise e
        except Exception as e:
            print(f"Query failed: {e}")

start_time = time.time()

# Use ThreadPoolExecutor for multi-threading
with ThreadPoolExecutor(max_workers=10) as executor:
    list(tqdm.tqdm(executor.map(process_work_item, wks), total=len(wks)))