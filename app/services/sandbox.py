import httpx

from app.config import settings


class SandboxError(Exception):
    pass


async def run_python(code: str, stdin: str = "") -> dict:
    """
    Sends code to the Piston execution engine and returns stdout/stderr/exit
    code. Piston runs each submission in its own isolated container with
    CPU/memory/time limits and no network access — matching the "server-side
    sandboxed containers" decision from the PRD without us having to build
    and secure that isolation layer ourselves.

    In production, point PISTON_URL at your own deployed instance
    (see DEPLOYMENT.md, Step 4) rather than a public one, both for
    reliability and so you control the resource limits.
    """
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(
            f"{settings.piston_url}/execute",
            json={
                "language": "python",
                "version": "3.10.0",
                "files": [{"name": "main.py", "content": code}],
                "stdin": stdin,
            },
        )
    if response.status_code != 200:
        raise SandboxError(f"Sandbox returned {response.status_code}: {response.text}")

    data = response.json()
    run = data.get("run", {})
    return {
        "stdout": run.get("stdout", ""),
        "stderr": run.get("stderr", ""),
        "exit_code": run.get("code", -1),
    }


def check_output(actual_stdout: str, expected_output: str) -> bool:
    """Exact-match comparison, trimmed. Good enough for beginner exercises;
    fuzzier matching (whitespace/float tolerance) is a Phase 6+ refinement."""
    return actual_stdout.strip() == expected_output.strip()
