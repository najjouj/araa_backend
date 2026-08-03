import os
import resource
import subprocess
import tempfile

# Hard caps applied to every submission. These are deliberately tight —
# beginner exercises finish in milliseconds; anything hitting these limits
# is either an infinite loop, a runaway allocation, or actively hostile code.
TIMEOUT_SECONDS = 5
MEMORY_LIMIT_BYTES = 100 * 1024 * 1024  # 100 MB
CPU_TIME_LIMIT_SECONDS = 5


class SandboxError(Exception):
    pass


def _limit_resources():
    """
    Runs in the child process before exec, via subprocess's preexec_fn.
    Caps CPU time and memory so a submission can't consume the host
    container's resources, and disables core dumps.

    Important honesty note: this is NOT equivalent to Piston's real
    container-per-run isolation. The child process still shares the same
    filesystem and network namespace as the backend itself — there is no
    process/network isolation here, only resource limits and a timeout.
    This is a reasonable tradeoff for a classroom/prototype setting with
    trusted users, but it is not safe as a public, fully-untrusted-code
    execution service. If this platform ever opens up to anonymous /
    fully public submissions at scale, revisit real container isolation
    (Piston, gVisor, Firecracker) rather than relying on this alone.
    """
    resource.setrlimit(resource.RLIMIT_CPU, (CPU_TIME_LIMIT_SECONDS, CPU_TIME_LIMIT_SECONDS))
    resource.setrlimit(resource.RLIMIT_AS, (MEMORY_LIMIT_BYTES, MEMORY_LIMIT_BYTES))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))


async def run_python(code: str, stdin: str = "") -> dict:
    """
    Runs student code as a constrained local subprocess and returns
    stdout/stderr/exit code — same return shape as the previous Piston-based
    implementation, so callers (app/routers/exercises.py) don't need to change.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        script_path = os.path.join(tmp_dir, "main.py")
        with open(script_path, "w") as f:
            f.write(code)

        try:
            result = subprocess.run(
                ["python3", script_path],
                input=stdin,
                capture_output=True,
                text=True,
                timeout=TIMEOUT_SECONDS,
                cwd=tmp_dir,
                preexec_fn=_limit_resources,
                env={"PATH": os.environ.get("PATH", "/usr/bin:/bin")},
            )
        except subprocess.TimeoutExpired:
            return {
                "stdout": "",
                "stderr": f"Execution timed out after {TIMEOUT_SECONDS} seconds.",
                "exit_code": -1,
            }
        except Exception as exc:
            raise SandboxError(f"Local sandbox failed to run: {exc}")

        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode,
        }


def check_output(actual_stdout: str, expected_output: str) -> bool:
    """Exact-match comparison, trimmed. Good enough for beginner exercises;
    fuzzier matching (whitespace/float tolerance) is a later refinement."""
    return actual_stdout.strip() == expected_output.strip()
