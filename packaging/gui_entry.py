import argparse

p = argparse.ArgumentParser()
p.add_argument("--smoke-test")
p.add_argument("--profile", choices=("HC-ND30", "DANG-HD05"), default="HC-ND30")
p.add_argument("--report")
a = p.parse_args()
if a.smoke_test:
    from vietspell.gui.smoke import run_smoke
    raise SystemExit(run_smoke(a.smoke_test, report_path=a.report, profile=a.profile))
from vietspell.gui.app import run
raise SystemExit(run())
