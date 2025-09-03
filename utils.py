from flask import Request


def request_to_sanitized_json(req: Request) -> dict:
    """
    Convert a Flask request into a safe JSON-serializable dict (should not contain any sensitive data)."""
    return {
        "method": req.method,
        "path": req.path,
        "query": req.args.to_dict(flat=True),  # type: ignore
        "form": req.form.to_dict(flat=True) if req.form else None,  # type: ignore
        "json": req.get_json(silent=True) if req.is_json else None,
        "ip": req.headers.get("X-Forwarded-For", req.remote_addr),
        "user_agent": req.user_agent.string,
    }
