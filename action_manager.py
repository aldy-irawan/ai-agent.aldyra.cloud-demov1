import json
import sqlite3
import subprocess
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel


# ============================================================
# ACTION MANAGER
# ============================================================

router = APIRouter(
    prefix="/action",
    tags=["Action Manager"]
)


# ============================================================
# CONFIGURATION
# ============================================================

ACTION_SCRIPT = "/usr/local/bin/ai_ec2_action.sh"

# Persistent proposal database.
# This prevents proposals from disappearing when the API service
# restarts and also allows /action/confirm to find proposals
# created by /action/propose.
PROPOSAL_DB = "/home/ubuntu/ai-agent/action_proposals.db"

ALLOWED_ACTIONS = {
    "stop"
}

VERIFICATION_TIMEOUT = 60
VERIFICATION_INTERVAL = 3


# ============================================================
# REQUEST MODELS
# ============================================================

class ActionProposalRequest(BaseModel):
    action: str
    instance_name: str


class ActionConfirmRequest(BaseModel):
    proposal_id: str


# ============================================================
# DATABASE
# ============================================================

def get_db():
    conn = sqlite3.connect(
        PROPOSAL_DB,
        timeout=10
    )

    conn.row_factory = sqlite3.Row

    return conn


def init_db():
    conn = get_db()

    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS action_proposals (
                proposal_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                status TEXT NOT NULL,
                proposal_json TEXT NOT NULL
            )
            """
        )

        conn.commit()

    finally:
        conn.close()


def save_proposal(proposal):
    conn = get_db()

    try:
        conn.execute(
            """
            INSERT INTO action_proposals (
                proposal_id,
                created_at,
                status,
                proposal_json
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                proposal["proposal_id"],
                proposal["created_at"],
                proposal["status"],
                json.dumps(proposal)
            )
        )

        conn.commit()

    finally:
        conn.close()


def load_proposal(proposal_id):
    conn = get_db()

    try:
        row = conn.execute(
            """
            SELECT
                proposal_json
            FROM action_proposals
            WHERE proposal_id = ?
            """,
            (proposal_id,)
        ).fetchone()

    finally:
        conn.close()

    if row is None:
        return None

    try:
        return json.loads(
            row["proposal_json"]
        )

    except Exception:
        return None


def update_proposal(proposal):
    conn = get_db()

    try:
        conn.execute(
            """
            UPDATE action_proposals
            SET
                status = ?,
                proposal_json = ?
            WHERE proposal_id = ?
            """,
            (
                proposal.get("status"),
                json.dumps(proposal),
                proposal["proposal_id"]
            )
        )

        conn.commit()

    finally:
        conn.close()


# Initialize database when module is loaded.
init_db()


# ============================================================
# HELPER - RUN ACTION SCRIPT
# ============================================================

def run_action_script(
    action,
    instance_name,
    timeout=30
):

    try:
        result = subprocess.run(
            [
                ACTION_SCRIPT,
                action,
                instance_name
            ],
            capture_output=True,
            text=True,
            timeout=timeout
        )

    except FileNotFoundError:
        raise HTTPException(
            status_code=500,
            detail=(
                "Action script not found: "
                f"{ACTION_SCRIPT}"
            )
        )

    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=504,
            detail=(
                f"EC2 {action.upper()} operation timed out"
            )
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=(
                f"Failed to execute EC2 "
                f"{action.upper()}: {str(e)}"
            )
        )

    return result


# ============================================================
# HELPER - PARSE CHECK OUTPUT
# ============================================================

def parse_check_output(output):

    instance_id = None
    current_state = None
    region = None
    instance_type = None
    private_ip = None
    instance_name = None

    for raw_line in output.splitlines():

        line = raw_line.strip()

        if line.startswith("Instance Name"):
            if ":" in line:
                instance_name = (
                    line.split(":", 1)[1].strip()
                )

        elif line.startswith("Instance ID"):
            if ":" in line:
                instance_id = (
                    line.split(":", 1)[1].strip()
                )

        elif line.startswith("Region"):
            if ":" in line:
                region = (
                    line.split(":", 1)[1].strip()
                )

        elif line.startswith("State"):
            if ":" in line:
                current_state = (
                    line.split(":", 1)[1].strip()
                )

        elif line.startswith("Instance Type"):
            if ":" in line:
                instance_type = (
                    line.split(":", 1)[1].strip()
                )

        elif line.startswith("Private IP"):
            if ":" in line:
                private_ip = (
                    line.split(":", 1)[1].strip()
                )

    return {
        "instance_name": instance_name,
        "instance_id": instance_id,
        "region": region,
        "current_state": current_state,
        "instance_type": instance_type,
        "private_ip": private_ip
    }


# ============================================================
# HELPER - VERIFY TARGET STATE
# ============================================================

def verify_instance_state(
    instance_name,
    expected_state,
    timeout=VERIFICATION_TIMEOUT,
    interval=VERIFICATION_INTERVAL
):
    import time

    deadline = time.monotonic() + timeout

    last_output = ""
    last_error = ""
    last_info = {}

    while time.monotonic() <= deadline:

        result = run_action_script(
            "check",
            instance_name,
            timeout=30
        )

        last_output = (
            result.stdout or ""
        ).strip()

        last_error = (
            result.stderr or ""
        ).strip()

        if result.returncode == 0:

            last_info = parse_check_output(
                last_output
            )

            current_state = (
                last_info.get(
                    "current_state"
                )
            )

            if current_state == expected_state:
                return {
                    "verified": True,
                    "state": current_state,
                    "info": last_info,
                    "output": last_output,
                    "error": last_error
                }

        time.sleep(interval)

    return {
        "verified": False,
        "state": last_info.get(
            "current_state"
        ),
        "info": last_info,
        "output": last_output,
        "error": last_error
    }


# ============================================================
# PROPOSE ACTION
# ============================================================

@router.post("/propose")
def propose_action(
    request: ActionProposalRequest
):

    action = (
        request.action or ""
    ).strip().lower()

    instance_name = (
        request.instance_name or ""
    ).strip()

    # --------------------------------------------------------
    # Validate action
    # --------------------------------------------------------

    if action not in ALLOWED_ACTIONS:

        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported action '{action}'. "
                f"Allowed actions: "
                f"{', '.join(sorted(ALLOWED_ACTIONS))}"
            )
        )

    # --------------------------------------------------------
    # Validate instance name
    # --------------------------------------------------------

    if not instance_name:

        raise HTTPException(
            status_code=400,
            detail="instance_name is required"
        )

    # --------------------------------------------------------
    # CHECK ONLY
    # --------------------------------------------------------

    result = run_action_script(
        "check",
        instance_name
    )

    check_output = (
        result.stdout or ""
    ).strip()

    check_error = (
        result.stderr or ""
    ).strip()

    # --------------------------------------------------------
    # CHECK FAILED
    # --------------------------------------------------------

    if result.returncode != 0:

        return {
            "status": "rejected",
            "proposal_id": None,
            "action": action,
            "instance_name": instance_name,
            "decision": "NOT SAFE",
            "requires_confirmation": False,
            "execution_allowed": False,
            "message": (
                "EC2 CHECK failed. "
                "Action proposal was not created."
            ),
            "check_output": check_output,
            "check_error": check_error
        }

    # --------------------------------------------------------
    # Parse instance information
    # --------------------------------------------------------

    instance_info = parse_check_output(
        check_output
    )

    current_state = (
        instance_info.get(
            "current_state"
        )
    )

    # --------------------------------------------------------
    # Safety check
    # --------------------------------------------------------

    if current_state != "running":

        return {
            "status": "rejected",
            "proposal_id": None,
            "action": action,
            "instance_name": instance_name,
            "instance_id": instance_info.get(
                "instance_id"
            ),
            "region": instance_info.get(
                "region"
            ),
            "current_state": current_state,
            "decision": "NOT SAFE",
            "requires_confirmation": False,
            "execution_allowed": False,
            "message": (
                "STOP proposal rejected because "
                "the instance is not RUNNING."
            ),
            "check_output": check_output
        }

    # ========================================================
    # CREATE PROPOSAL
    # ========================================================

    proposal_id = (
        "ACTION-"
        +
        uuid.uuid4().hex[:12].upper()
    )

    created_at = datetime.now(
        timezone.utc
    ).isoformat()

    proposal = {
        "proposal_id": proposal_id,
        "created_at": created_at,
        "action": action,
        "instance_name": instance_name,
        "instance_id": instance_info.get(
            "instance_id"
        ),
        "region": instance_info.get(
            "region"
        ),
        "current_state": current_state,
        "instance_type": instance_info.get(
            "instance_type"
        ),
        "private_ip": instance_info.get(
            "private_ip"
        ),
        "decision": "REVIEW",
        "requires_confirmation": True,
        "execution_allowed": False,
        "status": "pending"
    }

    # --------------------------------------------------------
    # IMPORTANT:
    # Persist proposal BEFORE returning the response.
    # --------------------------------------------------------

    save_proposal(proposal)

    # ========================================================
    # RESPONSE
    # ========================================================

    return {
        "status": "success",
        "proposal_id": proposal_id,
        "created_at": created_at,
        "action": action,
        "instance_name": instance_name,
        "instance_id": instance_info.get(
            "instance_id"
        ),
        "region": instance_info.get(
            "region"
        ),
        "current_state": current_state,
        "instance_type": instance_info.get(
            "instance_type"
        ),
        "private_ip": instance_info.get(
            "private_ip"
        ),
        "decision": "REVIEW",
        "requires_confirmation": True,
        "execution_allowed": False,
        "message": (
            "Action proposal created. "
            "Human confirmation is required "
            "before execution."
        )
    }


# ============================================================
# CONFIRM ACTION
# ============================================================

@router.post("/confirm")
def confirm_action(
    request: ActionConfirmRequest
):

    proposal_id = (
        request.proposal_id or ""
    ).strip()

    # --------------------------------------------------------
    # Load proposal from persistent storage
    # --------------------------------------------------------

    proposal = load_proposal(
        proposal_id
    )

    if proposal is None:

        raise HTTPException(
            status_code=404,
            detail=(
                f"Action proposal "
                f"'{proposal_id}' not found."
            )
        )

    # --------------------------------------------------------
    # Prevent duplicate execution
    # --------------------------------------------------------

    if proposal.get("status") != "pending":

        return {
            "status": "rejected",
            "proposal_id": proposal_id,
            "message": (
                "This action proposal is no longer "
                "pending and cannot be executed again."
            ),
            "execution_allowed": False,
            "proposal_status": proposal.get(
                "status"
            )
        }

    action = proposal.get("action")
    instance_name = proposal.get("instance_name")

    # --------------------------------------------------------
    # Safety: only allowed action
    # --------------------------------------------------------

    if action not in ALLOWED_ACTIONS:

        proposal["status"] = "rejected"

        update_proposal(proposal)

        return {
            "status": "rejected",
            "proposal_id": proposal_id,
            "message": "Action is not allowed.",
            "execution_allowed": False
        }

    # ========================================================
    # RE-CHECK INSTANCE BEFORE EXECUTION
    # ========================================================

    check_result = run_action_script(
        "check",
        instance_name
    )

    check_output = (
        check_result.stdout or ""
    ).strip()

    check_error = (
        check_result.stderr or ""
    ).strip()

    if check_result.returncode != 0:

        proposal["status"] = "rejected"
        proposal["rejected_at"] = datetime.now(
            timezone.utc
        ).isoformat()
        proposal["rejection_reason"] = (
            "Pre-execution EC2 CHECK failed."
        )

        update_proposal(proposal)

        return {
            "status": "rejected",
            "proposal_id": proposal_id,
            "message": (
                "Pre-execution EC2 CHECK failed. "
                "Execution was blocked."
            ),
            "execution_allowed": False,
            "check_output": check_output,
            "check_error": check_error
        }

    current_info = parse_check_output(
        check_output
    )

    current_state = (
        current_info.get(
            "current_state"
        )
    )

    # --------------------------------------------------------
    # Instance must still be running
    # --------------------------------------------------------

    if current_state != "running":

        proposal["status"] = "rejected"
        proposal["rejected_at"] = datetime.now(
            timezone.utc
        ).isoformat()
        proposal["rejection_reason"] = (
            "Instance is no longer RUNNING."
        )

        update_proposal(proposal)

        return {
            "status": "rejected",
            "proposal_id": proposal_id,
            "action": action,
            "instance_name": instance_name,
            "current_state": current_state,
            "decision": "NOT SAFE",
            "execution_allowed": False,
            "message": (
                "Execution blocked because the "
                "instance is no longer RUNNING."
            )
        }

    # ========================================================
    # EXECUTE ACTION
    # ========================================================

    execution_result = run_action_script(
        action,
        instance_name,
        timeout=60
    )

    execution_output = (
        execution_result.stdout or ""
    ).strip()

    execution_error = (
        execution_result.stderr or ""
    ).strip()

    # --------------------------------------------------------
    # Execution failed
    # --------------------------------------------------------

    if execution_result.returncode != 0:

        proposal["status"] = "execution_failed"
        proposal["execution_failed_at"] = (
            datetime.now(
                timezone.utc
            ).isoformat()
        )
        proposal["execution_error"] = (
            execution_error
        )

        update_proposal(proposal)

        return {
            "status": "execution_failed",
            "proposal_id": proposal_id,
            "action": action,
            "instance_name": instance_name,
            "execution_allowed": True,
            "message": (
                "Action execution failed."
            ),
            "execution_output": execution_output,
            "execution_error": execution_error
        }

    # ========================================================
    # VERIFY ACTION RESULT
    # ========================================================

    verification = verify_instance_state(
        instance_name,
        "stopped"
    )

    # --------------------------------------------------------
    # Verification failed
    # --------------------------------------------------------

    if not verification["verified"]:

        proposal["status"] = "verification_failed"
        proposal["verification_failed_at"] = (
            datetime.now(
                timezone.utc
            ).isoformat()
        )
        proposal["execution_output"] = (
            execution_output
        )
        proposal["verification_state"] = (
            verification.get("state")
        )

        update_proposal(proposal)

        return {
            "status": "verification_failed",
            "proposal_id": proposal_id,
            "action": action,
            "instance_name": instance_name,
            "instance_id": proposal.get(
                "instance_id"
            ),
            "region": proposal.get(
                "region"
            ),
            "previous_state": current_state,
            "decision": "APPROVED",
            "execution_allowed": True,
            "execution_status": "executed_but_not_verified",
            "verified_state": verification.get(
                "state"
            ),
            "message": (
                "EC2 action executed, but the final "
                "STOPPED state could not be verified."
            ),
            "execution_output": execution_output,
            "verification_output": verification.get(
                "output"
            ),
            "verification_error": verification.get(
                "error"
            )
        }

    # ========================================================
    # EXECUTION + VERIFICATION SUCCESS
    # ========================================================

    executed_at = datetime.now(
        timezone.utc
    ).isoformat()

    proposal["status"] = "executed"
    proposal["executed_at"] = executed_at
    proposal["verified_state"] = "stopped"

    update_proposal(proposal)

    return {
        "status": "success",
        "proposal_id": proposal_id,
        "action": action,
        "instance_name": instance_name,
        "instance_id": proposal.get(
            "instance_id"
        ),
        "region": proposal.get(
            "region"
        ),
        "previous_state": current_state,
        "decision": "APPROVED",
        "execution_allowed": True,
        "execution_status": "executed",
        "verified_state": "stopped",
        "message": (
            "Human confirmation received. "
            "EC2 action executed and final state "
            "verified successfully."
        ),
        "execution_output": execution_output,
        "verification_output": verification.get(
            "output"
        )
    }
