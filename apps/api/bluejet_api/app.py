from flask import Flask, jsonify
from flask import request
import uuid

from .config import Config, validate_config
from .auth import NostrAuth
from .learning import LearningService
from .work import WorkService
from .finance import FinanceService
from .community import CommunityService


def create_app(config_object: type[Config] = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_object)
    validate_config(app.config)
    auth = NostrAuth()
    learning = LearningService()
    work = WorkService()
    finance = FinanceService()
    community = CommunityService()
    onboarding_drafts = {}
    app.config["NOSTR_AUTH"] = auth
    app.config["LEARNING"] = learning
    app.config["WORK"] = work
    app.config["FINANCE"] = finance

    def participant():
        return auth.current(request.cookies.get("bluejet_session"))

    def require_participant():
        current = participant()
        return current, (None if current else (jsonify({"status": 401, "title": "Unauthorized"}), 401))

    def require_admin():
        current = participant()
        if not current:
            return None, (jsonify({"status": 401, "title": "Unauthorized"}), 401)
        admins = app.config.get("ADMIN_PUBKEYS", set())
        if not admins or current.pubkey not in admins:
            return None, (jsonify({"status": 403, "title": "Forbidden"}), 403)
        return current, None

    @app.get("/health/live")
    def live():
        return jsonify({"status": "ok"})

    @app.get("/health/ready")
    def ready():
        # Database readiness is wired in when SQLAlchemy is introduced.
        return jsonify({"status": "ok", "dependencies": {"database": "not-configured"}})

    @app.post("/auth/nostr/challenges")
    def create_challenge():
        challenge = auth.issue_challenge()
        return jsonify({"challenge": challenge.value, "expires_at": challenge.expires_at.isoformat()})

    @app.post("/auth/nostr/sessions")
    def create_session():
        body = request.get_json(silent=True) or {}
        try:
            created = auth.authenticate(body.get("challenge"), body.get("pubkey"), body.get("signature"), body.get("event"))
        except ValueError as error:
            return jsonify({"type": "about:blank", "title": "Invalid authentication", "status": 401, "detail": str(error)}), 401
        response = jsonify({"pubkey": created.pubkey, "expires_at": created.expires_at.isoformat()})
        response.set_cookie("bluejet_session", created.token, httponly=True, secure=app.config["ENVIRONMENT"] == "production", samesite="Lax")
        return response, 201

    @app.post("/onboarding/drafts")
    def create_onboarding_draft():
        draft_id = uuid.uuid4().hex
        onboarding_drafts[draft_id] = {"id": draft_id, "status": "IN_PROGRESS"}
        return jsonify(onboarding_drafts[draft_id]), 201

    @app.patch("/onboarding/drafts/<draft_id>")
    def update_onboarding_draft(draft_id):
        draft = onboarding_drafts.get(draft_id)
        if not draft:
            return jsonify({"status": 404, "title": "Not Found"}), 404
        body = request.get_json(silent=True) or {}
        for key in ("name", "email", "identity", "skills", "verification", "consent"):
            if key in body: draft[key] = body[key]
        return jsonify(draft)

    @app.post("/onboarding/drafts/<draft_id>/complete")
    def complete_onboarding_draft(draft_id):
        draft = onboarding_drafts.get(draft_id)
        if not draft:
            return jsonify({"status": 404, "title": "Not Found"}), 404
        required = ("name", "email", "identity", "skills", "consent")
        if any(not draft.get(key) for key in required) or not draft.get("skills"):
            return jsonify({"status": 422, "title": "Onboarding incomplete"}), 422
        draft["status"] = "COMPLETED"
        return jsonify(draft), 201

    @app.get("/courses")
    def courses():
        course = learning.course
        return jsonify({"items": [{"id": course.id, "title": course.title, "objective": course.objective, "duration_minutes": course.duration_minutes}]})

    @app.get("/courses/<course_id>")
    def course_detail(course_id):
        if course_id != learning.course.id:
            return jsonify({"status": 404, "title": "Not Found"}), 404
        course = learning.course
        return jsonify({"id": course.id, "title": course.title, "objective": course.objective, "duration_minutes": course.duration_minutes, "module_id": course.module_id, "modules": course.modules, "questions": [{"id": q["id"], "prompt": q["prompt"]} for q in course.questions]})

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
        if not content:
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
        attempt, evidence = learning.submit(current.pubkey, body.get("answers", {}))
        return jsonify({"attempt": attempt, "skill_evidence": evidence, "passed": attempt["score"] >= 80}), 201

    @app.get("/skill-evidence")
    def skill_evidence():
        current = participant()
        if not current:
            return jsonify({"status": 401, "title": "Unauthorized"}), 401
        return jsonify({"items": ([learning.evidence[current.pubkey]] if current.pubkey in learning.evidence else [])})

    @app.put("/skill-evidence/<evidence_id>/badge-consent")
    def badge_consent(evidence_id):
        current = participant()
        if not current:
            return jsonify({"status": 401, "title": "Unauthorized"}), 401
        try:
            return jsonify(learning.consent_badge(current.pubkey, evidence_id)), 202
        except ValueError:
            return jsonify({"status": 404, "title": "Not Found"}), 404

    @app.get("/me")
    def me():
        current = auth.current(request.cookies.get("bluejet_session"))
        if not current:
            return jsonify({"type": "about:blank", "title": "Unauthorized", "status": 401}), 401
        return jsonify({"pubkey": current.pubkey})

    @app.post("/admin/companies")
    def create_company():
        _, error = require_admin()
        if error: return error
        body = request.get_json(silent=True) or {}
        try:
            return jsonify(work.company(body["name"], body.get("description", ""))), 201
        except KeyError:
            return jsonify({"status": 400, "title": "name is required"}), 400

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
        try:
            return jsonify(work.fund(task_id, int((request.get_json(silent=True) or {})["amount_sats"]))), 201
        except (KeyError, ValueError):
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
        eligible = bool(current and learning.evidence.get(current.pubkey))
        return jsonify({"items": [t for t in work.tasks.values() if t["status"] == "PUBLISHED" and (not request.args.get("eligible") or eligible)]})

    @app.get("/paid-tasks/<task_id>")
    def task_detail(task_id):
        task = work.tasks.get(task_id)
        if not task or task["status"] != "PUBLISHED":
            return jsonify({"status": 404, "title": "Not Found"}), 404
        company = work.companies.get(task["company_id"], {})
        return jsonify({**task, "company": company, "eligible": bool(participant() and learning.evidence.get(participant().pubkey))})

    @app.post("/paid-tasks/<task_id>/assignment-reservations")
    def reserve_task(task_id):
        current, error = require_participant()
        if error: return error
        try:
            return jsonify(work.reserve(task_id, current.pubkey, bool(learning.evidence.get(current.pubkey)))), 201
        except RuntimeError:
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
        if body.get("mime_type") not in {"image/png", "image/jpeg", "application/pdf", "video/mp4"} or int(body.get("size", 0)) > 10 * 1024 * 1024:
            return jsonify({"status": 422, "title": "Unsupported or oversized upload"}), 422
        return jsonify({"upload_id": uuid.uuid4().hex, "private": True, "owner": current.pubkey, "filename": body.get("filename")}), 201

    @app.get("/assignments/<assignment_id>")
    def assignment_detail(assignment_id):
        current, error = require_participant()
        if error: return error
        assignment = work.assignments.get(assignment_id)
        if not assignment:
            return jsonify({"status": 404, "title": "Not Found"}), 404
        if assignment["pubkey"] != current.pubkey:
            return jsonify({"status": 403, "title": "Forbidden"}), 403
        task = work.tasks.get(assignment["task_id"], {})
        return jsonify({"assignment": assignment, "task": task})

    @app.post("/assignments/<assignment_id>/submissions")
    def submit_assignment(assignment_id):
        current, error = require_participant()
        if error: return error
        body = request.get_json(silent=True) or {}
        try:
            return jsonify(work.submit(assignment_id, current.pubkey, body.get("content", ""), body.get("filename", "submission"), body.get("mime_type", "text/plain"))), 201
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
        auth.revoke(request.cookies.get("bluejet_session"))
        response = jsonify({"status": "revoked"})
        response.delete_cookie("bluejet_session")
        return response

    @app.get("/admin/review-queue")
    def review_queue():
        _, error = require_admin()
        if error: return error
        return jsonify({"items": [s for s in work.submissions if s.get("review_status") != "APPROVED"]})

    @app.post("/admin/submissions/<submission_id>/reviews")
    def review_submission(submission_id):
        _, error = require_admin()
        if error: return error
        body = request.get_json(silent=True) or {}
        try:
            review = finance.review(submission_id, body["decision"], body.get("reason", ""))
            if body["decision"] == "APPROVE":
                submission = next(s for s in work.submissions if s["id"] == submission_id)
                assignment = work.assignments[submission["assignment_id"]]; assignment["status"] = "APPROVED"
                obligation = finance.obligation(assignment["id"], work.tasks[assignment["task_id"]]["reward_sats"])
                return jsonify({"review": review, "payment_obligation": obligation}), 201
            return jsonify(review), 201
        except (KeyError, ValueError, StopIteration):
            return jsonify({"status": 400, "title": "invalid review"}), 400

    @app.get("/assignments/<assignment_id>/payment-obligation")
    def get_obligation(assignment_id):
        obligation = finance.obligations.get(assignment_id)
        return (jsonify(obligation), 200) if obligation else (jsonify({"status": 404, "title": "Not Found"}), 404)

    @app.post("/payment-obligations/<obligation_id>/payout-attempts")
    def create_attempt(obligation_id):
        body = request.get_json(silent=True) or {}
        try:
            return jsonify(finance.attempt(obligation_id, body["invoice"], request.headers.get("Idempotency-Key", ""))), 201
        except (KeyError, RuntimeError):
            return jsonify({"status": 409, "title": "active payout attempt exists or invalid request"}), 409

    @app.get("/payment-obligations/<obligation_id>/payout-status")
    def payout_status(obligation_id):
        current, error = require_participant()
        if error: return error
        obligation = next((item for item in finance.obligations.values() if item["id"] == obligation_id), None)
        if not obligation:
            return jsonify({"status": 404, "title": "Not Found"}), 404
        attempt = next((item for item in finance.attempts.values() if item["obligation_id"] == obligation_id), None)
        return jsonify({"obligation": obligation, "attempt": attempt, "mode": attempt.get("mode", "MOCK") if attempt else "MOCK"})

    @app.post("/admin/payout-attempts/<attempt_id>/reconcile")
    def reconcile(attempt_id):
        try: return jsonify(finance.settle(attempt_id))
        except KeyError: return jsonify({"status": 404, "title": "Not Found"}), 404

    @app.get("/receipts/<receipt_id>")
    def receipt(receipt_id):
        item = finance.receipts.get(receipt_id)
        return (jsonify(item), 200) if item else (jsonify({"status": 404, "title": "Not Found"}), 404)

    @app.get("/community/feed")
    def community_feed():
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
        try: return jsonify(community.post(current.pubkey, body["category"], body["content"], body.get("media_asset_id"))), 201
        except (KeyError, ValueError): return jsonify({"status": 400, "title": "invalid post"}), 400

    @app.post("/community/reports")
    def report():
        current, error = require_participant()
        if error: return error
        body = request.get_json(silent=True) or {}; item = {"id": uuid.uuid4().hex, "nostr_event_id": body.get("nostr_event_id"), "reporter": current.pubkey, "reason": body.get("reason", ""), "status": "OPEN"}; community.reports.append(item); return jsonify(item), 201

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
        return jsonify({"paid_tasks": [{**task, "type": "PAID_TASK"} for task in work.tasks.values() if task["status"] == "PUBLISHED"], "external_opportunities": [{**item, "type": "EXTERNAL_OPPORTUNITY"} for item in community.opportunities if item.get("status") == "PUBLISHED"]})

    @app.post("/admin/opportunities")
    def add_opportunity():
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
