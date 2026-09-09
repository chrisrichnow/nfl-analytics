"""
Run dbt commands with env vars loaded straight from .env into the subprocess
environment (bypassing the shell) so special characters in the password
survive intact. Usage: python run_dbt.py run
                        python run_dbt.py test
"""

import os
import subprocess
import sys

from dotenv import dotenv_values

env = os.environ.copy()
env.update(dotenv_values(".env"))
env["DBT_PROFILES_DIR"] = os.path.join(os.getcwd(), "dbt_project")

args = sys.argv[1:] or ["run"]
cmd = [os.path.join(".venv", "Scripts", "dbt.exe"), *args, "--project-dir", "dbt_project"]

result = subprocess.run(cmd, env=env)
sys.exit(result.returncode)
