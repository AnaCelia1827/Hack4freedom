#!/usr/bin/env python3
"""LARES Verificável: validador e projetor de status Git-native.

O utilitário usa somente a biblioteca padrão para permanecer executável no CI
antes da instalação das dependências da aplicação. Os arquivos em
``docs/controle`` são o registro; ``status.md`` é sempre uma projeção.
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
CONTROL = ROOT / "docs" / "controle"

ID_PATTERN = re.compile(r"^(?:RF|RN|RNF|CA)-\d{3}$")
SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")
HASH_PATTERN = re.compile(r"^[0-9a-f]{64}$")

WORK_STATES = {
    "CAPTURADO",
    "LASTREADO",
    "PRONTO",
    "EM_EXECUCAO",
    "EM_VERIFICACAO",
    "EM_VERIFICACAO_LOCAL",
    "BLOQUEADO",
    "EM_RISCO",
    "CANCELADO",
}
RISK_RANK = {"S0": 0, "S1": 1, "S2": 2, "S3": 3}
EVIDENCE_MODES = {"NA", "MOCK", "SANDBOX", "REAL"}
SOURCE_STATUSES = {"DRAFT", "ACTIVE", "APPROVED", "SUPERSEDED"}

SENSITIVE_PATTERNS = {
    "Nostr private key": re.compile(r"\bnsec1[023456789acdefghjklmnpqrstuvwxyz]{20,}", re.I),
    "BOLT11 invoice": re.compile(r"\bln(?:bc|tb|bcrt)[0-9a-z]{20,}", re.I),
    "credential assignment": re.compile(
        r"(?i)(?:token|secret|password|passwd|rune|macaroon)\s*[:=]\s*[\"']?[A-Za-z0-9_./+\-=]{16,}"
    ),
    "private PEM": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
}


@dataclass
class Report:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    def print(self) -> None:
        for item in self.errors:
            print(f"ERROR: {item}")
        for item in self.warnings:
            print(f"WARN: {item}")
        print(f"LARES: {len(self.errors)} erro(s), {len(self.warnings)} aviso(s)")


def read_json(path: Path, report: Report) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        report.error(f"arquivo ausente: {path.relative_to(ROOT)}")
        return None
    except json.JSONDecodeError as exc:
        report.error(f"JSON inválido em {path.relative_to(ROOT)}: {exc}")
        return None
    if not isinstance(value, dict):
        report.error(f"objeto JSON esperado em {path.relative_to(ROOT)}")
        return None
    return value


def read_collection(directory: str, report: Report) -> list[tuple[Path, dict[str, Any]]]:
    target = CONTROL / directory
    if not target.exists():
        report.error(f"diretório ausente: {target.relative_to(ROOT)}")
        return []
    result: list[tuple[Path, dict[str, Any]]] = []
    for path in sorted(target.glob("*.json")):
        value = read_json(path, report)
        if value is not None:
            result.append((path, value))
    return result


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require_fields(value: dict[str, Any], fields: Iterable[str], label: str, report: Report) -> None:
    for name in fields:
        # Uma coleção vazia pode ser semanticamente válida (por exemplo, uma
        # tarefa sem dependências). Regras que exigem coleção não vazia são
        # verificadas explicitamente no contexto correto.
        if name not in value or value[name] in (None, ""):
            report.error(f"{label}: campo obrigatório ausente ou vazio: {name}")


def duplicate_values(values: Iterable[str]) -> set[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return duplicates


def extract_requirement_ids(path: Path) -> set[str]:
    return set(re.findall(r"\b(?:RF|RNF|RN)-\d{3}\b|\bCA-\d{3}\b", path.read_text(encoding="utf-8")))


def sensitive_matches(text: str) -> list[str]:
    return [label for label, pattern in SENSITIVE_PATTERNS.items() if pattern.search(text)]


def minimum_risk(paths: Iterable[str], operations: Iterable[str], policy: dict[str, Any]) -> str:
    minimum = "S0"
    for path in paths:
        matched = False
        for rule in policy.get("path_rules", []):
            if fnmatch.fnmatch(path, rule.get("pattern", "")):
                matched = True
                candidate = rule.get("minimum_risk", "S0")
                if RISK_RANK.get(candidate, 99) > RISK_RANK[minimum]:
                    minimum = candidate
        if not matched:
            candidate = policy.get("default_unknown_risk", "S3")
            if RISK_RANK.get(candidate, 99) > RISK_RANK[minimum]:
                minimum = candidate
    normalized_operations = " ".join(operations).lower()
    for rule in policy.get("operation_rules", []):
        if any(keyword.lower() in normalized_operations for keyword in rule.get("keywords", [])):
            candidate = rule.get("minimum_risk", "S0")
            if RISK_RANK.get(candidate, 99) > RISK_RANK[minimum]:
                minimum = candidate
    return minimum


def evidence_satisfies_mode(mode: str, requirements: Iterable[str], real_only: set[str]) -> bool:
    return mode == "REAL" or not set(requirements).intersection(real_only)


def git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=ROOT, check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "git command failed")
    return result.stdout.strip()


def subject_is_current_or_control_descendant(subject_commit: str, current_commit: str) -> bool:
    """Aceita um commit verificado ou descendente que só acrescente auditoria.

    EvidenceRecord e status são criados depois do commit que foi testado. Exigir
    que ambos tenham o mesmo SHA produziria uma referência circular impossível.
    Um descendente continua válido somente quando a diferença contém arquivos
    do próprio control plane em ``docs/controle``.
    """

    if subject_commit == current_commit:
        return True
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", subject_commit, current_commit],
        cwd=ROOT,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if ancestor.returncode != 0:
        return False
    try:
        changed = git("diff", "--name-only", f"{subject_commit}..{current_commit}").splitlines()
    except RuntimeError:
        return False
    return bool(changed) and all(path.startswith("docs/controle/") for path in changed)


def workspace_fingerprint(excluded_prefixes: Iterable[str] = ()) -> str:
    """Fingerprint dos arquivos rastreados e não ignorados do workspace.

    O hash inclui caminho, conteúdo e marcadores de arquivos removidos. Registros
    de runtime podem ser excluídos pelo chamador para evitar autorreferência
    entre uma Run e o próprio hash que ela registra.
    """

    result = subprocess.run(
        ["git", "ls-files", "-c", "-m", "-o", "--exclude-standard", "-z"],
        cwd=ROOT,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode:
        raise RuntimeError(result.stderr.decode("utf-8", errors="replace").strip() or "git ls-files failed")
    prefixes = tuple(prefix.rstrip("/") + "/" for prefix in excluded_prefixes)
    paths = sorted({raw.decode("utf-8") for raw in result.stdout.split(b"\0") if raw})
    digest = hashlib.sha256()
    for relative in paths:
        if any(relative == prefix.rstrip("/") or relative.startswith(prefix) for prefix in prefixes):
            continue
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        path = ROOT / relative
        if path.is_file():
            digest.update(sha256_file(path).encode("ascii"))
        else:
            digest.update(b"MISSING")
        digest.update(b"\0")
    return digest.hexdigest()


def path_is_authorized(path: str, allowed_patterns: Iterable[str]) -> bool:
    """Verifica cobertura conservadora de um path/glob pelo envelope."""

    for pattern in allowed_patterns:
        if path == pattern or fnmatch.fnmatch(path, pattern):
            return True
        if pattern.endswith("/**") and path == pattern[:-3].rstrip("/"):
            return True
        if path.endswith("/**") and pattern.endswith("/**"):
            if path[:-3].startswith(pattern[:-3]):
                return True
    return False


def indexed_by_id(items: list[tuple[Path, dict[str, Any]]], label: str, report: Report) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for path, item in items:
        item_id = item.get("id")
        if not isinstance(item_id, str) or not item_id:
            report.error(f"{path.relative_to(ROOT)}: id ausente")
            continue
        if item_id in result:
            report.error(f"{label}: id duplicado: {item_id}")
        result[item_id] = item
    return result


def validate_repository() -> tuple[Report, dict[str, Any]]:
    report = Report()
    # Schemas e templates também fazem parte da infraestrutura. Mesmo sem uma
    # dependência externa de JSON Schema, nenhum JSON versionado pode ficar
    # sintaticamente inválido sem derrubar o gate.
    for json_path in sorted(CONTROL.rglob("*.json")):
        try:
            json.loads(json_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            report.error(f"JSON inválido em {json_path.relative_to(ROOT)}: {exc}")

    registry = read_json(CONTROL / "source-registry.json", report) or {}
    scope = read_json(CONTROL / "scope-baseline.json", report) or {}
    policy = read_json(CONTROL / "risk-policy.json", report) or {}
    risk_register = read_json(CONTROL / "risk-register.json", report) or {}

    work_items_list = read_collection("work-items", report)
    authorizations_list = read_collection("authorizations", report)
    runs_list = read_collection("runs", report)
    evidence_list = read_collection("evidence", report)
    decisions_list = read_collection("gate-decisions", report)
    challenges_list = read_collection("challenges", report)
    gates_list = read_collection("gates", report)
    divergences_list = read_collection("divergences", report)
    incidents_list = read_collection("incidents", report)
    supersessions_list = read_collection("supersessions", report)

    work_items = indexed_by_id(work_items_list, "work item", report)
    authorizations = indexed_by_id(authorizations_list, "authorization", report)
    runs = indexed_by_id(runs_list, "run", report)
    evidence = indexed_by_id(evidence_list, "evidence", report)
    decisions = indexed_by_id(decisions_list, "gate decision", report)
    challenges = indexed_by_id(challenges_list, "adversarial challenge", report)
    gates = indexed_by_id(gates_list, "gate", report)
    divergences = indexed_by_id(divergences_list, "divergence", report)
    incidents = indexed_by_id(incidents_list, "incident", report)
    supersessions = indexed_by_id(supersessions_list, "supersession", report)

    require_fields(registry, ["schema_version", "registry_version", "sources", "claims"], "source-registry", report)
    sources = {item.get("id"): item for item in registry.get("sources", []) if isinstance(item, dict)}
    claims = {item.get("id"): item for item in registry.get("claims", []) if isinstance(item, dict)}
    if len(sources) != len(registry.get("sources", [])):
        report.error("source-registry: source id ausente ou duplicado")
    if len(claims) != len(registry.get("claims", [])):
        report.error("source-registry: claim id ausente ou duplicado")

    for source_id, source in sources.items():
        require_fields(source, ["id", "title", "kind", "authority", "status"], f"source {source_id}", report)
        if source.get("status") not in SOURCE_STATUSES:
            report.error(f"source {source_id}: status inválido: {source.get('status')}")
        if source.get("kind") == "LOCAL_FILE":
            require_fields(source, ["path", "sha256"], f"source {source_id}", report)
            relative = source.get("path", "")
            target = ROOT / relative
            if not target.is_file():
                report.error(f"source {source_id}: arquivo ausente: {relative}")
            elif not HASH_PATTERN.match(str(source.get("sha256", ""))):
                report.error(f"source {source_id}: sha256 inválido")
            else:
                actual = sha256_file(target)
                if actual != source["sha256"]:
                    report.error(f"source {source_id}: drift detectado em {relative}; esperado {source['sha256']}, atual {actual}")
        elif source.get("kind") == "EXTERNAL_REFERENCE":
            require_fields(source, ["url", "inspection_policy"], f"source {source_id}", report)

    for claim_id, claim in claims.items():
        require_fields(claim, ["id", "statement", "type", "source_id", "status"], f"claim {claim_id}", report)
        if claim.get("source_id") not in sources:
            report.error(f"claim {claim_id}: source inexistente: {claim.get('source_id')}")

    require_fields(
        scope,
        ["id", "release", "as_of", "requirements_source", "required_requirements", "golden_path", "release_gates"],
        "scope-baseline",
        report,
    )
    requirements_source = sources.get(scope.get("requirements_source"), {})
    requirements_path = ROOT / requirements_source.get("path", "missing")
    available_ids = extract_requirement_ids(requirements_path) if requirements_path.is_file() else set()
    required_ids = scope.get("required_requirements", [])
    if duplicate_values(required_ids):
        report.error(f"scope-baseline: requisitos duplicados: {sorted(duplicate_values(required_ids))}")
    for requirement_id in required_ids:
        if not ID_PATTERN.match(requirement_id):
            report.error(f"scope-baseline: id inválido: {requirement_id}")
        elif requirement_id not in available_ids:
            report.error(f"scope-baseline: id inexistente em requisitos.md: {requirement_id}")
    golden_steps = [item.get("step") for item in scope.get("golden_path", []) if isinstance(item, dict)]
    if golden_steps != list(range(1, 18)):
        report.error("scope-baseline: golden path deve conter exatamente os passos 1 a 17, em ordem")

    require_fields(policy, ["schema_version", "path_rules", "operation_rules", "approval_matrix"], "risk-policy", report)
    require_fields(risk_register, ["schema_version", "id", "as_of", "risks"], "risk-register", report)

    for authorization_id, authorization in authorizations.items():
        require_fields(
            authorization,
            [
                "id",
                "risk_class",
                "granted_by",
                "approval_basis",
                "repository",
                "base_commit",
                "allowed_paths",
                "allowed_operations",
                "denied_operations",
                "environment",
                "external_side_effects",
                "expires_at",
                "assurance",
            ],
            f"authorization {authorization_id}",
            report,
        )
        if authorization.get("risk_class") not in RISK_RANK:
            report.error(f"authorization {authorization_id}: classe de risco inválida")
        if not SHA_PATTERN.match(str(authorization.get("base_commit", ""))):
            report.error(f"authorization {authorization_id}: base_commit deve ser SHA completo")
        if authorization.get("risk_class") == "S3":
            if authorization.get("assurance") not in {"SIGNED", "PLATFORM_VERIFIED"}:
                report.error(f"authorization {authorization_id}: S3 exige aprovação verificável")
            if authorization.get("max_total_sats") is None:
                report.error(f"authorization {authorization_id}: S3 exige max_total_sats")
            if authorization.get("single_use") is not True:
                report.error(f"authorization {authorization_id}: S3 deve ser single_use")
        try:
            datetime.fromisoformat(str(authorization.get("expires_at", "")).replace("Z", "+00:00"))
        except ValueError:
            report.error(f"authorization {authorization_id}: expires_at inválido")

    all_evidence_requirements: dict[str, list[str]] = {}
    for evidence_id, item in evidence.items():
        require_fields(
            item,
            [
                "id",
                "work_item_id",
                "run_id",
                "title",
                "producer",
                "verifier",
                "subject_commit",
                "workspace_tree_hash",
                "environment",
                "classification",
                "claims",
                "limitations",
            ],
            f"evidence {evidence_id}",
            report,
        )
        if item.get("work_item_id") not in work_items:
            report.error(f"evidence {evidence_id}: work item inexistente")
        if item.get("run_id") not in runs:
            report.error(f"evidence {evidence_id}: run inexistente")
        if not SHA_PATTERN.match(str(item.get("subject_commit", ""))):
            report.error(f"evidence {evidence_id}: subject_commit inválido")
        if not HASH_PATTERN.match(str(item.get("workspace_tree_hash", ""))):
            report.error(f"evidence {evidence_id}: workspace_tree_hash inválido")
        if not HASH_PATTERN.match(str(item.get("artifact_hash", ""))):
            report.error(f"evidence {evidence_id}: artifact_hash inválido")
        elif any(
            artifact.get("reference") == item.get("run_id")
            for artifact in item.get("artifacts", [])
            if isinstance(artifact, dict)
        ):
            run_path = CONTROL / "runs" / f"{item.get('run_id')}.json"
            if run_path.is_file() and sha256_file(run_path) != item.get("artifact_hash"):
                report.error(f"evidence {evidence_id}: artifact_hash não corresponde ao RunManifest")
        environment = item.get("environment", {})
        mode = environment.get("mode") if isinstance(environment, dict) else None
        if mode not in EVIDENCE_MODES:
            report.error(f"evidence {evidence_id}: environment.mode inválido: {mode}")
        if item.get("classification") in {"SECRET", "FINANCIAL_RAW"}:
            report.error(f"evidence {evidence_id}: conteúdo sensível não pode ser armazenado no Git")
        matches = sensitive_matches(json.dumps(item, ensure_ascii=False))
        if matches:
            report.error(f"evidence {evidence_id}: padrão sensível detectado: {', '.join(matches)}")
        requirements = [value for value in item.get("claims", []) if ID_PATTERN.match(value)]
        all_evidence_requirements[evidence_id] = requirements
        real_only = set(scope.get("real_only_requirements", []))
        if not evidence_satisfies_mode(str(mode), requirements, real_only):
            report.error(f"evidence {evidence_id}: modo {mode} não satisfaz requisito REAL")

    for run_id, run in runs.items():
        require_fields(
            run,
            [
                "id",
                "work_item_id",
                "authorization_id",
                "started_at",
                "source_commit",
                "workspace_clean",
                "workspace_tree_hash",
                "commands",
                "result",
                "changed_paths",
            ],
            f"run {run_id}",
            report,
        )
        if run.get("work_item_id") not in work_items:
            report.error(f"run {run_id}: work item inexistente")
        if run.get("authorization_id") not in authorizations:
            report.error(f"run {run_id}: authorization inexistente")
        if not SHA_PATTERN.match(str(run.get("source_commit", ""))):
            report.error(f"run {run_id}: source_commit inválido")
        result_commit = run.get("result_commit")
        if result_commit is not None and not SHA_PATTERN.match(str(result_commit)):
            report.error(f"run {run_id}: result_commit inválido")
        if not HASH_PATTERN.match(str(run.get("workspace_tree_hash", ""))):
            report.error(f"run {run_id}: workspace_tree_hash inválido")
        if run.get("patch_hash") and not HASH_PATTERN.match(str(run.get("patch_hash", ""))):
            report.error(f"run {run_id}: patch_hash inválido")
        if run.get("workspace_clean") is False and run.get("result") == "PASS":
            report.error(f"run {run_id}: workspace sujo não pode declarar PASS reproduzível")
        authorization = authorizations.get(run.get("authorization_id"), {})
        if authorization:
            if run.get("source_commit") != authorization.get("base_commit"):
                report.error(f"run {run_id}: source_commit diverge do base_commit autorizado")
            for changed_path in run.get("changed_paths", []):
                if not path_is_authorized(changed_path, authorization.get("allowed_paths", [])):
                    report.error(f"run {run_id}: path alterado fora do envelope: {changed_path}")
            commands = " ".join(run.get("commands", [])).lower()
            for denied in authorization.get("denied_operations", []):
                if denied.lower() in commands:
                    report.error(f"run {run_id}: comando contém operação negada: {denied}")

    for evidence_id, item in evidence.items():
        run = runs.get(item.get("run_id"), {})
        if run:
            if item.get("work_item_id") != run.get("work_item_id"):
                report.error(f"evidence {evidence_id}: work item diverge da run")
            expected_subject = run.get("result_commit") or run.get("source_commit")
            if item.get("subject_commit") != expected_subject:
                report.error(f"evidence {evidence_id}: subject_commit diverge da run")
            if item.get("workspace_tree_hash") != run.get("workspace_tree_hash"):
                report.error(f"evidence {evidence_id}: workspace_tree_hash diverge da run")

    for work_item_id, item in work_items.items():
        require_fields(
            item,
            [
                "id",
                "title",
                "objective",
                "state",
                "risk_class",
                "source_claims",
                "requirements",
                "dependencies",
                "affected_paths",
                "operations",
                "acceptance_criteria",
                "refutation_conditions",
                "recovery_strategy",
            ],
            f"work item {work_item_id}",
            report,
        )
        if item.get("state") not in WORK_STATES:
            report.error(f"work item {work_item_id}: state inválido: {item.get('state')}")
        risk = item.get("risk_class")
        if risk not in RISK_RANK:
            report.error(f"work item {work_item_id}: risk_class inválida")
        else:
            required_risk = minimum_risk(item.get("affected_paths", []), item.get("operations", []), policy)
            if RISK_RANK[risk] < RISK_RANK[required_risk]:
                report.error(f"work item {work_item_id}: risco {risk} abaixo do mínimo derivado {required_risk}")
        for claim_id in item.get("source_claims", []):
            if claim_id not in claims:
                report.error(f"work item {work_item_id}: claim inexistente: {claim_id}")
        for requirement_id in item.get("requirements", []):
            if requirement_id not in available_ids:
                report.error(f"work item {work_item_id}: requisito inexistente: {requirement_id}")
        for dependency_id in item.get("dependencies", []):
            if dependency_id not in work_items:
                report.error(f"work item {work_item_id}: dependência inexistente: {dependency_id}")
        authorization_id = item.get("authorization_id")
        if authorization_id and authorization_id not in authorizations:
            report.error(f"work item {work_item_id}: authorization inexistente: {authorization_id}")
        if item.get("state") in {"EM_EXECUCAO", "EM_VERIFICACAO", "EM_VERIFICACAO_LOCAL"}:
            if not authorization_id:
                report.error(f"work item {work_item_id}: execução/verificação exige authorization_id")
            else:
                authorization = authorizations.get(authorization_id, {})
                if RISK_RANK.get(authorization.get("risk_class"), -1) < RISK_RANK.get(risk, 99):
                    report.error(
                        f"work item {work_item_id}: autorização {authorization_id} tem risco inferior ao Work Item"
                    )
                for affected_path in item.get("affected_paths", []):
                    if not path_is_authorized(affected_path, authorization.get("allowed_paths", [])):
                        report.error(
                            f"work item {work_item_id}: path fora do envelope {authorization_id}: {affected_path}"
                        )
                operations = " ".join(item.get("operations", [])).lower()
                for denied in authorization.get("denied_operations", []):
                    if denied.lower() in operations:
                        report.error(f"work item {work_item_id}: operação negada pelo envelope: {denied}")
        for evidence_id in item.get("evidence_ids", []):
            if evidence_id not in evidence:
                report.error(f"work item {work_item_id}: evidence inexistente: {evidence_id}")

    for challenge_id, challenge in challenges.items():
        require_fields(
            challenge,
            [
                "id",
                "work_item_id",
                "run_id",
                "status",
                "challengers",
                "attacks",
                "verdict",
                "created_at",
            ],
            f"adversarial challenge {challenge_id}",
            report,
        )
        if challenge.get("work_item_id") not in work_items:
            report.error(f"adversarial challenge {challenge_id}: work item inexistente")
        if challenge.get("run_id") not in runs:
            report.error(f"adversarial challenge {challenge_id}: run inexistente")
        if challenge.get("status") == "COMPLETE" and not challenge.get("attacks"):
            report.error(f"adversarial challenge {challenge_id}: COMPLETE exige ataques registrados")
        if len(set(challenge.get("challengers", []))) != len(challenge.get("challengers", [])):
            report.error(f"adversarial challenge {challenge_id}: challengers duplicados")
        for index, attack in enumerate(challenge.get("attacks", []), start=1):
            require_fields(
                attack,
                ["title", "attack", "expected_failure", "mitigation", "verification"],
                f"adversarial challenge {challenge_id}/attack-{index}",
                report,
            )

    for decision_id, decision in decisions.items():
        require_fields(
            decision,
            ["id", "work_item_id", "decision", "subject_commit", "evidence_ids", "decided_by", "decided_at"],
            f"gate decision {decision_id}",
            report,
        )
        work_item = work_items.get(decision.get("work_item_id"))
        if not SHA_PATTERN.match(str(decision.get("subject_commit", ""))):
            report.error(f"gate decision {decision_id}: subject_commit inválido")
        if not work_item:
            report.error(f"gate decision {decision_id}: work item inexistente")
            continue
        evidence_ids = decision.get("evidence_ids", [])
        if decision.get("decision") == "ACCEPT" and not evidence_ids:
            report.error(f"gate decision {decision_id}: ACCEPT exige evidências")
        for evidence_id in evidence_ids:
            item = evidence.get(evidence_id)
            if not item:
                report.error(f"gate decision {decision_id}: evidence inexistente: {evidence_id}")
                continue
            if item.get("subject_commit") != decision.get("subject_commit"):
                report.error(f"gate decision {decision_id}: evidence e decisão usam commits diferentes")
            if work_item.get("risk_class") in {"S2", "S3"} and item.get("producer") == item.get("verifier"):
                report.error(f"gate decision {decision_id}: {work_item.get('risk_class')} exige verificador independente")
            if work_item.get("risk_class") in {"S2", "S3"} and decision.get("decided_by") == item.get("producer"):
                report.error(f"gate decision {decision_id}: executor não pode decidir aceite {work_item.get('risk_class')}")
            run = runs.get(item.get("run_id"), {})
            if decision.get("decision") == "ACCEPT" and run.get("workspace_clean") is not True:
                report.error(f"gate decision {decision_id}: ACCEPT exige run reproduzível em workspace limpo")
        if work_item.get("risk_class") in {"S2", "S3"} and decision.get("decision") == "ACCEPT":
            challenge_ids = decision.get("challenge_ids", [])
            if not challenge_ids:
                report.error(f"gate decision {decision_id}: {work_item.get('risk_class')} exige challenge adversarial")
            for challenge_id in challenge_ids:
                challenge = challenges.get(challenge_id)
                if not challenge:
                    report.error(f"gate decision {decision_id}: challenge inexistente: {challenge_id}")
                elif challenge.get("work_item_id") != decision.get("work_item_id"):
                    report.error(f"gate decision {decision_id}: challenge pertence a outro Work Item")
                elif challenge.get("status") != "COMPLETE":
                    report.error(f"gate decision {decision_id}: challenge não está COMPLETE")
        if work_item.get("risk_class") == "S3" and decision.get("decision") == "ACCEPT":
            first = decision.get("human_approver")
            second = decision.get("second_human_approver")
            if not first or not second or first == second:
                report.error(f"gate decision {decision_id}: S3 exige dois aprovadores humanos distintos")

    for gate_id, gate in gates.items():
        require_fields(gate, ["id", "type", "title", "release", "decision_policy"], f"gate {gate_id}", report)
        for requirement_id in gate.get("required_requirements", []):
            if requirement_id not in available_ids:
                report.error(f"gate {gate_id}: requisito inexistente: {requirement_id}")
        for step in gate.get("steps", []):
            for requirement_id in step.get("requirements", []):
                if requirement_id not in available_ids:
                    report.error(f"gate {gate_id}/{step.get('id')}: requisito inexistente: {requirement_id}")
            for evidence_id in step.get("evidence_ids", []):
                if evidence_id not in evidence:
                    report.error(f"gate {gate_id}/{step.get('id')}: evidence inexistente: {evidence_id}")
            if step.get("evidence_ids"):
                status, complete, _ = gate_status({"steps": [step]}, evidence)
                if not status.startswith("ACEITO_NO_COMMIT") or complete != 1:
                    report.error(f"gate {gate_id}/{step.get('id')}: evidência não cobre claim, modo ou commit exigido")

    for divergence_id, divergence in divergences.items():
        require_fields(
            divergence,
            ["id", "title", "status", "sources", "summary", "impact", "blocks_release", "next_action"],
            f"divergence {divergence_id}",
            report,
        )
        for source_id in divergence.get("sources", []):
            if source_id not in sources:
                report.error(f"divergence {divergence_id}: source inexistente: {source_id}")

    for incident_id, incident in incidents.items():
        require_fields(
            incident,
            ["id", "severity", "status", "detected_at", "summary", "affected_work_items", "containment", "recovery_type", "owner"],
            f"incident {incident_id}",
            report,
        )
        for work_item_id in incident.get("affected_work_items", []):
            if work_item_id not in work_items:
                report.error(f"incident {incident_id}: work item inexistente: {work_item_id}")

    known_record_ids = set(evidence) | set(decisions) | set(authorizations) | set(runs)
    for supersession_id, supersession in supersessions.items():
        require_fields(
            supersession,
            ["id", "record_type", "superseded_id", "replacement_id", "reason", "created_by", "created_at"],
            f"supersession {supersession_id}",
            report,
        )
        if supersession.get("superseded_id") not in known_record_ids:
            report.error(f"supersession {supersession_id}: registro substituído inexistente")
        if supersession.get("replacement_id") not in known_record_ids:
            report.error(f"supersession {supersession_id}: registro substituto inexistente")

    covered = {req for item in work_items.values() for req in item.get("requirements", [])}
    uncovered = sorted(set(required_ids) - covered)
    if uncovered:
        report.warn(f"escopo possui {len(uncovered)} requisito(s) sem Work Item; release permanece não pronta")

    for release_gate in scope.get("release_gates", []):
        if release_gate not in gates:
            report.error(f"scope-baseline: release gate inexistente: {release_gate}")

    return report, {
        "registry": registry,
        "scope": scope,
        "policy": policy,
        "sources": sources,
        "claims": claims,
        "work_items": work_items,
        "authorizations": authorizations,
        "runs": runs,
        "evidence": evidence,
        "decisions": decisions,
        "challenges": challenges,
        "gates": gates,
        "divergences": divergences,
        "incidents": incidents,
        "supersessions": supersessions,
        "available_requirements": available_ids,
    }


def effective_work_status(work_item_id: str, item: dict[str, Any], decisions: dict[str, dict[str, Any]]) -> str:
    accepted = [
        decision
        for decision in decisions.values()
        if decision.get("work_item_id") == work_item_id and decision.get("decision") == "ACCEPT"
    ]
    if accepted:
        subject = sorted(accepted, key=lambda value: value.get("decided_at", ""))[-1].get("subject_commit", "")
        return f"ACEITO_NO_COMMIT {subject[:12]}"
    return item.get("state", "CAPTURADO")


def gate_status(
    gate: dict[str, Any], evidence: dict[str, dict[str, Any]], current_commit: str | None = None
) -> tuple[str, int, int]:
    steps = gate.get("steps", [])
    if not steps:
        return "NAO_PRONTO", 0, 0
    complete = 0
    gate_commits: set[str] = set()
    for step in steps:
        ids = step.get("evidence_ids", [])
        if not ids or not all(item in evidence for item in ids):
            continue
        records = [evidence[item] for item in ids]
        claims = {claim for record in records for claim in record.get("claims", [])}
        if not set(step.get("requirements", [])).issubset(claims):
            continue
        required_mode = step.get("required_mode")
        if required_mode and not all(record.get("environment", {}).get("mode") == required_mode for record in records):
            continue
        commits = {record.get("subject_commit") for record in records}
        if len(commits) != 1:
            continue
        gate_commits.update(commit for commit in commits if isinstance(commit, str))
        complete += 1
    if complete != len(steps) or len(gate_commits) != 1:
        return "NAO_PRONTO", complete, len(steps)
    subject_commit = next(iter(gate_commits))
    if current_commit is not None and not subject_is_current_or_control_descendant(subject_commit, current_commit):
        return "REVALIDACAO_NECESSARIA", complete, len(steps)
    return f"ACEITO_NO_COMMIT {subject_commit[:12]}", complete, len(steps)


def render_status(context: dict[str, Any]) -> str:
    scope = context["scope"]
    work_items = context["work_items"]
    decisions = context["decisions"]
    evidence = context["evidence"]
    divergences = context["divergences"]
    gates = context["gates"]
    required = set(scope.get("required_requirements", []))
    covered = {req for item in work_items.values() for req in item.get("requirements", [])}
    blocking = [item for item in divergences.values() if item.get("status") == "OPEN" and item.get("blocks_release")]

    gate_rows: list[str] = []
    all_release_gates_ready = True
    try:
        current_commit = git("rev-parse", "HEAD")
    except RuntimeError:
        current_commit = None
    for gate_id in scope.get("release_gates", []):
        status, complete, total = gate_status(gates.get(gate_id, {}), evidence, current_commit)
        all_release_gates_ready = all_release_gates_ready and status.startswith("ACEITO_NO_COMMIT")
        gate_rows.append(f"| `{gate_id}` | {status} | {complete}/{total} |")

    release_ready = all_release_gates_ready and not blocking and required.issubset(covered)
    lines = [
        "# Status verificável do Bluejet",
        "",
        "> Este arquivo é gerado por `python tools/lares/lares.py status --write`.",
        "> Não o edite manualmente.",
        "",
        f"- Baseline: `{scope.get('id', 'unknown')}`",
        f"- Data de corte do baseline: `{scope.get('as_of', 'unknown')}`",
        f"- Release: `{scope.get('release', 'unknown')}`",
        f"- Pronta para release: `{'SIM' if release_ready else 'NÃO'}`",
        f"- Cobertura lastreada: `{len(required.intersection(covered))}/{len(required)}` requisitos obrigatórios",
        f"- Divergências bloqueantes abertas: `{len(blocking)}`",
        "",
        "## Work Items",
        "",
        "| Work Item | Estado verificável | Risco | Requisitos |",
        "| --- | --- | --- | --- |",
    ]
    for work_item_id, item in sorted(work_items.items()):
        requirements = ", ".join(item.get("requirements", [])) or "—"
        lines.append(
            f"| `{work_item_id}` — {item.get('title', '')} | {effective_work_status(work_item_id, item, decisions)} | {item.get('risk_class', '')} | {requirements} |"
        )

    lines.extend(
        [
            "",
            "## Gates da release",
            "",
            "| Gate | Estado | Evidências/etapas |",
            "| --- | --- | --- |",
            *gate_rows,
            "",
            "## Divergências bloqueantes",
            "",
        ]
    )
    if blocking:
        for item in sorted(blocking, key=lambda value: value.get("id", "")):
            lines.append(f"- `{item['id']}` — {item['title']}: {item['next_action']}")
    else:
        lines.append("- Nenhuma.")

    uncovered = sorted(required - covered)
    lines.extend(["", "## Requisitos ainda sem Work Item", ""])
    if uncovered:
        lines.append(", ".join(f"`{item}`" for item in uncovered))
    else:
        lines.append("Todos os requisitos do baseline possuem Work Item.")
    lines.append("")
    return "\n".join(lines)


def doctor(strict: bool) -> int:
    try:
        head = git("rev-parse", "HEAD")
        branch = git("branch", "--show-current") or "DETACHED"
        status = git("status", "--porcelain=v2")
        remote_counts = git("rev-list", "--left-right", "--count", "HEAD...origin/main")
    except RuntimeError as exc:
        print(f"ERROR: {exc}")
        return 2
    dirty = bool(status)
    print(f"root={ROOT}")
    print(f"branch={branch}")
    print(f"head={head}")
    print(f"workspace_clean={'true' if not dirty else 'false'}")
    print(f"head_vs_origin_main={remote_counts}")
    if dirty:
        print("WARN: workspace sujo; aceite reproduzível está proibido")
    return 1 if strict and dirty else 0


def meta_test() -> int:
    failures: list[str] = []

    sample_policy = {
        "path_rules": [{"pattern": "**/payments/**", "minimum_risk": "S2"}],
        "operation_rules": [{"keywords": ["xpay"], "minimum_risk": "S3"}],
    }
    if minimum_risk(["apps/api/payments/service.py"], [], sample_policy) != "S2":
        failures.append("path financeiro não elevou risco para S2")
    if minimum_risk([], ["executar xpay"], sample_policy) != "S3":
        failures.append("xpay não elevou risco para S3")
    if evidence_satisfies_mode("MOCK", ["CA-005"], {"CA-005"}):
        failures.append("MOCK satisfez requisito REAL")
    if not sensitive_matches("invoice lnbc1qqqqqqqqqqqqqqqqqqqqqqqqqq"):
        failures.append("scanner não detectou BOLT11")
    if sensitive_matches("payment_hash truncado: a1b2c3d4"):
        failures.append("scanner produziu falso positivo básico")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print("LARES meta-tests: PASS")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="LARES Verificável")
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate_parser = subparsers.add_parser("validate", help="validar registros e políticas")
    validate_parser.add_argument("--strict", action="store_true", help="tratar avisos como erro")
    status_parser = subparsers.add_parser("status", help="gerar ou verificar status.md")
    status_mode = status_parser.add_mutually_exclusive_group(required=True)
    status_mode.add_argument("--write", action="store_true")
    status_mode.add_argument("--check", action="store_true")
    doctor_parser = subparsers.add_parser("doctor", help="inspecionar Git e reprodutibilidade")
    doctor_parser.add_argument("--strict", action="store_true")
    fingerprint_parser = subparsers.add_parser("fingerprint", help="calcular sha256 de fontes")
    fingerprint_parser.add_argument("paths", nargs="+")
    workspace_parser = subparsers.add_parser("workspace-fingerprint", help="calcular hash determinístico do workspace")
    workspace_parser.add_argument("--exclude", action="append", default=[], help="prefixo a excluir; pode repetir")
    subparsers.add_parser("meta-test", help="executar ataques mínimos ao próprio protocolo")
    args = parser.parse_args()

    if args.command == "doctor":
        return doctor(args.strict)
    if args.command == "fingerprint":
        for raw_path in args.paths:
            path = ROOT / raw_path
            if not path.is_file():
                print(f"ERROR: arquivo ausente: {raw_path}")
                return 2
            print(f"{sha256_file(path)}  {raw_path}")
        return 0
    if args.command == "workspace-fingerprint":
        try:
            print(workspace_fingerprint(args.exclude))
        except RuntimeError as exc:
            print(f"ERROR: {exc}")
            return 2
        return 0
    if args.command == "meta-test":
        return meta_test()

    report, context = validate_repository()
    if args.command == "validate":
        report.print()
        return 1 if report.errors or (args.strict and report.warnings) else 0

    if report.errors:
        report.print()
        return 1
    rendered = render_status(context)
    target = CONTROL / "status.md"
    if args.write:
        target.write_text(rendered, encoding="utf-8")
        print(f"WROTE: {target.relative_to(ROOT)}")
        return 0
    current = target.read_text(encoding="utf-8") if target.exists() else ""
    if current != rendered:
        print("ERROR: docs/controle/status.md está desatualizado; execute status --write")
        return 1
    print("LARES status projection: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
