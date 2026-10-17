"""A real event-loop / background-check smoke test, usable without a display."""
import argparse
from vietspell.gui.smoke import run_smoke


def main():
    p = argparse.ArgumentParser()
    p.add_argument("file")
    p.add_argument("--screenshot")
    p.add_argument("--report")
    p.add_argument("--profile", choices=("HC-ND30", "DANG-HD05"), default="HC-ND30")
    a = p.parse_args()
    return run_smoke(a.file, screenshot=a.screenshot, report_path=a.report, profile=a.profile)


if __name__ == "__main__":
    raise SystemExit(main())
