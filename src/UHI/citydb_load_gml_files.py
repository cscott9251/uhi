from UHI.config import *
import subprocess


CITY_TOOL = CITY_TOOL_DIR / "citydb.bat"

run_args = [
        f"{CITY_TOOL}",
        "import", "citygml",
        "--db-host", f"{PGHOST}",
        "--db-port", f"5432",
        "--db-name", f"{PGCITYDB}",
        "--db-schema", f"citydb",
        "--db-username", f"{PGADMIN}",
        "--db-password", f"{PGADMIN_PASSWORD}",
        f"{str(LOD2_DIR_ORIG)}"
    ]

print(" ".join(run_args))

subprocess.run(run_args, check=True, text=True)