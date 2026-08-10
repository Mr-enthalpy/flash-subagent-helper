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
        gateway_path = ccr_home / "gateway.config.json"
        gateway_sentinel = b'{"runtime": "must-remain-untouched"}\n'
        gateway_path.write_bytes(gateway_sentinel)
        data["deployment"].update(codex_home=str(codex_home), ccr_home=str(ccr_home), backup_root="auto")
        with contextlib.redirect_stdout(io.StringIO()):
            package_tool.apply(data)
            revision_root = codex_home / "deployment-package-state" / "revisions"
            revisions_after_first = len(list(revision_root.iterdir()))
            current_pointer = json.loads((codex_home / "deployment-package-state" / "current.json").read_text(encoding="utf-8"))
            first_manifest_path = Path(current_pointer["manifest"])
            first_manifest = json.loads(first_manifest_path.read_text(encoding="utf-8"))
            legacy_manifest = dict(first_manifest)
            legacy_manifest["package_version"] = "0.3.0"
            legacy_manifest.pop("managed_target_set")
            first_manifest_path.write_text(json.dumps(legacy_manifest), encoding="utf-8")
            package_tool.plan(data)
            first_manifest_path.write_text(json.dumps(first_manifest), encoding="utf-8")
            first = {
                str(path.relative_to(codex_home)): package_tool.artifact_hash(path)
                for path in [codex_home / "models.worker.json", *[codex_home / "agents" / f"{role}.toml" for role in package["roles"]]]
            }
            package_tool.apply(data)
            assert len(list(revision_root.iterdir())) == revisions_after_first, "NOOP apply created a revision"
            second = {
                str(path.relative_to(codex_home)): package_tool.artifact_hash(path)
                for path in [codex_home / "models.worker.json", *[codex_home / "agents" / f"{role}.toml" for role in package["roles"]]]
            }
            assert first == second, "second apply changed deterministic artifacts"
            data["worker"]["model_selector"] = "fixture-provider/fixture-model-v2"
            package_tool.apply(data)
            assert len(list(revision_root.iterdir())) == revisions_after_first + 1
            package_tool.rollback(data)
            package_tool.uninstall(data)
        assert not (codex_home / "config.toml").exists()
        assert not (codex_home / "models.worker.json").exists()
        assert not (codex_home / "agents").exists() or not any((codex_home / "agents").iterdir())
        assert not (ccr_home / "plugins" / package["plugin_id"]).exists()
        assert gateway_path.read_bytes() == gateway_sentinel

    with tempfile.TemporaryDirectory(prefix="deployment-old-lifecycle-") as temporary:
        root = Path(temporary)
        codex_home, ccr_home = root / "codex", root / "ccr"
        state = codex_home / "deployment-package-state"
        manifest = state / "revisions" / "old" / "revision-manifest.json"
        manifest.parent.mkdir(parents=True)
        manifest.write_text(json.dumps({"package_version": "0.2.0"}), encoding="utf-8")
        state.mkdir(parents=True, exist_ok=True)
        (state / "current.json").write_text(json.dumps({"manifest": str(manifest)}), encoding="utf-8")
        data["deployment"].update(codex_home=str(codex_home), ccr_home=str(ccr_home), backup_root="auto")
        try:
            package_tool.plan(data)
        except package_tool.PackageError as error:
            assert "UNSUPPORTED LIFECYCLE UPGRADE" in str(error)
        else:
            raise AssertionError("0.2 to 0.3 lifecycle upgrade was not refused")

    with tempfile.TemporaryDirectory(prefix="deployment-target-set-") as temporary:
        root = Path(temporary)
        codex_home, ccr_home = root / "codex", root / "ccr"
        state = codex_home / "deployment-package-state"
        manifest = state / "revisions" / "changed-targets" / "revision-manifest.json"
        manifest.parent.mkdir(parents=True)
        manifest.write_text(json.dumps({
            "package_version": package["package_version"],
            "managed_target_set": ["codex:agent:unexpected_patch_role"],
            "installed_hashes": {},
        }), encoding="utf-8")
        state.mkdir(parents=True, exist_ok=True)
        (state / "current.json").write_text(json.dumps({"manifest": str(manifest)}), encoding="utf-8")
        data["deployment"].update(codex_home=str(codex_home), ccr_home=str(ccr_home), backup_root="auto")
        try:
            package_tool.plan(data)
        except package_tool.PackageError as error:
            assert "MANAGED TARGET SET CHANGED WITHIN PATCH SERIES" in str(error)
        else:
            raise AssertionError("patch-series managed target change was not refused")
    print("DEPLOYMENT LIFECYCLE PASS: apply, NOOP, upgrade, rollback, baseline uninstall, lifecycle and target-set refusals; CCR runtime untouched")


if __name__ == "__main__":
    main()
