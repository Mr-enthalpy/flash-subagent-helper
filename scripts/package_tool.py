#!/usr/bin/env python3
"""Provider-independent renderer, validator, deployer, and doctor.

CODEX-SENSITIVE:
WHY: Codex typed roles currently use [agents.<name>] config entries whose
config_file points at a role TOML containing model/provider/catalog fields.
VERIFIED AGAINST: Codex CLI 0.146.0 on Windows.
FAILURE SYMPTOM: roles are absent, rejected by strict config, or inherit root.

CCR-SENSITIVE:
WHY: CCR plugin registration differs by build. This tool detects known
interfaces and refuses silent registration on unknown builds.
VERIFIED AGAINST: providerPlugins.transformRequest and CUSTOM_ROUTER_PATH.
FAILURE SYMPTOM: plugin tests pass but live upstream bodies remain unchanged.
"""

from __future__ import annotations

import argparse
import datetime as dt
import fnmatch
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import tomllib
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
BEGIN = "# BEGIN MANAGED: codex-ccr-deepseek-worker-pool:v1"
END = "# END MANAGED: codex-ccr-deepseek-worker-pool:v1"
ROLES = (
    "deepseek_scout", "deepseek_analyst", "deepseek_auditor",
    "deepseek_coder", "deepseek_test_coder", "deepseek_config_coder",
    "deepseek_worker",
)
FORBIDDEN_NAMES = {
    "auth.json", "cap_sid", "models_cache.json", ".env",
    ".codex-global-state.json",
}


class PackageError(RuntimeError):
    pass


def load_toml(path: Path) -> dict:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def artifact_hash(path: Path) -> str:
    if path.is_file():
        return sha256(path)
    digest = hashlib.sha256()
    for child in sorted(p for p in path.rglob("*") if p.is_file()):
        digest.update(child.relative_to(path).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(sha256(child).encode("ascii"))
        digest.update(b"\0")
    return digest.hexdigest()


def stable_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def ps_auto_home(kind: str) -> Path:
    if kind == "codex":
        return Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
    override = os.environ.get("CCR_HOME")
    if override:
        return Path(override)
    appdata = os.environ.get("APPDATA")
    return Path(appdata) / "claude-code-router" if appdata else Path.home() / ".ccr"


def resolve_home(value: str, kind: str) -> Path:
    return ps_auto_home(kind) if value == "auto" else Path(value).expanduser().resolve()


def deployment(path: Path) -> dict:
    data = load_toml(path)
    required = {
        "worker": ("model_family", "compatibility_profile", "provider_id", "model_selector"),
        "gateway": ("local_base_url", "client_key_env", "route_id"),
        "deployment": ("codex_home", "ccr_home"),
    }
    for section, keys in required.items():
        if section not in data:
            raise PackageError(f"missing [{section}]")
        for key in keys:
            value = data[section].get(key)
            if not isinstance(value, str) or not value.strip():
                raise PackageError(f"missing {section}.{key}")
    for value in (data["worker"]["provider_id"], data["worker"]["model_selector"]):
        if value.startswith("<"):
            raise PackageError("deployment file still contains configuration placeholders")
    return data


def load_sources(data: dict) -> tuple[dict, dict, list[dict]]:
    family_id = data["worker"]["model_family"]
    profile_id = data["worker"]["compatibility_profile"]
    family_path = ROOT / "model-families" / f"{family_id}.toml"
    profile_path = ROOT / "compatibility" / f"{profile_id}.toml"
    if not family_path.is_file() or not profile_path.is_file():
        raise PackageError("model family or compatibility profile reference is missing")
    family = load_toml(family_path)
    profile = load_toml(profile_path)
    roles = [load_toml(ROOT / "roles" / f"{name}.toml") for name in ROLES]
    if {role["id"] for role in roles} != set(ROLES):
        raise PackageError("role ids are missing or duplicated")
    return family, profile, roles


def quote_toml(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def render_tree(data: dict, output: Path, codex_home: Path | None = None) -> dict[str, str]:
    family, profile, roles = load_sources(data)
    worker = data["worker"]
    gateway = data["gateway"]
    catalog_path = (codex_home / "models.worker.json") if codex_home else Path("<CODEX_HOME>") / "models.worker.json"
    generated: dict[str, str] = {}

    # CODEX-SENSITIVE: model catalog fields and load lifecycle are version-bound.
    # VERIFIED AGAINST: Codex CLI 0.146.0. FAILURE SYMPTOM: catalog rejected or
    # auto-review falls back to an unavailable reviewer model.
    model = {
        "slug": worker["model_selector"],
        "display_name": family["display_name"],
        "context_window": family["default_context_window"],
        "default_reasoning_level": family["default_reasoning_level"],
        "supported_reasoning_levels": [
            {"effort": level, "description": f"{level} reasoning"}
            for level in family["reasoning_levels"]
        ],
        "shell_type": "shell_command",
        "apply_patch_tool_type": family["capability_defaults"]["apply_patch_tool_type"],
        "supports_parallel_tool_calls": family["capability_defaults"]["supports_parallel_tool_calls"],
        "supports_web_search": family["capability_defaults"]["supports_web_search"],
        "supports_multi_agent": family["capability_defaults"]["supports_multi_agent"],
        "auto_review_model_override": worker["model_selector"],
        "compatibility_profile": profile["id"],
        "effective_model_identity": worker.get("effective_model_identity", "USER_MUST_VERIFY"),
    }
    generated["models.worker.json"] = stable_json({"models": [model]})

    config_lines = [BEGIN]
    for role in roles:
        path = (codex_home / "agents" / f"{role['id']}.toml") if codex_home else Path("<CODEX_HOME>") / "agents" / f"{role['id']}.toml"
        config_lines.extend([
            f"[agents.{role['id']}]",
            f"description = {quote_toml(role['description'])}",
            f"config_file = {quote_toml(str(path))}",
            "",
        ])
        role_lines = [
            f"model_provider = {quote_toml(worker['provider_id'])}",
            f"model = {quote_toml(worker['model_selector'])}",
            f"model_catalog_json = {quote_toml(str(catalog_path))}",
            f"sandbox_mode = {quote_toml(role['sandbox'])}",
            f"network_access = {'true' if role['network'] else 'false'}",
            "approval_policy = \"on-request\"",
            f"developer_instructions = {quote_toml(role['instructions'])}",
            "",
        ]
        generated[f"agents/{role['id']}.toml"] = "\n".join(role_lines)
    config_lines.append(END)
    generated["config.fragment.toml"] = "\n".join(config_lines) + "\n"
    generated["plugin-profile.json"] = stable_json({
        "profile_id": profile["id"],
        "profile_version": profile["version"],
        "model_selectors": [worker["model_selector"]],
        "responses_endpoint_suffix": "/responses",
        "unsupported_tool_types": profile["unsupported_tool_types"],
        "namespace_tool_choice_fallback": profile["namespace_tool_choice_fallback"],
        "route_id": gateway["route_id"],
    })
    for relative, content in generated.items():
        write_text(output / relative, content)
    manifest = {"schema_version": 1, "files": {name: hashlib.sha256(text.encode()).hexdigest() for name, text in sorted(generated.items())}}
    write_text(output / "deployment-manifest.json", stable_json(manifest))
    generated["deployment-manifest.json"] = (output / "deployment-manifest.json").read_text(encoding="utf-8")
    return generated


def remove_managed_block(text: str) -> tuple[str, bool]:
    pattern = re.compile(rf"(?ms)^\Q{BEGIN}\E.*?^\Q{END}\E\s*".replace("\\Q", "").replace("\\E", ""))
    match = pattern.search(text)
    return (pattern.sub("", text), bool(match))


def check_conflicts(config_text: str) -> None:
    unmanaged, _ = remove_managed_block(config_text)
    for role in ROLES:
        if re.search(rf"(?m)^\s*\[agents\.{re.escape(role)}\]\s*$", unmanaged):
            raise PackageError(f"CONFLICT: unmanaged agent already exists: {role}")


def command_version(command: str) -> str | None:
    executable = shutil.which(command)
    if not executable:
        return None
    for args in ([executable, "--version"], [executable, "version"]):
        try:
            result = subprocess.run(args, capture_output=True, text=True, timeout=8, check=False)
            value = (result.stdout or result.stderr).strip().splitlines()
            if value:
                return value[0][:160]
        except Exception:
            pass
    return "present-version-unknown"


def detect_ccr(ccr_home: Path) -> dict:
    version = command_version("ccr")
    gateway = ccr_home / "gateway.config.json"
    mechanisms: list[str] = []
    if gateway.is_file():
        text = gateway.read_text(encoding="utf-8", errors="ignore")
        if '"plugins"' in text:
            mechanisms.append("gateway_plugin_config")
        if "providerPlugins" in text or "transformRequest" in text:
            mechanisms.append("provider_transformer")
        if "CUSTOM_ROUTER_PATH" in text or "customRouter" in text:
            mechanisms.append("custom_router")
    status = "VERIFIED" if version and mechanisms else "UNVERIFIED"
    return {"version": version or "not-detected", "mechanisms": mechanisms, "status": status}


def plan(data: dict) -> dict:
    codex_home = resolve_home(data["deployment"]["codex_home"], "codex")
    ccr_home = resolve_home(data["deployment"]["ccr_home"], "ccr")
    ccr = detect_ccr(ccr_home)
    config = codex_home / "config.toml"
    existing = config.read_text(encoding="utf-8") if config.is_file() else ""
    check_conflicts(existing)
    artifact_targets = [codex_home / "agents" / f"{r}.toml" for r in ROLES] + [codex_home / "models.worker.json"]
    config_target = codex_home / "config.toml"
    plugin_target = ccr_home / "plugins" / "responses-tool-capability-compat"
    create_targets = [str(path) for path in artifact_targets if not path.exists()]
    modify_targets = [str(path) for path in artifact_targets if path.exists()]
    (modify_targets if config_target.exists() else create_targets).append(str(config_target))
    (modify_targets if plugin_target.exists() else create_targets).append(str(plugin_target))
    return {
        "detected": {"codex": command_version("codex") or "not-detected", "ccr": ccr["version"]},
        "target": {
            "model_family": data["worker"]["model_family"],
            "provider": data["worker"]["provider_id"],
            "model_selector": data["worker"]["model_selector"],
            "compatibility_profile": data["worker"]["compatibility_profile"],
        },
        "will_create": create_targets,
        "will_modify": modify_targets + ([str(ccr_home / "gateway.config.json")] if (ccr_home / "gateway.config.json").exists() else []),
        "will_preserve": ["root model/provider", "login/auth", "unmanaged agents", "MCP", "tools", "unrelated instructions"],
        "external_dependencies": ["Codex login", "CCR installation", "CCR upstream credential", data["gateway"]["client_key_env"]],
        "restart_required": True,
        "compatibility_status": ccr["status"],
        "ccr_mechanisms": ccr["mechanisms"],
        "codex_home": str(codex_home),
        "ccr_home": str(ccr_home),
    }


def print_plan(value: dict) -> None:
    print("DEPLOYMENT PLAN")
    print(stable_json(value), end="")


def apply(data: dict, allow_unverified: bool) -> None:
    value = plan(data)
    print_plan(value)
    if value["compatibility_status"] != "VERIFIED" and not allow_unverified:
        raise PackageError("UNVERIFIED CCR VERSION: aborting; use explicit compatibility override only after review")
    codex_home = Path(value["codex_home"])
    ccr_home = Path(value["ccr_home"])
    timestamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    configured_backup_root = data["deployment"].get("backup_root", "auto")
    revision_root = (
        codex_home / "deployment-package-state" / "revisions" / timestamp
        if configured_backup_root == "auto"
        else Path(configured_backup_root).expanduser().resolve() / timestamp
    )
    current_path = codex_home / "deployment-package-state" / "current.json"
    previous_current = None
    if current_path.is_file():
        previous_current = json.loads(current_path.read_text(encoding="utf-8"))
    backup_root = revision_root / "backups"
    created: list[str] = []
    modified: list[str] = []
    backups: dict[str, str] = {}

    # Complete structural/conflict preflight before the first deployment write.
    plugin_target = ccr_home / "plugins" / "responses-tool-capability-compat"
    if plugin_target.exists():
        plugin_meta = plugin_target / "plugin.json"
        try:
            plugin_owned = json.loads(plugin_meta.read_text(encoding="utf-8")).get("id") == "responses-tool-capability-compat"
        except Exception:
            plugin_owned = False
        if not plugin_owned:
            raise PackageError(f"CONFLICT: plugin target is not package-owned: {plugin_target}")
    gateway_config = ccr_home / "gateway.config.json"
    if not gateway_config.is_file():
        raise PackageError("CCR gateway.config.json not found; cannot register compatibility plugin")
    gateway_data = json.loads(gateway_config.read_text(encoding="utf-8"))
    plugins = gateway_data.get("plugins")
    if not isinstance(plugins, list):
        raise PackageError("UNVERIFIED CCR VERSION: gateway plugins[] interface missing")
    plugin_key = "responses-tool-capability-compat-core"
    module_path = str(plugin_target / "gateway-plugin.cjs")
    existing_plugin = next((entry for entry in plugins if isinstance(entry, dict) and entry.get("key") == plugin_key), None)
    if existing_plugin and existing_plugin.get("modulePath") != module_path:
        raise PackageError(f"CONFLICT: CCR plugin key is owned by another module: {plugin_key}")

    with tempfile.TemporaryDirectory(prefix="codex-worker-pool-render-") as temp:
        rendered = Path(temp)
        render_tree(data, rendered, codex_home)
        targets = [(rendered / "models.worker.json", codex_home / "models.worker.json")]
        targets += [(rendered / "agents" / f"{r}.toml", codex_home / "agents" / f"{r}.toml") for r in ROLES]
        for source, target in targets:
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists():
                backup = backup_root / target.relative_to(codex_home)
                backup.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(target, backup)
                backups[str(target)] = str(backup)
                modified.append(str(target))
            else:
                created.append(str(target))
            shutil.copy2(source, target)
        config = codex_home / "config.toml"
        old = config.read_text(encoding="utf-8") if config.exists() else ""
        check_conflicts(old)
        without, _ = remove_managed_block(old)
        if config.exists():
            backup = backup_root / "config.toml"
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(config, backup)
            backups[str(config)] = str(backup)
            modified.append(str(config))
        else:
            created.append(str(config))
        fragment = (rendered / "config.fragment.toml").read_text(encoding="utf-8")
        write_text(config, without.rstrip() + "\n\n" + fragment)

        if plugin_target.exists():
            backup = backup_root / "ccr-plugin" / plugin_target.name
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(plugin_target, backup)
            backups[str(plugin_target)] = str(backup)
            modified.append(str(plugin_target))
            shutil.rmtree(plugin_target)
        else:
            created.append(str(plugin_target))
        plugin_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(ROOT / "plugins" / "responses-tool-capability-compat", plugin_target)
        shutil.copy2(rendered / "plugin-profile.json", plugin_target / "capability-profile.json")

        # CCR-SENSITIVE: parser-aware merge into the verified gateway plugin
        # list. VERIFIED AGAINST: gateway.config.json plugins[] interface on
        # 2026-08-09. FAILURE SYMPTOM: plugin files exist but never enter the
        # live request pipeline.
        backup = backup_root / "ccr" / "gateway.config.json"
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(gateway_config, backup)
        backups[str(gateway_config)] = str(backup)
        modified.append(str(gateway_config))
        if existing_plugin:
            existing_plugin.update({"enabled": True, "modulePath": module_path})
        else:
            plugins.append({"enabled": True, "key": plugin_key, "modulePath": module_path})
        write_text(gateway_config, stable_json(gateway_data))

    hashes = {}
    for item in created + modified:
        path = Path(item)
        if path.exists():
            hashes[item] = artifact_hash(path)
    manifest = {
        "schema_version": 1,
        "package_version": load_toml(ROOT / "package.toml")["package_version"],
        "timestamp": timestamp,
        "created": created,
        "modified": modified,
        "backups": backups,
        "installed_hashes": hashes,
        "previous_current": previous_current,
    }
    write_text(revision_root / "revision-manifest.json", stable_json(manifest))
    write_text(current_path, stable_json({"revision": timestamp, "manifest": str(revision_root / "revision-manifest.json")}))
    print(f"APPLIED revision={timestamp}; full Codex restart required")


def latest_manifest(codex_home: Path) -> tuple[Path, dict]:
    current = codex_home / "deployment-package-state" / "current.json"
    if not current.is_file():
        raise PackageError("no package-managed deployment found")
    pointer = json.loads(current.read_text(encoding="utf-8"))
    path = Path(pointer["manifest"])
    return path, json.loads(path.read_text(encoding="utf-8"))


def rollback(data: dict) -> None:
    codex_home = resolve_home(data["deployment"]["codex_home"], "codex")
    manifest_path, manifest = latest_manifest(codex_home)
    # Validate the entire rollback set before restoring or deleting anything.
    for item in manifest["created"] + manifest["modified"]:
        path = Path(item)
        expected = manifest["installed_hashes"].get(item)
        if path.exists() and expected and artifact_hash(path) != expected:
            raise PackageError(f"refusing rollback: managed artifact changed: {path}")
    for original, backup in manifest["backups"].items():
        target, source = Path(original), Path(backup)
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.is_dir():
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(source, target)
        else:
            shutil.copy2(source, target)
    for item in sorted(manifest["created"], key=len, reverse=True):
        path = Path(item)
        if path.is_file():
            path.unlink()
        elif path.is_dir() and path.name == "responses-tool-capability-compat":
            shutil.rmtree(path)
    current_path = codex_home / "deployment-package-state" / "current.json"
    if manifest.get("previous_current"):
        write_text(current_path, stable_json(manifest["previous_current"]))
    else:
        current_path.unlink(missing_ok=True)
    print(f"ROLLED BACK {manifest_path.parent.name}; restart required")


def uninstall(data: dict) -> None:
    codex_home = resolve_home(data["deployment"]["codex_home"], "codex")
    _, manifest = latest_manifest(codex_home)
    config = codex_home / "config.toml"
    ccr_home = resolve_home(data["deployment"]["ccr_home"], "ccr")
    if config.is_file():
        cleaned, found = remove_managed_block(config.read_text(encoding="utf-8"))
        if not found:
            raise PackageError("managed config marker is missing; refusing uninstall")
        write_text(config, cleaned.rstrip() + "\n")
    for item in manifest["created"] + manifest["modified"]:
        path = Path(item)
        gateway_config = ccr_home / "gateway.config.json"
        if path == gateway_config and path.is_file():
            expected = manifest["installed_hashes"].get(item)
            if expected and artifact_hash(path) != expected:
                raise PackageError(f"refusing uninstall: CCR gateway config changed: {path}")
            value = json.loads(path.read_text(encoding="utf-8"))
            plugin_target = ccr_home / "plugins" / "responses-tool-capability-compat" / "gateway-plugin.cjs"
            value["plugins"] = [entry for entry in value.get("plugins", []) if not (isinstance(entry, dict) and entry.get("key") == "responses-tool-capability-compat-core" and entry.get("modulePath") == str(plugin_target))]
            write_text(path, stable_json(value))
            continue
        if path == config or not path.exists():
            continue
        expected = manifest["installed_hashes"].get(item)
        if path.is_file() and expected and artifact_hash(path) == expected:
            path.unlink()
        elif path.is_dir() and path.name == "responses-tool-capability-compat" and expected and artifact_hash(path) == expected:
            shutil.rmtree(path)
        else:
            raise PackageError(f"refusing uninstall: managed artifact changed: {path}")
    print("UNINSTALLED package-owned artifacts only; restart required")


def allowed(path: Path, patterns: list[str]) -> bool:
    relative = path.relative_to(ROOT).as_posix()
    return any(fnmatch.fnmatch(relative, pattern) for pattern in patterns)


def secret_scan() -> list[str]:
    patterns = [line.strip() for line in (ROOT / "publish-allowlist.txt").read_text(encoding="utf-8").splitlines() if line.strip() and not line.startswith("#")]
    findings: list[str] = []
    secret_patterns = [
        ("OpenAI-shaped secret", re.compile(r"(?<![A-Za-z0-9])sk-[A-Za-z0-9_-]{16,}")),
        ("Bearer value", re.compile(r"(?i)Bearer\s+[A-Za-z0-9._~+/=-]{12,}")),
        ("credential assignment", re.compile(r"(?i)(api[_-]?key|authorization|cookie|client[_-]?key|token)\s*[=:]\s*[\"'](?!<|\$|env:)[^\"']{8,}[\"']")),
        ("profile credential", re.compile(r"ccr-profile-[A-Za-z0-9_-]{8,}")),
        ("Windows user path", re.compile(r"(?i)[A-Z]:\\Users\\(?!<|USER|username)[^\\\s]+\\")),
    ]
    for path in sorted(p for p in ROOT.rglob("*") if p.is_file() and ".git" not in p.parts):
        rel = path.relative_to(ROOT).as_posix()
        if not allowed(path, patterns):
            findings.append(f"not in deployment allowlist: {rel}")
            continue
        if path.name in FORBIDDEN_NAMES or path.suffix in {".sqlite", ".db"}:
            findings.append(f"forbidden file: {rel}")
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            findings.append(f"binary/non-UTF8 file: {rel}")
            continue
        for label, regex in secret_patterns:
            if regex.search(text):
                findings.append(f"{label}: {rel}")
    return findings


def validate() -> None:
    for path in sorted(ROOT.rglob("*.toml")):
        load_toml(path)
    for path in sorted(ROOT.rglob("*.json")):
        json.loads(path.read_text(encoding="utf-8"))
    for path in sorted(ROOT.rglob("*.cjs")):
        result = subprocess.run(["node", "--check", str(path)], capture_output=True, text=True)
        if result.returncode:
            raise PackageError(f"JavaScript syntax error: {path}: {result.stderr.strip()}")
    test_data = deployment(ROOT / "tests" / "fixtures" / "deployment.test.toml")
    _, _, roles = load_sources(test_data)
    if len(roles) != len({role["id"] for role in roles}):
        raise PackageError("duplicate roles")
    findings = secret_scan()
    if findings:
        raise PackageError("secret/allowlist scan failed:\n" + "\n".join(findings))
    with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
        one, two = Path(first), Path(second)
        render_tree(test_data, one, Path("C:/fixture/codex-home"))
        render_tree(test_data, two, Path("C:/fixture/codex-home"))
        files_one = {p.relative_to(one).as_posix(): sha256(p) for p in one.rglob("*") if p.is_file()}
        files_two = {p.relative_to(two).as_posix(): sha256(p) for p in two.rglob("*") if p.is_file()}
        if files_one != files_two:
            raise PackageError("render is not deterministic")
        fragment = (one / "config.fragment.toml").read_text(encoding="utf-8")
        merged = "model = \"official-root-model\"\n\n" + fragment
        cleaned, found = remove_managed_block(merged)
        if not found or "official-root-model" not in cleaned:
            raise PackageError("managed merge/removal invariant failed")
        try:
            check_conflicts("[agents.deepseek_scout]\nconfig_file = \"unmanaged.toml\"\n")
        except PackageError:
            pass
        else:
            raise PackageError("unmanaged same-name role conflict was not detected")
    print("VALIDATION PASS: TOML JSON CJS schema refs secrets determinism idempotence")


def doctor(data: dict, live: bool, confirm_cost: bool) -> None:
    value = plan(data)
    codex_home, ccr_home = Path(value["codex_home"]), Path(value["ccr_home"])
    env_name = data["gateway"]["client_key_env"]
    host = data["gateway"]["local_base_url"].split("://", 1)[-1].split("/", 1)[0]
    hostname, _, port_text = host.partition(":")
    try:
        with socket.create_connection((hostname, int(port_text or "80")), timeout=1):
            port_status = "reachable"
    except Exception:
        port_status = "not-reachable"
    report = {
        "powershell": command_version("pwsh") or "missing",
        "python": command_version("python") or sys.version.split()[0],
        "node": command_version("node") or "missing",
        "codex": value["detected"]["codex"],
        "ccr": value["detected"]["ccr"],
        "ccr_port": port_status,
        "required_env_present": bool(os.environ.get(env_name)),
        "required_env_name": env_name,
        "model_catalog": (codex_home / "models.worker.json").is_file(),
        "registered_roles": all((codex_home / "agents" / f"{r}.toml").is_file() for r in ROLES),
        "compatibility_plugin": (ccr_home / "plugins" / "responses-tool-capability-compat").is_dir(),
        "ccr_mechanisms": value["ccr_mechanisms"],
        "mode": "live" if live else "offline",
    }
    if live:
        if not confirm_cost:
            raise PackageError("live mode may make a real API request and consume tokens; pass --confirm-cost")
        key = os.environ.get(env_name)
        if not key:
            raise PackageError(f"required environment variable is absent: {env_name}")
        endpoint = data["gateway"]["local_base_url"].rstrip("/") + "/responses"
        body = stable_json({
            "model": data["worker"]["model_selector"],
            "input": "Return exactly OK.",
            "max_output_tokens": 8,
            "tools": [{"type": "namespace", "name": "fixture_namespace", "tools": []}, {"type": "function", "name": "fixture_function", "description": "fixture", "parameters": {"type": "object", "properties": {}}}],
            "tool_choice": {"type": "namespace", "name": "fixture_namespace"},
        }).encode("utf-8")
        request = urllib.request.Request(endpoint, data=body, method="POST", headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"})
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                report["live_http_status"] = response.status
                report["live_response_valid"] = 200 <= response.status < 300
        except urllib.error.HTTPError as error:
            report["live_http_status"] = error.code
            report["live_response_valid"] = False
        except Exception as error:
            report["live_error_type"] = type(error).__name__
            report["live_response_valid"] = False
    print(stable_json(report), end="")


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("validate")
    sub.add_parser("secret-scan")
    render_p = sub.add_parser("render")
    render_p.add_argument("--deployment", type=Path, required=True)
    render_p.add_argument("--output", type=Path, required=True)
    render_p.add_argument("--codex-home", type=Path)
    for name in ("plan", "apply", "rollback", "uninstall", "doctor"):
        item = sub.add_parser(name)
        item.add_argument("--deployment", type=Path, required=True)
        if name == "apply":
            item.add_argument("--allow-unverified-ccr", action="store_true")
        if name == "doctor":
            item.add_argument("--live", action="store_true")
            item.add_argument("--confirm-cost", action="store_true")
    args = parser.parse_args()
    try:
        if args.command == "validate":
            validate()
        elif args.command == "secret-scan":
            findings = secret_scan()
            if findings:
                raise PackageError("secret/allowlist scan failed:\n" + "\n".join(findings))
            print("SECRET SCAN PASS")
        elif args.command == "render":
            render_tree(deployment(args.deployment), args.output, args.codex_home)
            print(f"RENDERED {args.output}")
        else:
            data = deployment(args.deployment)
            if args.command == "plan":
                print_plan(plan(data))
            elif args.command == "apply":
                apply(data, args.allow_unverified_ccr)
            elif args.command == "rollback":
                rollback(data)
            elif args.command == "uninstall":
                uninstall(data)
            elif args.command == "doctor":
                doctor(data, args.live, args.confirm_cost)
        return 0
    except (PackageError, OSError, ValueError, json.JSONDecodeError, tomllib.TOMLDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
