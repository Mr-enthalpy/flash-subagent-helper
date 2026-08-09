#!/usr/bin/env python3
"""Provider-independent renderer, validator, deployer, and doctor.

CODEX-SENSITIVE:
WHY: provider, typed-agent, sandbox, and ModelInfo structures are external Codex
interfaces. VERIFIED AGAINST: Codex CLI 0.146.0 on Windows.
FAILURE SYMPTOM: strict-load rejection, missing roles, or wrong Guardian model.

CCR-SENSITIVE:
WHY: plugin registration is external. Compatibility is decided by an executable
adapter contract, never inferred from a version string.
VERIFIED AGAINST: gateway_plugin_v1, 2026-08-09.
FAILURE SYMPTOM: the contract probe fails before deployment.
"""
from __future__ import annotations

import argparse, datetime as dt, fnmatch, hashlib, json, os, re, shutil, socket
import subprocess, sys, tempfile, tomllib, urllib.error, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_NAMES = {"auth.json", "cap_sid", "models_cache.json", ".env", ".codex-global-state.json"}
PACKAGE_KEYS = {"schema_version", "package_id", "package_version", "managed_marker", "local_provider_id", "plugin_id", "roles"}
DEPLOYMENT_KEYS = {
    "deployment": {"codex_home", "ccr_home", "backup_root"},
    "gateway": {"base_url", "client_key_env"},
    "worker": {"model_selector", "profile", "effective_model_identity"},
    "ccr": {"adapter"},
}
PROFILE_KEYS = {"schema_version", "id", "version", "codex_baseline", "model_template", "responses_endpoint_suffix", "unsupported_tool_types", "tool_choice_fallback"}
ROLE_KEYS = {"id", "description", "sandbox", "network", "instructions"}


class PackageError(RuntimeError): pass


def load_toml(path: Path) -> dict:
    with path.open("rb") as handle: return tomllib.load(handle)


def package_config() -> dict:
    value = load_toml(ROOT / "package.toml")
    if set(value) != PACKAGE_KEYS or value.get("schema_version") != 2:
        raise PackageError("package.toml contains missing, duplicated-source, or unsupported keys")
    roles = value.get("roles")
    if not isinstance(roles, list) or not roles or len(roles) != len(set(roles)):
        raise PackageError("package.toml roles must be a non-empty unique list")
    identifiers = [value["local_provider_id"], value["plugin_id"], *roles]
    if not all(isinstance(item, str) and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_-]*", item) for item in identifiers):
        raise PackageError("package.toml contains an unsafe provider/plugin/role identifier")
    plugin_manifest = ROOT / "plugins" / value["plugin_id"] / "plugin.json"
    if not plugin_manifest.is_file() or json.loads(plugin_manifest.read_text(encoding="utf-8")).get("id") != value["plugin_id"]:
        raise PackageError("package.toml plugin_id does not resolve to a matching plugin manifest")
    return value


def roles_from(package: dict) -> tuple[str, ...]: return tuple(package["roles"])


def markers(package: dict) -> tuple[str, str]:
    marker = package["managed_marker"]
    return f"# BEGIN MANAGED: {marker}", f"# END MANAGED: {marker}"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(65536), b""): digest.update(block)
    return digest.hexdigest()


def artifact_hash(path: Path) -> str:
    if path.is_file(): return sha256(path)
    digest = hashlib.sha256()
    for child in sorted(p for p in path.rglob("*") if p.is_file()):
        digest.update(child.relative_to(path).as_posix().encode()); digest.update(b"\0")
        digest.update(sha256(child).encode()); digest.update(b"\0")
    return digest.hexdigest()


def stable_json(value: object) -> str: return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def auto_home(kind: str) -> Path:
    if kind == "codex": return Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
    if os.environ.get("CCR_HOME"): return Path(os.environ["CCR_HOME"])
    return Path(os.environ["APPDATA"]) / "claude-code-router" if os.environ.get("APPDATA") else Path.home() / ".ccr"


def resolve_home(value: str, kind: str) -> Path: return auto_home(kind) if value == "auto" else Path(value).expanduser().resolve()


def exact_keys(label: str, value: dict, allowed: set[str], required: set[str] | None = None) -> None:
    extra, missing = set(value) - allowed, (required or allowed) - set(value)
    if extra or missing: raise PackageError(f"{label} keys invalid; missing={sorted(missing)} extra={sorted(extra)}")


def deployment(path: Path) -> dict:
    data = load_toml(path)
    if data.get("schema_version") != 2: raise PackageError("deployment schema_version must be 2")
    exact_keys("deployment root", data, {"schema_version", *DEPLOYMENT_KEYS})
    for section, allowed in DEPLOYMENT_KEYS.items():
        if not isinstance(data.get(section), dict): raise PackageError(f"missing [{section}]")
        optional = {"backup_root"} if section == "deployment" else ({"effective_model_identity"} if section == "worker" else set())
        required = allowed - optional
        exact_keys(section, data[section], allowed, required)
        for key in required:
            if not isinstance(data[section][key], str) or not data[section][key].strip(): raise PackageError(f"missing {section}.{key}")
    if data["worker"]["model_selector"].startswith("<"): raise PackageError("deployment file still contains a model selector placeholder")
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", data["gateway"]["client_key_env"]): raise PackageError("invalid gateway.client_key_env")
    gateway_url = urllib.parse.urlparse(data["gateway"]["base_url"])
    if gateway_url.scheme not in {"http", "https"} or gateway_url.hostname not in {"127.0.0.1", "localhost", "::1"} or gateway_url.username or gateway_url.password:
        raise PackageError("gateway.base_url must be a credential-free loopback HTTP(S) URL")
    if data["ccr"]["adapter"] != "gateway_plugin_v1": raise PackageError("unsupported ccr.adapter")
    return data


def load_sources(data: dict) -> tuple[dict, list[dict], dict]:
    package, profile_id = package_config(), data["worker"]["profile"]
    profile_path = ROOT / "profile" / profile_id / "profile.toml"
    if not profile_path.is_file(): raise PackageError(f"profile missing: {profile_id}")
    profile = load_toml(profile_path); exact_keys("profile", profile, PROFILE_KEYS)
    if profile["id"] != profile_id or not (profile_path.parent / profile["model_template"]).is_file(): raise PackageError("profile identity/template invalid")
    roles = []
    for name in roles_from(package):
        path = ROOT / "roles" / f"{name}.toml"
        if not path.is_file(): raise PackageError(f"declared role missing: {name}")
        role = load_toml(path); exact_keys(f"role {name}", role, ROLE_KEYS)
        if role["id"] != name or role["sandbox"] not in {"read-only", "workspace-write"}: raise PackageError(f"invalid role: {name}")
        if role["network"] is not False: raise PackageError(f"network must remain denied: {name}")
        roles.append(role)
    if {p.stem for p in (ROOT / "roles").glob("*.toml")} != set(roles_from(package)): raise PackageError("role files differ from package.toml")
    return profile, roles, package


def quote_toml(value: str) -> str: return json.dumps(value, ensure_ascii=False)


def render_catalog(profile: dict, selector: str) -> dict:
    path = ROOT / "profile" / profile["id"] / profile["model_template"]
    catalog = json.loads(path.read_text(encoding="utf-8")); models = catalog.get("models")
    if not isinstance(models, list) or len(models) != 1: raise PackageError("model template must contain one ModelInfo")
    model = models[0]
    if model.get("slug") != "__MODEL_SELECTOR__" or model.get("auto_review_model_override") != "__MODEL_SELECTOR__": raise PackageError("model selector placeholders missing")
    model["slug"] = selector; model["auto_review_model_override"] = selector
    return catalog


def render_tree(data: dict, output: Path, codex_home: Path | None = None) -> dict[str, str]:
    profile, roles, package = load_sources(data); worker, gateway = data["worker"], data["gateway"]
    provider_id, (begin, end) = package["local_provider_id"], markers(package)
    catalog_path = (codex_home / "models.worker.json") if codex_home else Path("<CODEX_HOME>") / "models.worker.json"
    generated = {"models.worker.json": stable_json(render_catalog(profile, worker["model_selector"]))}
    # CODEX-SENSITIVE: native provider fields; verified Codex 0.146.0.
    # FAILURE SYMPTOM: workers inherit the root provider or local auth is unused.
    config = [begin, f"[model_providers.{provider_id}]", 'name = "CCR Flash Worker"', f"base_url = {quote_toml(gateway['base_url'].rstrip('/'))}", f"env_key = {quote_toml(gateway['client_key_env'])}", 'wire_api = "responses"', "requires_openai_auth = false", ""]
    for role in roles:
        role_path = (codex_home / "agents" / f"{role['id']}.toml") if codex_home else Path("<CODEX_HOME>") / "agents" / f"{role['id']}.toml"
        config += [f"[agents.{role['id']}]", f"description = {quote_toml(role['description'])}", f"config_file = {quote_toml(str(role_path))}", ""]
        lines = [f"model_provider = {quote_toml(provider_id)}", f"model = {quote_toml(worker['model_selector'])}", f"model_catalog_json = {quote_toml(str(catalog_path))}", f"sandbox_mode = {quote_toml(role['sandbox'])}", 'approval_policy = "on-request"', f"developer_instructions = {quote_toml(role['instructions'])}"]
        if role["network"] is False:
            # CODEX-SENSITIVE: network_access is nested here, not top-level.
            # VERIFIED AGAINST: Codex 0.146.0. FAILURE: strict rejection or network grant.
            lines += ["", "[sandbox_workspace_write]", "network_access = false"]
        lines.append(""); generated[f"agents/{role['id']}.toml"] = "\n".join(lines)
    config.append(end); generated["config.fragment.toml"] = "\n".join(config) + "\n"
    generated["plugin-profile.json"] = stable_json({"profile_id": profile["id"], "profile_version": profile["version"], "model_selectors": [worker["model_selector"]], "responses_endpoint_suffix": profile["responses_endpoint_suffix"], "unsupported_tool_types": profile["unsupported_tool_types"], "namespace_tool_choice_fallback": profile["tool_choice_fallback"]})
    for relative, content in generated.items(): write_text(output / relative, content)
    manifest = {"schema_version": 2, "package_version": package["package_version"], "profile": f"{profile['id']}@{profile['version']}", "codex_baseline": profile["codex_baseline"], "effective_model_identity": worker.get("effective_model_identity", "USER_MUST_VERIFY"), "files": {name: hashlib.sha256(text.encode()).hexdigest() for name, text in sorted(generated.items())}}
    write_text(output / "deployment-manifest.json", stable_json(manifest)); generated["deployment-manifest.json"] = (output / "deployment-manifest.json").read_text(encoding="utf-8")
    return generated


def remove_managed_block(text: str, package: dict) -> tuple[str, bool]:
    begin, end = markers(package); pattern = re.compile(rf"(?ms)^{re.escape(begin)}.*?^{re.escape(end)}\s*")
    return pattern.sub("", text), bool(pattern.search(text))


def check_conflicts(text: str, package: dict) -> None:
    if text.strip():
        try: tomllib.loads(text)
        except tomllib.TOMLDecodeError as error: raise PackageError(f"existing Codex config.toml is invalid: {error}") from error
    unmanaged, _ = remove_managed_block(text, package); provider = package["local_provider_id"]
    if re.search(rf"(?m)^\s*\[model_providers\.{re.escape(provider)}\]\s*$", unmanaged): raise PackageError(f"CONFLICT unmanaged provider: {provider}")
    for role in roles_from(package):
        if re.search(rf"(?m)^\s*\[agents\.{re.escape(role)}\]\s*$", unmanaged): raise PackageError(f"CONFLICT unmanaged agent: {role}")


def merge_managed_block(text: str, fragment: str, package: dict) -> str:
    check_conflicts(text, package); unmanaged, _ = remove_managed_block(text, package)
    return unmanaged.rstrip() + ("\n\n" if unmanaged.strip() else "") + fragment


def command_version(command: str) -> str | None:
    executable = shutil.which(command)
    if not executable: return None
    for args in ([executable, "--version"], [executable, "version"]):
        try:
            result = subprocess.run(args, capture_output=True, text=True, timeout=8)
            lines = (result.stdout or result.stderr).strip().splitlines()
            if lines: return lines[0][:160]
        except Exception: pass
    return "present-version-unknown"


def probe_ccr_adapter(data: dict, ccr_home: Path) -> dict:
    result = {"adapter": data["ccr"]["adapter"], "status": "FAIL", "detail": "not probed"}
    gateway = ccr_home / "gateway.config.json"
    if not gateway.is_file(): result["detail"] = "gateway.config.json missing"; return result
    try: gateway_data = json.loads(gateway.read_text(encoding="utf-8"))
    except Exception as error: result["detail"] = f"gateway parse failed: {type(error).__name__}"; return result
    if not isinstance(gateway_data.get("plugins"), list): result["detail"] = "gateway_plugin_v1 requires plugins[]"; return result
    if not shutil.which("node"): result["detail"] = "Node.js missing"; return result
    with tempfile.TemporaryDirectory(prefix="ccr-adapter-probe-") as temp:
        rendered = Path(temp); render_tree(data, rendered, Path("C:/fixture/codex-home"))
        command = ["node", str(ROOT / "scripts" / "ccr-adapter-contract.cjs"), str(ROOT / "plugins" / package_config()["plugin_id"] / "gateway-plugin.cjs"), str(rendered / "plugin-profile.json")]
        probe = subprocess.run(command, capture_output=True, text=True, timeout=15)
    if probe.returncode: result["detail"] = (probe.stderr or probe.stdout).strip()[:240]; return result
    result.update(status="PASS", detail="plugins[] parsed; executable transformRequest contract passed"); return result


def plan(data: dict) -> dict:
    package = package_config(); profile, _, _ = load_sources(data)
    codex_home, ccr_home = resolve_home(data["deployment"]["codex_home"], "codex"), resolve_home(data["deployment"]["ccr_home"], "ccr")
    config = codex_home / "config.toml"; check_conflicts(config.read_text(encoding="utf-8") if config.is_file() else "", package)
    probe = probe_ccr_adapter(data, ccr_home)
    artifacts = [codex_home / "agents" / f"{r}.toml" for r in roles_from(package)] + [codex_home / "models.worker.json"]
    assert_artifact_ownership(codex_home, artifacts)
    targets = artifacts + [config, ccr_home / "plugins" / package["plugin_id"]]
    gateway_config = ccr_home / "gateway.config.json"
    create, modify = [str(p) for p in targets if not p.exists()], [str(p) for p in targets if p.exists()]
    if gateway_config.exists(): modify.append(str(gateway_config))
    return {"detected": {"codex": command_version("codex") or "not-detected", "ccr": command_version("ccr") or "not-detected"}, "target": {"local_provider": package["local_provider_id"], "gateway": data["gateway"]["base_url"], "model_selector": data["worker"]["model_selector"], "effective_model_identity": data["worker"].get("effective_model_identity", "USER_MUST_VERIFY"), "profile": f"{profile['id']}@{profile['version']}", "ccr_adapter": data["ccr"]["adapter"]}, "will_create": create, "will_modify": modify, "will_preserve": ["root model/provider", "login/auth", "unmanaged agents", "MCP", "tools", "unrelated instructions"], "external_dependencies": ["Codex login", "CCR upstream route and credential", data["gateway"]["client_key_env"]], "restart_required": True, "compatibility_status": "VERIFIED" if probe["status"] == "PASS" else "INCOMPATIBLE", "ccr_contract": probe, "codex_home": str(codex_home), "ccr_home": str(ccr_home)}


def print_plan(value: dict) -> None: print("DEPLOYMENT PLAN\n" + stable_json(value), end="")
def plugin_registration(package: dict, target: Path) -> tuple[str, str]: return f"{package['plugin_id']}-core", str(target / "gateway-plugin.cjs")


def assert_artifact_ownership(codex_home: Path, targets: list[Path]) -> None:
    """Refuse to overwrite files not proven package-owned by the current manifest."""
    pointer = codex_home / "deployment-package-state" / "current.json"
    manifest = None
    if pointer.is_file():
        try:
            manifest_path = Path(json.loads(pointer.read_text(encoding="utf-8"))["manifest"])
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception as error:
            raise PackageError(f"package ownership manifest is unreadable: {type(error).__name__}") from error
    hashes = manifest.get("installed_hashes", {}) if manifest else {}
    for target in targets:
        if not target.exists(): continue
        expected = hashes.get(str(target))
        if not expected: raise PackageError(f"CONFLICT existing artifact is not package-owned: {target}")
        if artifact_hash(target) != expected: raise PackageError(f"CONFLICT package-owned artifact was edited: {target}")


def apply(data: dict) -> None:
    value = plan(data); print_plan(value)
    if value["ccr_contract"]["status"] != "PASS": raise PackageError("CCR adapter contract probe failed; apply refused")
    package = package_config(); codex_home, ccr_home = Path(value["codex_home"]), Path(value["ccr_home"])
    timestamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    backup_setting = data["deployment"].get("backup_root", "auto")
    revision = codex_home / "deployment-package-state" / "revisions" / timestamp if backup_setting == "auto" else Path(backup_setting).expanduser().resolve() / timestamp
    current = codex_home / "deployment-package-state" / "current.json"; previous = json.loads(current.read_text(encoding="utf-8")) if current.is_file() else None
    backup_root = revision / "backups"; created, modified, backups = [], [], {}
    managed_targets = [codex_home / "models.worker.json"] + [codex_home / "agents" / f"{r}.toml" for r in roles_from(package)]
    assert_artifact_ownership(codex_home, managed_targets)
    plugin_target = ccr_home / "plugins" / package["plugin_id"]
    if plugin_target.exists():
        try: owned = json.loads((plugin_target / "plugin.json").read_text(encoding="utf-8")).get("id") == package["plugin_id"]
        except Exception: owned = False
        if not owned: raise PackageError(f"CONFLICT plugin not package-owned: {plugin_target}")
    gateway_config = ccr_home / "gateway.config.json"; gateway_data = json.loads(gateway_config.read_text(encoding="utf-8")); plugins = gateway_data.get("plugins")
    if not isinstance(plugins, list): raise PackageError("gateway_plugin_v1 plugins[] missing")
    plugin_key, module_path = plugin_registration(package, plugin_target); entry = next((x for x in plugins if isinstance(x, dict) and x.get("key") == plugin_key), None)
    if entry and entry.get("modulePath") != module_path: raise PackageError(f"CONFLICT plugin key: {plugin_key}")
    def backup(target: Path, relative: Path) -> None:
        destination = backup_root / relative; destination.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(target, destination)
        backups[str(target)] = str(destination); modified.append(str(target))
    with tempfile.TemporaryDirectory(prefix="worker-pool-render-") as temp:
        rendered = Path(temp); render_tree(data, rendered, codex_home)
        targets = [(rendered / "models.worker.json", codex_home / "models.worker.json")] + [(rendered / "agents" / f"{r}.toml", codex_home / "agents" / f"{r}.toml") for r in roles_from(package)]
        for source, target in targets:
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists(): backup(target, target.relative_to(codex_home))
            else: created.append(str(target))
            shutil.copy2(source, target)
        config = codex_home / "config.toml"; old = config.read_text(encoding="utf-8") if config.exists() else ""
        if config.exists(): backup(config, Path("config.toml"))
        else: created.append(str(config))
        write_text(config, merge_managed_block(old, (rendered / "config.fragment.toml").read_text(encoding="utf-8"), package))
        if plugin_target.exists():
            destination = backup_root / "ccr-plugin" / plugin_target.name; destination.parent.mkdir(parents=True, exist_ok=True); shutil.copytree(plugin_target, destination)
            backups[str(plugin_target)] = str(destination); modified.append(str(plugin_target)); shutil.rmtree(plugin_target)
        else: created.append(str(plugin_target))
        plugin_target.parent.mkdir(parents=True, exist_ok=True); shutil.copytree(ROOT / "plugins" / package["plugin_id"], plugin_target); shutil.copy2(rendered / "plugin-profile.json", plugin_target / "capability-profile.json")
        backup(gateway_config, Path("ccr") / "gateway.config.json")
        if entry: entry.update({"enabled": True, "modulePath": module_path})
        else: plugins.append({"enabled": True, "key": plugin_key, "modulePath": module_path})
        write_text(gateway_config, stable_json(gateway_data))
    hashes = {item: artifact_hash(Path(item)) for item in created + modified if Path(item).exists()}
    manifest = {"schema_version": 2, "package_version": package["package_version"], "timestamp": timestamp, "created": created, "modified": modified, "backups": backups, "installed_hashes": hashes, "previous_current": previous}
    write_text(revision / "revision-manifest.json", stable_json(manifest)); write_text(current, stable_json({"revision": timestamp, "manifest": str(revision / "revision-manifest.json")}))
    print(f"APPLIED revision={timestamp}; restart Codex and CCR")


def latest_manifest(codex_home: Path) -> tuple[Path, dict]:
    current = codex_home / "deployment-package-state" / "current.json"
    if not current.is_file(): raise PackageError("no package-managed deployment")
    path = Path(json.loads(current.read_text(encoding="utf-8"))["manifest"]); return path, json.loads(path.read_text(encoding="utf-8"))


def rollback(data: dict) -> None:
    codex_home = resolve_home(data["deployment"]["codex_home"], "codex"); manifest_path, manifest = latest_manifest(codex_home)
    for item in manifest["created"] + manifest["modified"]:
        path, expected = Path(item), manifest["installed_hashes"].get(item)
        if path.exists() and expected and artifact_hash(path) != expected: raise PackageError(f"refusing rollback; changed: {path}")
    for original, saved in manifest["backups"].items():
        target, source = Path(original), Path(saved); target.parent.mkdir(parents=True, exist_ok=True)
        if source.is_dir():
            if target.exists(): shutil.rmtree(target)
            shutil.copytree(source, target)
        else: shutil.copy2(source, target)
    plugin_id = package_config()["plugin_id"]
    for item in sorted(manifest["created"], key=len, reverse=True):
        path = Path(item)
        if path.is_file(): path.unlink()
        elif path.is_dir() and path.name == plugin_id: shutil.rmtree(path)
    current = codex_home / "deployment-package-state" / "current.json"
    if manifest.get("previous_current"): write_text(current, stable_json(manifest["previous_current"]))
    else: current.unlink(missing_ok=True)
    print(f"ROLLED BACK {manifest_path.parent.name}")


def uninstall(data: dict) -> None:
    package = package_config(); codex_home = resolve_home(data["deployment"]["codex_home"], "codex"); _, manifest = latest_manifest(codex_home)
    config, ccr_home = codex_home / "config.toml", resolve_home(data["deployment"]["ccr_home"], "ccr")
    created_set = set(manifest["created"])
    if config.is_file():
        cleaned, found = remove_managed_block(config.read_text(encoding="utf-8"), package)
        if not found: raise PackageError("managed marker missing; uninstall refused")
        if str(config) in created_set and not cleaned.strip(): config.unlink()
        else: write_text(config, cleaned.rstrip() + "\n")
    gateway = ccr_home / "gateway.config.json"; plugin_target = ccr_home / "plugins" / package["plugin_id"]; plugin_key, module_path = plugin_registration(package, plugin_target)
    for item in manifest["created"] + manifest["modified"]:
        path = Path(item)
        if path == gateway and path.is_file():
            expected = manifest["installed_hashes"].get(item)
            if expected and artifact_hash(path) != expected: raise PackageError(f"CCR config changed: {path}")
            value = json.loads(path.read_text(encoding="utf-8")); value["plugins"] = [x for x in value.get("plugins", []) if not (isinstance(x, dict) and x.get("key") == plugin_key and x.get("modulePath") == module_path)]; write_text(path, stable_json(value)); continue
        if path == config or not path.exists(): continue
        expected = manifest["installed_hashes"].get(item)
        if not expected or artifact_hash(path) != expected: raise PackageError(f"managed artifact changed: {path}")
        if item in created_set:
            if path.is_file(): path.unlink()
            elif path.is_dir() and path.name == package["plugin_id"]: shutil.rmtree(path)
            else: raise PackageError(f"refusing to delete unexpected artifact type: {path}")
        else:
            saved = manifest["backups"].get(item)
            if not saved: raise PackageError(f"backup missing for modified artifact: {path}")
            source = Path(saved)
            if source.is_dir():
                shutil.rmtree(path); shutil.copytree(source, path)
            else: shutil.copy2(source, path)
    (codex_home / "deployment-package-state" / "current.json").unlink(missing_ok=True)
    print("UNINSTALLED package-owned artifacts only")


def secret_scan() -> list[str]:
    patterns = [line.strip() for line in (ROOT / "publish-allowlist.txt").read_text(encoding="utf-8").splitlines() if line.strip() and not line.startswith("#")]
    regexes = [("OpenAI-shaped secret", re.compile(r"(?<![A-Za-z0-9])sk-[A-Za-z0-9_-]{16,}")), ("Bearer value", re.compile(r"(?i)Bearer\s+[A-Za-z0-9._~+/=-]{12,}")), ("credential assignment", re.compile(r"(?i)(api[_-]?key|authorization|cookie|client[_-]?key|token)\s*[=:]\s*[\"'](?!<|\$|env:)[^\"']{8,}[\"']")), ("profile credential", re.compile(r"ccr-profile-[A-Za-z0-9_-]{8,}")), ("Windows user path", re.compile(r"(?i)[A-Z]:\\Users\\(?!<|USER|username)[^\\\s]+\\"))]
    findings = []
    for path in sorted(p for p in ROOT.rglob("*") if p.is_file() and ".git" not in p.parts):
        relative = path.relative_to(ROOT).as_posix()
        if not any(fnmatch.fnmatch(relative, pattern) for pattern in patterns): findings.append(f"not in deployment allowlist: {relative}"); continue
        if path.name in FORBIDDEN_NAMES or path.suffix in {".sqlite", ".db"}: findings.append(f"forbidden file: {relative}"); continue
        try: text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError: findings.append(f"binary/non-UTF8 file: {relative}"); continue
        findings += [f"{label}: {relative}" for label, regex in regexes if regex.search(text)]
    return findings


def validate_template(profile: dict) -> None:
    model = json.loads((ROOT / "profile" / profile["id"] / profile["model_template"]).read_text(encoding="utf-8")).get("models", [None])[0]
    required = {"slug", "apply_patch_tool_type", "supports_search_tool", "web_search_tool_type", "multi_agent_version", "visibility", "supported_in_api", "priority", "truncation_policy", "support_verbosity", "experimental_supported_tools", "auto_review_model_override", "context_window", "supported_reasoning_levels", "base_instructions"}
    if not isinstance(model, dict) or required - set(model): raise PackageError("native ModelInfo baseline fields missing")
    if model["apply_patch_tool_type"] != "freeform" or model["slug"] != "__MODEL_SELECTOR__": raise PackageError("native ModelInfo baseline invalid")
    if {"supports_web_search", "supports_multi_agent", "compatibility_profile", "effective_model_identity"} & set(model): raise PackageError("obsolete/deployment-only ModelInfo fields present")


def validate() -> None:
    package = package_config()
    for path in sorted(ROOT.rglob("*.toml")): load_toml(path)
    for path in sorted(ROOT.rglob("*.json")): json.loads(path.read_text(encoding="utf-8"))
    for path in sorted(ROOT.rglob("*.cjs")):
        result = subprocess.run(["node", "--check", str(path)], capture_output=True, text=True)
        if result.returncode: raise PackageError(f"CJS syntax error: {path}")
    data = deployment(ROOT / "tests" / "fixtures" / "deployment.test.toml"); profile, roles, _ = load_sources(data); validate_template(profile)
    findings = secret_scan()
    if findings: raise PackageError("secret/allowlist scan failed:\n" + "\n".join(findings))
    with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
        one, two = Path(a), Path(b); render_tree(data, one, Path("C:/fixture/codex-home")); render_tree(data, two, Path("C:/fixture/codex-home"))
        hashes = lambda root: {p.relative_to(root).as_posix(): sha256(p) for p in root.rglob("*") if p.is_file()}
        if hashes(one) != hashes(two): raise PackageError("render not deterministic")
        fragment = (one / "config.fragment.toml").read_text(encoding="utf-8"); parsed = tomllib.loads(fragment); provider = parsed["model_providers"][package["local_provider_id"]]
        expected = {"name": "CCR Flash Worker", "base_url": "http://127.0.0.1:3456/v1", "env_key": "FIXTURE_CCR_CLIENT_KEY", "wire_api": "responses", "requires_openai_auth": False}
        if provider != expected: raise PackageError("local provider incomplete")
        for role in roles:
            value = load_toml(one / "agents" / f"{role['id']}.toml")
            if value["model_provider"] != package["local_provider_id"] or "network_access" in value: raise PackageError("role provider/network invalid")
            if value.get("sandbox_workspace_write", {}).get("network_access") is not False: raise PackageError("role network denial missing")
        once = merge_managed_block('model = "official-root"\n', fragment, package); twice = merge_managed_block(once, fragment, package)
        if once != twice or "official-root" not in twice: raise PackageError("apply idempotence/preservation failed")
    probe = probe_ccr_adapter(data, ROOT / "tests" / "fixtures")
    if probe["status"] != "PASS": raise PackageError(f"CCR contract failed: {probe['detail']}")
    print("VALIDATION PASS: sources ModelInfo provider network secrets determinism idempotence CCR contract")


def codex_contract(data: dict) -> None:
    executable = shutil.which("codex")
    if not executable: raise PackageError("Codex executable missing")
    package = package_config()
    with tempfile.TemporaryDirectory(prefix="codex-contract-home-") as temp:
        home, rendered = Path(temp), Path(temp) / "rendered"; render_tree(data, rendered, home); (home / "agents").mkdir()
        shutil.copy2(rendered / "models.worker.json", home / "models.worker.json")
        for role in roles_from(package):
            shutil.copy2(rendered / "agents" / f"{role}.toml", home / "agents" / f"{role}.toml")
        child_env = dict(os.environ); child_env["CODEX_HOME"] = str(home)
        fragment = (rendered / "config.fragment.toml").read_text(encoding="utf-8")
        # CODEX-SENSITIVE: 0.146.0 rejects --strict-config on `debug`; `--help`
        # does not load config, and `doctor` performs network checks. The offline
        # consumer contract therefore uses debug prompt-input per role, while
        # this package's exact-key allowlists reject unknown fields.
        for role in roles_from(package):
            role_config = (rendered / "agents" / f"{role}.toml").read_text(encoding="utf-8")
            write_text(home / "config.toml", role_config + "\n" + fragment)
            consumer = subprocess.run([executable, "debug", "prompt-input", "contract fixture"], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30, env=child_env)
            if consumer.returncode: raise PackageError(f"Codex role consumer contract failed ({role}): " + (consumer.stderr or consumer.stdout).strip()[:500])
        result = subprocess.run([executable, "debug", "models"], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30, env=child_env)
        if result.returncode: raise PackageError("Codex catalog contract failed: " + (result.stderr or result.stdout).strip()[:500])
        catalog = json.loads(result.stdout); models = catalog if isinstance(catalog, list) else catalog.get("models", []); selector = data["worker"]["model_selector"]
        target = next((x for x in models if x.get("slug") == selector), None)
        if not target or target.get("auto_review_model_override") != selector or target.get("apply_patch_tool_type") != "freeform": raise PackageError("Codex loaded contract differs")
    print("CODEX CONTRACT PASS: seven role configs and native model catalog loaded offline")


def doctor(data: dict, live: bool, confirm_cost: bool) -> None:
    value = plan(data); codex_home, ccr_home = Path(value["codex_home"]), Path(value["ccr_home"]); env_name = data["gateway"]["client_key_env"]
    host = data["gateway"]["base_url"].split("://", 1)[-1].split("/", 1)[0]; hostname, _, port = host.partition(":")
    try:
        with socket.create_connection((hostname, int(port or "80")), timeout=1): port_status = "reachable"
    except Exception: port_status = "not-reachable"
    package = package_config(); report = {"powershell": command_version("pwsh") or "missing", "python": command_version("python") or sys.version.split()[0], "node": command_version("node") or "missing", "codex": value["detected"]["codex"], "ccr": value["detected"]["ccr"], "ccr_version_role": "audit-only; contract decides compatibility", "ccr_port": port_status, "required_env_present": bool(os.environ.get(env_name)), "required_env_name": env_name, "model_catalog": (codex_home / "models.worker.json").is_file(), "registered_roles": all((codex_home / "agents" / f"{r}.toml").is_file() for r in roles_from(package)), "compatibility_plugin": (ccr_home / "plugins" / package["plugin_id"]).is_dir(), "ccr_contract": value["ccr_contract"], "mode": "live" if live else "offline"}
    if live:
        if not confirm_cost: raise PackageError("live mode may consume tokens; pass --confirm-cost")
        key = os.environ.get(env_name)
        if not key: raise PackageError(f"required environment variable absent: {env_name}")
        endpoint = data["gateway"]["base_url"].rstrip("/") + "/responses"; body = stable_json({"model": data["worker"]["model_selector"], "input": "Return exactly OK.", "max_output_tokens": 8, "tools": [{"type": "namespace", "name": "fixture_namespace", "tools": []}, {"type": "function", "name": "fixture_function", "description": "fixture", "parameters": {"type": "object", "properties": {}}}], "tool_choice": {"type": "namespace", "name": "fixture_namespace"}}).encode()
        request = urllib.request.Request(endpoint, data=body, method="POST", headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"})
        try:
            with urllib.request.urlopen(request, timeout=60) as response: report["live_http_status"], report["live_response_valid"] = response.status, 200 <= response.status < 300
        except urllib.error.HTTPError as error: report["live_http_status"], report["live_response_valid"] = error.code, False
        except Exception as error: report["live_error_type"], report["live_response_valid"] = type(error).__name__, False
    print(stable_json(report), end="")


def main() -> int:
    parser = argparse.ArgumentParser(); sub = parser.add_subparsers(dest="command", required=True); sub.add_parser("validate"); sub.add_parser("secret-scan")
    render = sub.add_parser("render"); render.add_argument("--deployment", type=Path, required=True); render.add_argument("--output", type=Path, required=True); render.add_argument("--codex-home", type=Path)
    for name in ("plan", "apply", "rollback", "uninstall", "doctor", "codex-contract"):
        item = sub.add_parser(name); item.add_argument("--deployment", type=Path, required=True)
        if name == "doctor": item.add_argument("--live", action="store_true"); item.add_argument("--confirm-cost", action="store_true")
    args = parser.parse_args()
    try:
        if args.command == "validate": validate()
        elif args.command == "secret-scan":
            findings = secret_scan()
            if findings: raise PackageError("secret/allowlist scan failed:\n" + "\n".join(findings))
            print("SECRET SCAN PASS")
        elif args.command == "render": render_tree(deployment(args.deployment), args.output, args.codex_home); print(f"RENDERED {args.output}")
        else:
            data = deployment(args.deployment)
            if args.command == "plan": print_plan(plan(data))
            elif args.command == "apply": apply(data)
            elif args.command == "rollback": rollback(data)
            elif args.command == "uninstall": uninstall(data)
            elif args.command == "doctor": doctor(data, args.live, args.confirm_cost)
            elif args.command == "codex-contract": codex_contract(data)
        return 0
    except (PackageError, OSError, ValueError, json.JSONDecodeError, tomllib.TOMLDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr); return 1


if __name__ == "__main__": raise SystemExit(main())
