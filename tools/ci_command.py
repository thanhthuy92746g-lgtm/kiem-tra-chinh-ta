"""Keep a CI command's exit status and expose its failure in GitHub annotations."""
import argparse
import os
import subprocess
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", required=True)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        parser.error("Cần lệnh Python sau --.")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    environment = os.environ.copy()
    environment["PYTHONUTF8"] = "1"
    log = Path(args.log)
    with log.open("w", encoding="utf-8") as output:
        process = subprocess.Popen([sys.executable]+command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   text=True, encoding="utf-8", errors="replace", env=environment)
        for line in process.stdout:
            output.write(line)
            print(line, end="", flush=True)
        status = process.wait()
    if status:
        tail = log.read_text(encoding="utf-8")[-16000:]
        escaped = tail.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
        print("::error title=Command diagnostics::"+escaped)
    return status


if __name__ == "__main__":
    raise SystemExit(main())
