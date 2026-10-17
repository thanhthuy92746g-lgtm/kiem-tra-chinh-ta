import argparse
import importlib.metadata
import shutil
import subprocess
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Build and verify VietSpell ONEDIR on Windows x64.")
    parser.add_argument("--allow-demo", action="store_true", help="Chỉ dùng để thử đóng gói mô hình mẫu.")
    args = parser.parse_args()
    if sys.platform != "win32" or sys.maxsize <= 2**32:
        raise SystemExit("Cần chạy bằng Python 64-bit trên Windows để tạo và kiểm tra bản .exe.")
    root = Path(__file__).resolve().parents[1]
    for name in ("ngram.sqlite", "syllables.txt", "whitelist.txt"):
        if not (root / "data" / name).is_file():
            raise SystemExit("Thiếu data/"+name+"; hãy chuẩn bị mô hình trước.")
    from vietspell.core.ngram import NgramModel
    with NgramModel(root / "data/ngram.sqlite") as model:
        quality = model.meta.get("quality")
        if quality != "corpus" and not args.allow_demo:
            raise SystemExit("Mô hình không phải ngữ liệu thật; không tạo nhầm bộ cài mẫu. Chỉ CI thử nghiệm mới dùng --allow-demo.")
    subprocess.run([sys.executable, "-m", "PyInstaller", "--noconfirm", "packaging/vietspell.spec"], cwd=root, check=True)
    target = root / "dist/VietSpell"
    (target / "data").mkdir(exist_ok=True)
    for name in ("ngram.sqlite", "syllables.txt", "whitelist.txt"):
        shutil.copy2(root / "data" / name, target / "data" / name)
    for name in ("MODEL-CARD.md", "model-provenance.json", "model-validation.json", "evaluation-wiki.json", "evaluation-opus.json", "evaluation-wiki-strict.json", "evaluation-opus-strict.json"):
        if (root / "data" / name).is_file():
            shutil.copy2(root / "data" / name, target / "data" / name)
    for source, dest in (("docs/USER-GUIDE.vi.md", "HUONG-DAN.md"), ("LICENSE.txt", "LICENSE.txt"), ("THIRD-PARTY-NOTICES.md", "THIRD-PARTY-NOTICES.md")):
        shutil.copy2(root / source, target / dest)
    licenses = target / "licenses"
    licenses.mkdir(exist_ok=True)
    shutil.copytree(root / "resources/licenses", licenses / "Qt", dirs_exist_ok=True)
    for name in ("PySide6", "PySide6-Essentials", "shiboken6", "python-docx", "lxml", "pyinstaller"):
        distribution = importlib.metadata.distribution(name)
        for file in distribution.files or []:
            if any(token in str(file).lower() for token in ("license", "copying", "copyright")):
                source = Path(distribution.locate_file(file))
                if source.is_file():
                    destination = licenses / name / str(file).replace("..", "_")
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, destination)
    license_names = [p.name.lower() for p in licenses.rglob("*") if p.is_file()]
    if not any("lgpl" in name for name in license_names) or not any("gpl" in name and "lgpl" not in name for name in license_names):
        raise SystemExit("Chưa thu thập đủ toàn văn LGPL/GPL của Qt; bổ sung giấy phép chính thức trước khi phân phối.")
    from check_release import verify
    reports = root / "build/windows-verification"
    result = verify(reports, cli=target / "vietspell-cli.exe", gui=target / "VietSpell.exe", allow_demo=args.allow_demo)
    if not result["passed"]:
        raise SystemExit("Bản đóng gói không vượt kiểm tra: "+result.get("error", "không rõ lỗi"))
    shutil.copy2(reports / "release-report.json", target / "BUILD-REPORT.json")
    samples = target / "samples"
    samples.mkdir(exist_ok=True)
    for path in reports.glob("*.docx"):
        shutil.copy2(path, samples / path.name)
    size = sum(p.stat().st_size for p in target.rglob("*") if p.is_file()) / 1024**2
    print(f"Thư mục sản phẩm: {target}, {size:.1f} MiB. Vẫn cần mở bốn bản Word và GUI trên Windows để xác minh trực quan.")
    if size > 250:
        raise SystemExit("Chưa đạt mục tiêu kích thước dưới 250 MiB.")
    label = "DEMO" if quality != "corpus" else "trained"
    archive = shutil.make_archive(str(root / f"dist/VietSpell-Windows-x64-{label}"), "zip", root_dir=target.parent, base_dir=target.name)
    print("Gói đã vượt kiểm tra tự động: "+archive)


if __name__ == "__main__":
    main()
