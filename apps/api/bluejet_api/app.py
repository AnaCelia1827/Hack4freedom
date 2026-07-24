from flask import Flask, jsonify
from flask import request
import uuid

from .config import Config, validate_config
from .auth import AuthorizationDenied, Bip340NostrEventVerifier, NostrAuth
from .learning import LearningService
from .work import WorkService
from .finance import FinanceService, SandboxLightningGateway
from .community import CommunityService
from .database import ActivePayoutAttempt, AssignmentUnavailable, DatabaseManager, IdempotencyConflict, ObligationNotOpen, OnboardingIncomplete, ReviewConflict
from .observability import configure_logging


def create_app(config_object: type[Config] = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_object)
    validate_config(app.config)
    configure_logging(app)
    database = (
        DatabaseManager(app.config["DATABASE_URL"], app.config["DATABASE_LOCK_TIMEOUT_MS"])
        if app.config.get("DATABASE_URL")
        else None
    )
    rbac_store = app.config.get("RBAC_STORE") or database
    persistent_community = database is not None and app.config.get("RBAC_STORE") is None
    auth = NostrAuth(
        store=app.config.get("AUTH_STORE") or database,
        verifier=app.config.get("AUTH_VERIFIER")
        or Bip340NostrEventVerifier(app.config["NOSTR_MAX_CLOCK_SKEW_SECONDS"]),
        max_attempts_per_challenge=app.config["NOSTR_MAX_AUTH_ATTEMPTS"],
        expected_url=app.config["NOSTR_AUTH_AUDIENCE"],
    )

    def administrative_pubkey_authorized(pubkey: str) -> bool:
        if rbac_store:
            return rbac_store.has_any_role(pubkey, {"ADMIN", "REVIEWER"})
        return pubkey in app.config.get("ADMIN_PUBKEYS", set())

    admin_auth = NostrAuth(
        store=app.config.get("AUTH_STORE") or database,
        verifier=app.config.get("AUTH_VERIFIER")
        or Bip340NostrEventVerifier(app.config["NOSTR_MAX_CLOCK_SKEW_SECONDS"]),
        max_attempts_per_challenge=app.config["NOSTR_MAX_AUTH_ATTEMPTS"],
        expected_url=app.config["ADMIN_NOSTR_AUTH_AUDIENCE"],
        session_scope="ADMIN",
        pubkey_authorizer=administrative_pubkey_authorized,
    )
    learning = LearningService(store=database)
    work = WorkService(store=database)
    finance = FinanceService()
    lightning_gateway = app.config.get("LIGHTNING_GATEWAY")
    if lightning_gateway is None:
        if app.config["LIGHTNING_MODE"] != "SANDBOX":
            raise RuntimeError("a LightningGateway adapter is required outside SANDBOX")
        lightning_gateway = SandboxLightningGateway()
    community = CommunityService()
    onboarding_drafts = {}
    app.config["NOSTR_AUTH"] = auth
    app.config["ADMIN_NOSTR_AUTH"] = admin_auth
    app.config["LEARNING"] = learning
    app.config["WORK"] = work
    app.config["FINANCE"] = finance
    app.config["LIGHTNING_GATEWAY"] = lightning_gateway
    app.config["DATABASE"] = database

    def session_cookie_options() -> dict:
        return {
            "httponly": app.config["SESSION_COOKIE_HTTPONLY"],
            "secure": app.config["ENVIRONMENT"] == "production",
            "samesite": app.config["SESSION_COOKIE_SAMESITE"],
            "path": app.config["SESSION_COOKIE_PATH"],
        }

    def admin_session_cookie_options() -> dict:
        return {
            **session_cookie_options(),
            "path": "/admin",
        }

    @app.before_request
    def enforce_cookie_origin():
        if (
            app.config["ENVIRONMENT"] == "production"
            and request.method not in {"GET", "HEAD", "OPTIONS"}
            and (
                request.cookies.get(app.config["SESSION_COOKIE_NAME"])
                or request.cookies.get(app.config["ADMIN_SESSION_COOKIE_NAME"])
            )
        ):
            origin = request.headers.get("Origin")
            if not origin or origin not in app.config["CORS_ORIGINS"]:
                return jsonify({"type": "about:blank", "title": "Forbidden", "status": 403}), 403

    @app.after_request
    def apply_cors(response):
        origin = request.headers.get("Origin")
        if origin and origin in app.config["CORS_ORIGINS"]:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, Idempotency-Key"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
            response.vary.add("Origin")
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        app.logger.info(
            "http_request_completed",
            extra={"fields": {"method": request.method, "path": request.path, "status": response.status_code}},
        )
        return response

    def participant():
        return auth.current(request.cookies.get(app.config["SESSION_COOKIE_NAME"]))

    def require_participant():
        current = participant()
        if not current:
            return None, (jsonify({"status": 401, "title": "Unauthorized"}), 401)
        if rbac_store and not rbac_store.has_any_role(current.pubkey, {"PARTICIPANT"}):
            return None, (jsonify({"status": 403, "title": "Forbidden"}), 403)
        return current, None

    def require_admin(required_roles=frozenset({"ADMIN"})):
        current = admin_auth.current(
            request.cookies.get(app.config["ADMIN_SESSION_COOKIE_NAME"])
        )
        if not current:
            if participant():
                return None, (jsonify({"status": 403, "title": "Forbidden"}), 403)
            return None, (jsonify({"status": 401, "title": "Unauthorized"}), 401)
        if rbac_store and not rbac_store.has_any_role(current.pubkey, required_roles):
            return None, (jsonify({"status": 403, "title": "Forbidden"}), 403)
        return current, None

    def require_donor():
        current, error = require_participant()
        if error:
            return None, error
        if not rbac_store or not rbac_store.has_any_role(current.pubkey, {"DONOR"}):
            return None, (jsonify({"status": 403, "title": "Forbidden"}), 403)
        return current, None

    def reject_client_selected_role(body):
        if any(field in body for field in ("role", "roles", "session_scope")):
            return jsonify(
                {
                    "type": "about:blank",
                    "title": "Client-selected roles are not accepted",
                    "status": 422,
                }
            ), 422
        return None

    @app.get("/health/live")
    def live():
        return jsonify({"status": "ok"})

    @app.get("/health/ready")
    def ready():
        if database is None:
            return jsonify({"status": "ok", "dependencies": {"database": "not-configured"}})
        try:
            database.ping()
        except Exception:
            return jsonify({"status": "unavailable", "dependencies": {"database": "unavailable"}}), 503
        return jsonify({"status": "ok", "dependencies": {"database": "ready"}})

    @app.post("/auth/nostr/challenges")
    def create_challenge():
        challenge = auth.issue_challenge()
        return jsonify(
            {
                "challenge": challenge.value,
                "expires_at": challenge.expires_at.isoformat(),
                "signing": auth.signing_contract(challenge.value),
            }
        )

    @app.post("/auth/nostr/sessions")
    def create_session():
        body = request.get_json(silent=True) or {}
        rejected = reject_client_selected_role(body)
        if rejected:
            return rejected
        try:
            created = auth.authenticate(body.get("challenge"), body.get("pubkey"), body.get("signature"), body.get("event"))
        except ValueError as error:
            return jsonify({"type": "about:blank", "title": "Invalid authentication", "status": 401, "detail": str(error)}), 401
        auth.revoke(request.cookies.get(app.config["SESSION_COOKIE_NAME"]))
        response = jsonify(
            {"pubkey": created.pubkey, "expires_at": created.expires_at.isoformat(), "mode": created.mode}
        )
        response.set_cookie(app.config["SESSION_COOKIE_NAME"], created.token, **session_cookie_options())
        return response, 201

    @app.post("/auth/demo/sessions")
    def create_demo_session():
        if not app.config["DEMO_AUTH_ENABLED"] or app.config["ENVIRONMENT"] == "production":
            return jsonify({"type": "about:blank", "title": "Not Found", "status": 404}), 404
        auth.revoke(request.cookies.get(app.config["SESSION_COOKIE_NAME"]))
        created = auth.authenticate_demo(app.config["DEMO_AUTH_PUBKEY"])
        response = jsonify(
            {"pubkey": created.pubkey, "expires_at": created.expires_at.isoformat(), "mode": created.mode}
        )
        response.set_cookie(app.config["SESSION_COOKIE_NAME"], created.token, **session_cookie_options())
        return response, 201

    @app.post("/admin/auth/nostr/challenges")
    def create_admin_challenge():
        challenge = admin_auth.issue_challenge()
        return jsonify(
            {
                "challenge": challenge.value,
                "expires_at": challenge.expires_at.isoformat(),
                "signing": admin_auth.signing_contract(challenge.value),
            }
        )

    @app.post("/admin/auth/nostr/sessions")
    def create_admin_session():
        body = request.get_json(silent=True) or {}
        rejected = reject_client_selected_role(body)
        if rejected:
            return rejected
        try:
            created = admin_auth.authenticate(
                body.get("challenge"),
                body.get("pubkey"),
                body.get("signature"),
                body.get("event"),
            )
        except AuthorizationDenied as error:
            return jsonify(
                {
                    "type": "about:blank",
                    "title": "Administrative role required",
                    "status": 403,
                    "detail": str(error),
                }
            ), 403
        except ValueError as error:
            return jsonify(
                {
                    "type": "about:blank",
                    "title": "Invalid administrative authentication",
                    "status": 401,
                    "detail": str(error),
                }
            ), 401
        admin_auth.revoke(request.cookies.get(app.config["ADMIN_SESSION_COOKIE_NAME"]))
        response = jsonify(
            {
                "pubkey": created.pubkey,
                "expires_at": created.expires_at.isoformat(),
                "mode": created.mode,
                "scope": "ADMIN",
            }
        )
        response.set_cookie(
            app.config["ADMIN_SESSION_COOKIE_NAME"],
            created.token,
            **admin_session_cookie_options(),
        )
        return response, 201

    @app.post("/onboarding/drafts")
    def create_onboarding_draft():
        current, error = require_participant()
        if error:
            return error
        if database:
            return jsonify(database.create_onboarding_draft(current.pubkey)), 201
        existing = next(
            (
                draft
                for draft in onboarding_drafts.values()
                if draft["owner_pubkey"] == current.pubkey and draft["status"] == "IN_PROGRESS"
            ),
            None,
        )
        if existing:
            return jsonify({key: value for key, value in existing.items() if key != "owner_pubkey"}), 201
        draft_id = uuid.uuid4().hex
        onboarding_drafts[draft_id] = {
            "id": draft_id,
            "status": "IN_PROGRESS",
            "owner_pubkey": current.pubkey,
        }
        return jsonify({"id": draft_id, "status": "IN_PROGRESS"}), 201

    @app.patch("/onboarding/drafts/<draft_id>")
    def update_onboarding_draft(draft_id):
        current, error = require_participant()
        if error:
            return error
        draft = (
            database.get_onboarding_draft(draft_id, current.pubkey)
            if database
            else onboarding_drafts.get(draft_id)
        )
        if draft and not database and draft.get("owner_pubkey") != current.pubkey:
            draft = None
        if not draft:
            return jsonify({"status": 404, "title": "Not Found"}), 404
        body = request.get_json(silent=True) or {}
        fields = {
            key: body[key]
            for key in ("name", "email", "identity", "skills", "verification", "consent")
            if key in body
        }
        if database:
            try:
                draft = database.update_onboarding_draft(draft_id, current.pubkey, fields)
            except ValueError:
                return jsonify({"status": 409, "title": "Onboarding already completed"}), 409
        else:
            draft.update(fields)
        return jsonify({key: value for key, value in draft.items() if key != "owner_pubkey"})

    @app.post("/onboarding/drafts/<draft_id>/complete")
    def complete_onboarding_draft(draft_id):
        current, error = require_participant()
        if error:
            return error
        draft = (
            database.get_onboarding_draft(draft_id, current.pubkey)
            if database
            else onboarding_drafts.get(draft_id)
        )
        if draft and not database and draft.get("owner_pubkey") != current.pubkey:
            draft = None
        if not draft:
            return jsonify({"status": 404, "title": "Not Found"}), 404
        required = ("name", "email", "identity", "skills", "verification", "consent")
        if database:
            try:
                draft = database.complete_onboarding_draft(draft_id, current.pubkey, required)
            except OnboardingIncomplete:
                return jsonify({"status": 422, "title": "Onboarding incomplete"}), 422
        else:
            if any(not draft.get(key) for key in required):
                return jsonify({"status": 422, "title": "Onboarding incomplete"}), 422
            draft["status"] = "COMPLETED"
        return jsonify({key: value for key, value in draft.items() if key != "owner_pubkey"}), 201

    @app.get("/courses")
    def courses():
        course = learning.course
        return jsonify({"items": [{"id": course.id, "version": course.version, "title": course.title, "objective": course.objective, "duration_minutes": course.duration_minutes}]})

    @app.get("/courses/enrollments")
    def learning_enrollments():
        current, error = require_participant()
        if error:
            return error
        return jsonify({"items": learning.list_enrollments(current.pubkey)})

    @app.get("/courses/<course_id>")
    def course_detail(course_id):
        if course_id != learning.course.id:
            return jsonify({"status": 404, "title": "Not Found"}), 404
        course = learning.course
        return jsonify({"id": course.id, "version": course.version, "assessment_version": course.assessment_version, "title": course.title, "objective": course.objective, "duration_minutes": course.duration_minutes, "module_id": course.module_id, "modules": course.modules, "questions": [{"id": q["id"], "prompt": q["prompt"]} for q in course.questions]})

    @app.get("/courses/<course_id>/lessons/<lesson_id>")
    def lesson_detail(course_id, lesson_id):
        if course_id != learning.course.id:
            return jsonify({"status": 404, "title": "Not Found"}), 404
        lesson = learning.course.modules[0]["lessons"][0]
        if lesson_id != lesson["id"]:
            return jsonify({"status": 404, "title": "Not Found"}), 404
        return jsonify({"id": lesson["id"], "course_id": course_id, "module_id": learning.course.module_id, "title": lesson["title"], "status": "AVAILABLE", "activity_ids": lesson["activity_ids"]})

    @app.get("/courses/<course_id>/activities/<activity_id>")
    def activity_detail(course_id, activity_id):
        if course_id != learning.course.id:
            return jsonify({"status": 404, "title": "Not Found"}), 404
        activity = learning.course.modules[0]["lessons"][0]["activity_ids"]
        if activity_id not in activity:
            return jsonify({"status": 404, "title": "Not Found"}), 404
        return jsonify({"id": activity_id, "course_id": course_id, "module_id": learning.course.module_id, "lesson_id": learning.course.modules[0]["lessons"][0]["id"], "title": "Atividade prática", "status": "AVAILABLE"})

    @app.get("/courses/<course_id>/lessons/<lesson_id>/notes")
    def get_lesson_note(course_id, lesson_id):
        current, error = require_participant()
        if error: return error

        if course_id != learning.course.id or lesson_id != learning.course.modules[0]["lessons"][0]["id"]:
            return jsonify({"status": 404, "title": "Not Found"}), 404
        return jsonify(learning.note(current.pubkey, course_id, lesson_id))

    @app.put("/courses/<course_id>/lessons/<lesson_id>/notes")
    def save_lesson_note(course_id, lesson_id):
        current, error = require_participant()
        if error: return error
        if course_id != learning.course.id or lesson_id != learning.course.modules[0]["lessons"][0]["id"]:
            return jsonify({"status": 404, "title": "Not Found"}), 404
        content = (request.get_json(silent=True) or {}).get("content", "")
        if not isinstance(content, str) or len(content) > 10000:
            return jsonify({"status": 422, "title": "Invalid note"}), 422
        return jsonify(learning.save_note(current.pubkey, course_id, lesson_id, content))

    @app.post("/courses/<course_id>/activities/<activity_id>/submissions")
    def submit_learning_activity(course_id, activity_id):
        current = participant()
        if not current:
            return jsonify({"status": 401, "title": "Unauthorized"}), 401
        if course_id != learning.course.id:
            return jsonify({"status": 404, "title": "Not Found"}), 404
        content = (request.get_json(silent=True) or {}).get("content", "").strip()
        if not content or len(content) > 20000:
            return jsonify({"status": 422, "title": "Activity content is required"}), 422
        try:
            return jsonify(learning.submit_activity(current.pubkey, course_id, activity_id, content)), 201
        except ValueError:
            return jsonify({"status": 409, "title": "Activity already submitted"}), 409

    @app.post("/courses/<course_id>/enrollments")
    def enroll(course_id):
        current = participant()
        if not current:
            return jsonify({"status": 401, "title": "Unauthorized"}), 401
        if course_id != learning.course.id:
            return jsonify({"status": 404, "title": "Not Found"}), 404
        return jsonify(learning.enroll(current.pubkey)), 201

    @app.post("/modules/<module_id>/quiz-attempts")
    def quiz_attempt(module_id):
        current = participant()
        if not current:
            return jsonify({"status": 401, "title": "Unauthorized"}), 401
        if module_id != learning.course.module_id:
            return jsonify({"status": 404, "title": "Not Found"}), 404
        body = request.get_json(silent=True) or {}
        answers = body.get("answers")
        if (
            not isinstance(answers, dict)
            or len(answers) > 20
            or any(not isinstance(key, str) or not isinstance(value, str) or len(value) > 100 for key, value in answers.items())
        ):
            return jsonify({"status": 422, "title": "Invalid quiz answers"}), 422
        attempt, evidence = learning.submit(current.pubkey, answers)
        return jsonify({"attempt": attempt, "skill_evidence": evidence, "passed": attempt["score"] >= 80}), 201

    @app.get("/skill-evidence")
    def skill_evidence():
        current = participant()
        if not current:
            return jsonify({"status": 401, "title": "Unauthorized"}), 401
        return jsonify({"items": learning.list_evidence(current.pubkey)})

    @app.put("/skill-evidence/<evidence_id>/badge-consent")
    def badge_consent(evidence_id):
        current = participant()
        if not current:
            return jsonify({"status": 401, "title": "Unauthorized"}), 401
        body = request.get_json(silent=True) or {}
        if body.get("consent") is not True:
            return jsonify(
                {
                    "status": 422,
                    "title": "Explicit badge consent is required",
                }
            ), 422
        try:
            return jsonify(learning.consent_badge(current.pubkey, evidence_id)), 202
        except ValueError:
            return jsonify({"status": 404, "title": "Not Found"}), 404

    @app.get("/skill-evidence/<evidence_id>/badge-publication")
    def badge_publication(evidence_id):
        current = participant()
        if not current:
            return jsonify({"status": 401, "title": "Unauthorized"}), 401
        publication = learning.badge_publication(current.pubkey, evidence_id)
        if publication is None:
            return jsonify({"status": 404, "title": "Not Found"}), 404
        return jsonify(publication)

    @app.get("/me")
    def me():
        current = participant()
        if not current:
            return jsonify({"type": "about:blank", "title": "Unauthorized", "status": 401}), 401
        return jsonify(
            {
                "pubkey": current.pubkey,
                "mode": current.mode,
                "roles": sorted(rbac_store.roles_for_pubkey(current.pubkey)) if rbac_store else ["PARTICIPANT"],
                "expires_at": current.expires_at.isoformat(),
            }
        )

    @app.post("/admin/companies")
    def create_company():
        _, error = require_admin()
        if error: return error
        body = request.get_json(silent=True) or {}
        try:
            return jsonify(work.company(body["name"], body.get("description", ""))), 201
        except KeyError:
            return jsonify({"status": 400, "title": "name is required"}), 400

    @app.get("/organization/companies/<company_id>")
    def organization_company(company_id):
        current, error = require_participant()
        if error:
            return error
        if not database:
            return jsonify({"status": 503, "title": "Database required"}), 503
        if not rbac_store or not rbac_store.has_any_role(
            current.pubkey, {"ORGANIZATION"}
        ):
            return jsonify({"status": 403, "title": "Forbidden"}), 403
        if not rbac_store.has_company_membership(current.pubkey, company_id):
            return jsonify({"status": 403, "title": "Forbidden"}), 403
        company = database.get_company(company_id)
        return (jsonify(company), 200) if company else (
            jsonify({"status": 404, "title": "Not Found"}),
            404,
        )

    @app.post("/admin/paid-tasks/drafts")
    def create_task_draft():
        current, error = require_admin()
        if error: return error
        draft = work.create_draft(current.pubkey)
        return jsonify(draft), 201

    @app.patch("/admin/paid-tasks/drafts/<draft_id>")
    def update_task_draft(draft_id):
        draft = work.drafts.get(draft_id)
        if not draft:
            return jsonify({"status": 404, "title": "Not Found"}), 404
        current, error = require_admin()
        if error: return error
        if draft.get("owner_pubkey") and (not current or current.pubkey != draft["owner_pubkey"]):
            return jsonify({"status": 403, "title": "Forbidden"}), 403
        try:
            body = request.get_json(silent=True) or {}
            if "reward" in body and "reward_sats" not in body:
                body["reward_sats"] = int(body.pop("reward"))
            return jsonify(work.update_draft(draft_id, body))
        except (KeyError, TypeError, ValueError):
            return jsonify({"status": 422, "title": "Invalid draft"}), 422

    @app.post("/admin/paid-tasks/drafts/<draft_id>/publish")
    def publish_task_draft(draft_id):
        draft = work.drafts.get(draft_id)
        if not draft:
            return jsonify({"status": 404, "title": "Not Found"}), 404
        current, error = require_admin()
        if error: return error
        if draft.get("owner_pubkey") and (not current or current.pubkey != draft["owner_pubkey"]):
            return jsonify({"status": 403, "title": "Forbidden"}), 403
        try:
            return jsonify(work.publish_draft(draft_id)), 201
        except ValueError as error:
            return jsonify({"status": 422, "title": str(error)}), 422

    @app.post("/admin/paid-tasks")
    def create_task():
        _, error = require_admin()
        if error: return error
        body = request.get_json(silent=True) or {}
        try:
            return jsonify(work.task(body["company_id"], body["title"], body.get("instructions", ""), int(body["reward_sats"]))), 201
        except (KeyError, ValueError):
            return jsonify({"status": 400, "title": "invalid task"}), 400

    @app.post("/admin/paid-tasks/<task_id>/funding-reservations")
    def fund_task(task_id):
        _, error = require_admin()
        if error: return error
        body = request.get_json(silent=True) or {}
        try:
            return jsonify(work.fund(task_id, int(body["amount_sats"]), body.get("sources"))), 201
        except (AssignmentUnavailable, KeyError, ValueError):
            return jsonify({"status": 409, "title": "invalid funding"}), 409

    @app.post("/admin/paid-tasks/<task_id>/publish")
    def publish_task(task_id):
        _, error = require_admin()
        if error: return error
        try:
            return jsonify(work.publish(task_id))
        except (KeyError, ValueError):
            return jsonify({"status": 409, "title": "task must be fully funded"}), 409

    @app.get("/paid-tasks")
    def list_tasks():
        current = participant()
        eligible_only = request.args.get("eligible", "").lower() == "true"
        pubkey = current.pubkey if current and learning.has_evidence(current.pubkey) else None
        return jsonify({"items": work.list_tasks(pubkey, eligible_only)})

    @app.get("/paid-tasks/<task_id>")
    def task_detail(task_id):
        task = work.get_task(task_id)
        if not task or task["status"] != "PUBLISHED":
            return jsonify({"status": 404, "title": "Not Found"}), 404
        company = work.get_company(task["company_id"]) or {}
        current = participant()
        return jsonify({**task, "company": company, "eligible": bool(current and learning.has_evidence(current.pubkey))})

    @app.post("/paid-tasks/<task_id>/assignment-reservations")
    def reserve_task(task_id):
        current, error = require_participant()
        if error: return error
        try:
            return jsonify(work.reserve(task_id, current.pubkey, learning.has_evidence(current.pubkey))), 201
        except (AssignmentUnavailable, RuntimeError):
            return jsonify({"status": 409, "title": "task already reserved"}), 409
        except (KeyError, ValueError):
            return jsonify({"status": 409, "title": "task unavailable or ineligible"}), 409

    @app.post("/paid-tasks/<task_id>/applications")
    def apply_task(task_id):
        current, error = require_participant()
        if error: return error
        body = request.get_json(silent=True) or {}
        try:
            return jsonify(work.apply(task_id, current.pubkey, body.get("message", ""), body.get("assignment_id"))), 201
        except RuntimeError:
            return jsonify({"status": 409, "title": "application already exists"}), 409
        except ValueError:
            return jsonify({"status": 404, "title": "task unavailable"}), 404

    @app.post("/uploads")
    def upload_metadata():
        current, error = require_participant()
        if error: return error
        body = request.get_json(silent=True) or {}
        try:
            return jsonify(
                work.upload(
                    current.pubkey,
                    body.get("filename", "upload"),
                    body.get("mime_type", ""),
                    int(body.get("size", 0)),
                    body.get("content_hash", ""),
                )
            ), 201
        except (KeyError, TypeError, ValueError):
            return jsonify({"status": 422, "title": "Unsupported or oversized upload"}), 422

    @app.get("/assignments/<assignment_id>")
    def assignment_detail(assignment_id):
        current, error = require_participant()
        if error: return error
        assignment = work.get_assignment(assignment_id)
        if not assignment:
            return jsonify({"status": 404, "title": "Not Found"}), 404
        if assignment["pubkey"] != current.pubkey:
            return jsonify({"status": 403, "title": "Forbidden"}), 403
        task = work.get_task(assignment["task_id"]) or {}
        return jsonify({"assignment": assignment, "task": task})

    @app.post("/assignments/<assignment_id>/submissions")
    def submit_assignment(assignment_id):
        current, error = require_participant()
        if error: return error
        body = request.get_json(silent=True) or {}
        try:
            return jsonify(work.submit(assignment_id, current.pubkey, body.get("content", ""), body.get("filename", "submission"), body.get("mime_type", "text/plain"), body.get("stored_object_id"))), 201
        except ValueError as exc:
            return jsonify({"status": 409, "title": str(exc)}), 409

    @app.get("/assignments/<assignment_id>/submissions/draft")
    def get_submission_draft(assignment_id):
        current, error = require_participant()
        if error: return error
        try:
            return jsonify(work.submission_draft(assignment_id, current.pubkey) or {"status": "EMPTY"})
        except ValueError:
            return jsonify({"status": 403, "title": "Forbidden"}), 403

    @app.put("/assignments/<assignment_id>/submissions/draft")
    def save_submission_draft(assignment_id):
        current, error = require_participant()
        if error: return error
        body = request.get_json(silent=True) or {}
        try:
            return jsonify(work.save_submission_draft(assignment_id, current.pubkey, body.get("content", ""), body.get("filename", "submission.txt"), body.get("mime_type", "text/plain"))), 200
        except ValueError as exc:
            return jsonify({"status": 409, "title": str(exc)}), 409

    @app.delete("/sessions/current")
    def logout():
        auth.revoke(request.cookies.get(app.config["SESSION_COOKIE_NAME"]))
        response = jsonify({"status": "revoked"})
        response.delete_cookie(app.config["SESSION_COOKIE_NAME"], **session_cookie_options())
        return response

    @app.delete("/admin/sessions/current")
    def admin_logout():
        admin_auth.revoke(request.cookies.get(app.config["ADMIN_SESSION_COOKIE_NAME"]))
        response = jsonify({"status": "revoked"})
        response.delete_cookie(
            app.config["ADMIN_SESSION_COOKIE_NAME"],
            **admin_session_cookie_options(),
        )
        return response

    @app.get("/admin/review-queue")
    def review_queue():
        _, error = require_admin({"REVIEWER", "ADMIN"})
        if error: return error
        return jsonify({"items": work.pending_submissions()})

    @app.get("/admin/submissions/<submission_id>")
    def review_submission_detail(submission_id):
        _, error = require_admin({"REVIEWER", "ADMIN"})
        if error: return error
        submission = (
            database.get_submission_for_review(submission_id)
            if database
            else work.get_submission(submission_id)
        )
        return (jsonify(submission), 200) if submission else (
            jsonify({"status": 404, "title": "Not Found"}),
            404,
        )

    @app.post("/admin/submissions/<submission_id>/reviews")
    def review_submission(submission_id):
        reviewer, error = require_admin({"REVIEWER", "ADMIN"})
        if error: return error
        body = request.get_json(silent=True) or {}
        try:
            if database:
                result = database.review_submission(
                    submission_id,
                    reviewer.pubkey,
                    body.get("decision", ""),
                    body.get("reason", ""),
                    app.config.get("FINANCIAL_MODE", "SANDBOX"),
                )
                return jsonify(result), 201
            review = finance.review(submission_id, body["decision"], body.get("reason", ""))
            if body["decision"] == "APPROVE":
                submission = work.get_submission(submission_id)
                if not submission:
                    raise KeyError(submission_id)
                assignment = work.approve_assignment(submission["assignment_id"])
                if database:
                    obligation = database.create_obligation(
                        assignment["id"],
                        work.get_task(assignment["task_id"])["reward_sats"],
                        app.config.get("FINANCIAL_MODE", "MOCK"),
                    )
                else:
                    obligation = finance.obligation(assignment["id"], work.get_task(assignment["task_id"])["reward_sats"])
                return jsonify({"review": review, "payment_obligation": obligation}), 201
            return jsonify(review), 201
        except ReviewConflict as exc:
            return jsonify({"status": 409, "title": str(exc)}), 409
        except (KeyError, ValueError, StopIteration) as exc:
            return jsonify({"status": 422, "title": str(exc) or "invalid review"}), 422

    @app.get("/assignments/<assignment_id>/payment-obligation")
    def get_obligation(assignment_id):
        current, error = require_participant()
        if error: return error
        assignment = work.get_assignment(assignment_id)
        if not assignment:
            return jsonify({"status": 404, "title": "Not Found"}), 404
        if assignment["pubkey"] != current.pubkey:
            return jsonify({"status": 403, "title": "Forbidden"}), 403
        obligation = database.get_obligation(assignment_id) if database else finance.obligations.get(assignment_id)
        return (jsonify(obligation), 200) if obligation else (jsonify({"status": 404, "title": "Not Found"}), 404)

    @app.post("/payment-obligations/<obligation_id>/payout-attempts")
    def create_attempt(obligation_id):
        current, error = require_participant()
        if error:
            return error
        body = request.get_json(silent=True) or {}
        try:
            invoice = body["invoice"]
            if not isinstance(invoice, str) or not invoice.strip():
                raise ValueError("invoice is required")
            if database:
                obligation = database.get_obligation_by_id(obligation_id)
                if not obligation:
                    raise KeyError(obligation_id)
                assignment = work.get_assignment(obligation["assignment_id"])
                if not assignment:
                    raise KeyError(obligation["assignment_id"])
                if assignment["pubkey"] != current.pubkey:
                    return jsonify({"status": 403, "title": "Forbidden"}), 403
                metadata = lightning_gateway.validate_invoice(
                    invoice, obligation["amount_sats"]
                )
                attempt = database.create_payout_attempt(
                    obligation_id,
                    request.headers.get("Idempotency-Key", ""),
                    obligation["mode"],
                    invoice_metadata=metadata,
                )
            else:
                obligation = next(
                    (item for item in finance.obligations.values() if item["id"] == obligation_id),
                    None,
                )
                if not obligation:
                    raise KeyError(obligation_id)
                metadata = lightning_gateway.validate_invoice(
                    invoice, obligation["amount_sats"]
                )
                attempt = finance.attempt(
                    obligation_id,
                    metadata,
                    request.headers.get("Idempotency-Key", ""),
                )
            return jsonify(attempt), 201
        except (ActivePayoutAttempt, IdempotencyConflict, KeyError, ObligationNotOpen, RuntimeError, ValueError):
            return jsonify({"status": 409, "title": "active payout attempt exists or invalid request"}), 409

    @app.get("/payment-obligations/<obligation_id>/payout-status")
    def payout_status(obligation_id):
        current, error = require_participant()
        if error: return error
        obligation = database.get_obligation_by_id(obligation_id) if database else next(
            (item for item in finance.obligations.values() if item["id"] == obligation_id), None
        )
        if not obligation:
            return jsonify({"status": 404, "title": "Not Found"}), 404
        assignment = work.get_assignment(obligation["assignment_id"])
        if assignment and assignment["pubkey"] != current.pubkey:
            return jsonify({"status": 403, "title": "Forbidden"}), 403
        attempt = database.get_attempt_for_obligation(obligation_id) if database else next(
            (item for item in finance.attempts.values() if item["obligation_id"] == obligation_id), None
        )
        return jsonify({"obligation": obligation, "attempt": attempt, "mode": attempt.get("mode", "MOCK") if attempt else "MOCK"})

    @app.post("/admin/payout-attempts/<attempt_id>/reconcile")
    def reconcile(attempt_id):
        _, error = require_admin()
        if error: return error
        body = request.get_json(silent=True) or {}
        try:
            if database:
                return jsonify(
                    database.reconcile_payout_attempt(
                        attempt_id,
                        outcome=body.get("outcome", ""),
                        provider_event_id=body.get("provider_event_id", ""),
                        provider_reference=body.get("provider_reference"),
                    )
                )
            return jsonify(finance.settle(attempt_id))
        except KeyError:
            return jsonify({"status": 404, "title": "Not Found"}), 404
        except (IdempotencyConflict, ValueError) as exc:
            return jsonify({"status": 409, "title": str(exc)}), 409

    @app.get("/receipts/<receipt_id>")
    def receipt(receipt_id):
        current, error = require_participant()
        if error:
            return error
        if database:
            item = database.get_payment_receipt(receipt_id)
            if item and not database.receipt_owned_by_pubkey(receipt_id, current.pubkey):
                return jsonify({"status": 403, "title": "Forbidden"}), 403
        else:
            item = finance.receipts.get(receipt_id)
        return (jsonify(item), 200) if item else (jsonify({"status": 404, "title": "Not Found"}), 404)

    @app.post("/donor/contributions")
    def create_donor_contribution():
        current, error = require_donor()
        if error:
            return error
        if not database:
            return jsonify({"status": 503, "title": "PostgreSQL is required"}), 503
        body = request.get_json(silent=True) or {}
        try:
            result = database.create_donor_contribution(
                current.pubkey,
                idempotency_key=request.headers.get("Idempotency-Key", ""),
                amount_sats=body.get("amount_sats"),
                impact_percentage_bps=body.get("impact_percentage_bps"),
                liquidity_percentage_bps=body.get("liquidity_percentage_bps"),
                terms_version=body.get("terms_version", ""),
                terms_accepted=body.get("terms_accepted") is True,
                mode="SANDBOX",
            )
            return jsonify(result), 201
        except IdempotencyConflict as exc:
            return jsonify({"status": 409, "title": str(exc)}), 409
        except (PermissionError, ValueError) as exc:
            return jsonify({"status": 422, "title": str(exc)}), 422

    @app.get("/donor/contributions")
    def list_donor_contributions():
        current, error = require_donor()
        if error:
            return error
        return jsonify({"items": database.list_donor_contributions(current.pubkey)})

    @app.get("/donor/dashboard")
    def donor_dashboard():
        current, error = require_donor()
        if error:
            return error
        return jsonify(database.get_donor_dashboard(current.pubkey))

    @app.get("/community/feed")
    def community_feed():
        if persistent_community:
            try:
                limit = min(max(int(request.args.get("limit", 20)), 1), 50)
                offset = max(int(request.args.get("offset", 0)), 0)
            except ValueError:
                limit, offset = 20, 0
            category = request.args.get("category") or None
            try:
                items = database.list_visible_community_posts(limit, offset, category)
            except ValueError:
                return jsonify({"status": 422, "title": "Invalid community category"}), 422
            return jsonify({"items": items, "next_offset": offset + limit if len(items) == limit else None, "public_warning": "Conteúdo armazenado localmente; relays Nostr estão desabilitados."})
        visible = [p for p in community.posts if p["moderation_status"] == "VISIBLE"]
        try: limit = min(max(int(request.args.get("limit", 20)), 1), 50)
        except ValueError: limit = 20
        offset = max(int(request.args.get("offset", 0)), 0)
        page = visible[offset:offset + limit]
        return jsonify({"items": page, "next_offset": offset + limit if offset + limit < len(visible) else None, "public_warning": "Publicação Nostr é pública e difícil de remover."})

    @app.post("/community/posts")
    def community_post():
        current, error = require_participant()
        if error: return error
        body = request.get_json(silent=True) or {}
        if persistent_community:
            try:
                return jsonify(database.create_local_community_post(
                    current.pubkey,
                    body["category"],
                    body["content"],
                    body.get("public_acknowledged"),
                    request.headers.get("Idempotency-Key"),
                )), 201
            except (KeyError, ValueError):
                return jsonify({"status": 422, "title": "Invalid public post"}), 422
        try: return jsonify(community.post(current.pubkey, body["category"], body["content"], body.get("media_asset_id"))), 201
        except (KeyError, ValueError): return jsonify({"status": 400, "title": "invalid post"}), 400

    @app.post("/community/reports")
    def report():
        current, error = require_participant()
        if error: return error
        body = request.get_json(silent=True) or {}
        if persistent_community:
            try:
                subject_type = body.get("subject_type") or ("POST" if body.get("post_id") else "OPPORTUNITY")
                subject_id = body.get("subject_id") or body.get("post_id") or body.get("opportunity_id")
                return jsonify(database.report_community_content(
                    current.pubkey,
                    subject_type,
                    subject_id,
                    body.get("category") or "OTHER",
                    body.get("details") or body.get("reason", ""),
                )), 201
            except (KeyError, ValueError):
                return jsonify({"status": 422, "title": "Invalid report"}), 422
        item = {"id": uuid.uuid4().hex, "nostr_event_id": body.get("nostr_event_id"), "reporter": current.pubkey, "reason": body.get("reason", ""), "status": "OPEN"}; community.reports.append(item); return jsonify(item), 201

    @app.post("/community/posts/<post_id>/comments")
    def comment_post(post_id):
        current, error = require_participant()
        if error: return error
        try:
            return jsonify(community.comment(current.pubkey, post_id, (request.get_json(silent=True) or {}).get("content", ""))), 201
        except ValueError:
            return jsonify({"status": 422, "title": "Invalid comment"}), 422

    @app.post("/community/posts/<post_id>/reactions")
    def react_post(post_id):
        current, error = require_participant()
        if error: return error
        try: return jsonify(community.react(current.pubkey, post_id))
        except ValueError: return jsonify({"status": 404, "title": "Post not found"}), 404

    @app.get("/opportunities")
    def opportunities():
        if persistent_community:
            return jsonify({"paid_tasks": [{**task, "type": "PAID_TASK"} for task in work.tasks.values() if task["status"] == "PUBLISHED"], "external_opportunities": database.list_opportunity_listings()})
        return jsonify({"paid_tasks": [{**task, "type": "PAID_TASK"} for task in work.tasks.values() if task["status"] == "PUBLISHED"], "external_opportunities": [{**item, "type": "EXTERNAL_OPPORTUNITY"} for item in community.opportunities if item.get("status") == "PUBLISHED"]})

    @app.get("/opportunities/external/<listing_id>")
    def external_opportunity_detail(listing_id):
        if not persistent_community:
            return jsonify({"status": 503, "title": "Persistent database required"}), 503
        item = database.get_opportunity_listing(listing_id)
        if not item or item.get("moderation_status") != "VISIBLE":
            return jsonify({"status": 404, "title": "Not Found"}), 404
        return jsonify(item)

    @app.post("/opportunities/external")
    def create_external_opportunity():
        current, error = require_participant()
        if error:
            return error
        body = request.get_json(silent=True) or {}
        if not persistent_community:
            return jsonify({"status": 503, "title": "Persistent database required"}), 503
        try:
            return jsonify(database.create_opportunity_listing(
                current.pubkey,
                body["title"],
                body["category"],
                body["description"],
                body["organization_name"],
                body["external_url"],
                format=body["format"],
                location=body.get("location"),
                starts_at=body["starts_at"],
                application_deadline=body.get("application_deadline"),
                tags=body.get("tags"),
                requirements=body.get("requirements", ""),
                non_remunerated_ack=body.get("non_remunerated_ack"),
                idempotency_key=request.headers.get("Idempotency-Key"),
            )), 201
        except (KeyError, ValueError):
            return jsonify({"status": 422, "title": "Invalid external opportunity"}), 422

    @app.post("/admin/moderation-decisions")
    def moderate_community_content():
        current, error = require_admin({"ADMIN", "REVIEWER"})
        if error:
            return error
        body = request.get_json(silent=True) or {}
        if not database:
            return jsonify({"status": 503, "title": "Persistent database required"}), 503
        try:
            subject_type = body.get("subject_type") or ("POST" if body.get("post_id") else "OPPORTUNITY")
            subject_id = body.get("subject_id") or body.get("post_id") or body.get("opportunity_id")
            return jsonify(database.moderate_community_content(
                current.pubkey, subject_type, subject_id, body["action"], body["reason"]
            )), 201
        except (KeyError, ValueError):
            return jsonify({"status": 422, "title": "Invalid moderation decision"}), 422

    @app.get("/admin/me")
    def admin_me():
        current, error = require_admin({"ADMIN", "REVIEWER"})
        if error:
            return error
        return jsonify({
            "pubkey": current.pubkey,
            "roles": sorted(rbac_store.roles_for_pubkey(current.pubkey)) if rbac_store else ["ADMIN"],
            "expires_at": current.expires_at.isoformat(),
        })

    @app.get("/admin/community/moderation-queue")
    def community_moderation_queue():
        _, error = require_admin({"ADMIN", "REVIEWER"})
        if error:
            return error
        if not database:
            return jsonify({"status": 503, "title": "Persistent database required"}), 503
        return jsonify({"items": database.list_community_moderation_queue()})

    @app.post("/admin/opportunities")
    def add_opportunity():
        _, error = require_admin()
        if error: return error
        body = request.get_json(silent=True) or {}
        item = {"id": uuid.uuid4().hex, "type": "EXTERNAL_OPPORTUNITY", "organization_name": body.get("organization_name"), "title": body.get("title"), "external_url": body.get("external_url"), "status": "PUBLISHED"}
        community.opportunities.append(item)
        return jsonify(item), 201

    @app.get("/impact/realized")
    def realized_impact():
        return jsonify({"mode": "REAL", "settled_payments": len([a for a in finance.attempts.values() if a["status"] == "SETTLED"]), "simulation_included": False})

    @app.get("/impact/simulations")
    def simulations():
        return jsonify({"mode": "MOCK", "items": [], "simulation_included": False})

    @app.get("/wallet/summary")
    def wallet_summary():
        current = participant()
        if not current:
            return jsonify({"status": 401, "title": "Unauthorized"}), 401
        settled = [a for a in finance.attempts.values() if a["status"] == "SETTLED"]
        receipts = [r for r in finance.receipts.values() if any(a["id"] == r["attempt_id"] for a in settled)]
        return jsonify({"mode": "MOCK", "score": 0, "total_sats": sum(r["amount_sats"] for r in receipts), "transactions": receipts, "in_progress": []})

    @app.errorhandler(404)
    def not_found(_error):
        return jsonify({"type": "about:blank", "title": "Not Found", "status": 404}), 404

    return app
