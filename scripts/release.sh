#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: scripts/release.sh <version> [changelog line]

Examples:
  scripts/release.sh 0.4.1 "新增自动发版脚本"
  scripts/release.sh v0.5.0

The script updates project version files, creates a release commit and tag,
then pushes main and the tag to GitHub. Pushing the tag starts the GitHub
Actions Docker build and GitHub Release workflow.
USAGE
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" || $# -lt 1 ]]; then
  usage
  exit 0
fi

input_version="$1"
version="${input_version#v}"
tag="v${version}"
changelog_line="${2:-发布 ${tag}}"

if [[ ! "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "Version must use semantic format like 0.4.1 or v0.4.1." >&2
  exit 1
fi

repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root"

current_branch="$(git branch --show-current)"
if [[ "$current_branch" != "main" ]]; then
  echo "Release must be run from main. Current branch: ${current_branch}" >&2
  exit 1
fi

if [[ -n "$(git status --porcelain)" ]]; then
  echo "Working tree is not clean. Commit or stash your changes first." >&2
  git status --short
  exit 1
fi

git fetch origin --tags

if git rev-parse -q --verify "refs/tags/${tag}" >/dev/null; then
  echo "Tag ${tag} already exists." >&2
  exit 1
fi

python3 - "$version" <<'PY'
import json
import re
import sys
from pathlib import Path

version = sys.argv[1]

package_json = Path("frontend/package.json")
package_lock = Path("frontend/package-lock.json")
config_py = Path("backend/app/config.py")

for path in (package_json, package_lock):
    data = json.loads(path.read_text(encoding="utf-8"))
    data["version"] = version
    if path.name == "package-lock.json":
        data.setdefault("packages", {}).setdefault("", {})["version"] = version
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

config_text = config_py.read_text(encoding="utf-8")
updated = re.sub(r'app_version: str = "[^"]+"', f'app_version: str = "{version}"', config_text)
if updated == config_text:
    raise SystemExit("Could not update backend/app/config.py app_version.")
config_py.write_text(updated, encoding="utf-8")
PY

today="$(date +%F)"
python3 - "$tag" "$today" "$changelog_line" <<'PY'
import sys
from pathlib import Path

tag, today, changelog_line = sys.argv[1:4]
path = Path("CHANGELOG.md")
text = path.read_text(encoding="utf-8")
heading = f"## {tag} ({today})"

if heading not in text:
    marker = "\n## "
    insert = f"\n{heading}\n\n### 🔧 其他\n- {changelog_line}\n"
    if marker in text:
        title, rest = text.split(marker, 1)
        text = title.rstrip() + "\n" + insert + "\n## " + rest
    else:
        text = text.rstrip() + insert + "\n"
    path.write_text(text, encoding="utf-8")
PY

git add frontend/package.json frontend/package-lock.json backend/app/config.py CHANGELOG.md
git commit -m "Release ${tag}"
git tag -a "$tag" -m "Release ${tag}"
git push origin main
git push origin "$tag"

echo "Released ${tag}."
