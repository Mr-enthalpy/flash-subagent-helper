"""Offline package lifecycle test using only temporary fixture homes."""
from __future__ import annotations

import contextlib
import copy
import importlib.util
import io
import json
from pathlib import Path
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("package_tool", ROOT / "scripts" / "package_tool.py")
assert SPEC and SPEC.loader
package_tool = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(package_tool)


def main() -> None:
    data = copy.deepcopy(package_tool.deployment(ROOT / "tests" / "fixtures" / "deployment.test.toml"))
    package = package_tool.package_config()
    with tempfile.TemporaryDirectory(prefix="deployment-lifecycle-") as temporary:
        root = Path(temporary)
        codex_home, ccr_home = root / "codex", root / "ccr"
        ccr_home.mkdir(parents=True)
        (ccr_home / "gateway.config.json").write_text('{"plugins": [], "providers": []}\n', encoding="utf-8")
        data["deployment"].update(codex_home=str(codex_home), ccr_home=str(ccr_home), backup_root="auto")
        with contextlib.redirect_stdout(io.StringIO()):
            package_tool.apply(data)
            first = {
                str(path.relative_to(codex_home)): package_tool.artifact_hash(path)
                for path in [codex_home / "models.worker.json", *[codex_home / "agents" / f"{role}.toml" for role in package["roles"]]]
            }
            package_tool.apply(data)
            second = {
                str(path.relative_to(codex_home)): package_tool.artifact_hash(path)
                for path in [codex_home / "models.worker.json", *[codex_home / "agents" / f"{role}.toml" for role in package["roles"]]]
            }
            assert first == second, "second apply changed deterministic artifacts"
            package_tool.rollback(data)
            package_tool.uninstall(data)
        assert not (codex_home / "config.toml").exists()
        assert not (codex_home / "models.worker.json").exists()
        assert not (codex_home / "agents").exists() or not any((codex_home / "agents").iterdir())
        assert not (ccr_home / "plugins" / package["plugin_id"]).exists()
        gateway = json.loads((ccr_home / "gateway.config.json").read_text(encoding="utf-8"))
        assert gateway["plugins"] == []
    print("DEPLOYMENT LIFECYCLE PASS: apply x2, rollback, uninstall")


if __name__ == "__main__":
    main()
