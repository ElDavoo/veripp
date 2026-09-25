"""contracts.hpp outside the checker.

The header is included by C sources as well as C++ ones, and a project keeps
its VERIPP_REQUIRES/VERIPP_ENSURES in code that is also built normally. So it
has to compile in an ordinary build of either language: with
VERIPP_RUNTIME_CHECKS the contracts become asserts, and without it they
become nothing. It included <cassert>, so every C build with runtime checks
failed on the include itself.
"""

import shutil
import subprocess

import pytest

from veripp.paths import contracts_include_dir

SOURCE = (
    '#include "veripp/contracts.hpp"\n'
    "int half(int x) { VERIPP_REQUIRES(x >= 0); return x / 2; }\n"
    "int main(void) { return half(-1); }\n"
)

COMPILERS = {"c": ("cc", "gcc", "clang"), "c++": ("c++", "g++", "clang++")}
SUFFIXES = {"c": ".c", "c++": ".cpp"}


def _run(tmp_path, language: str, *flags: str) -> subprocess.CompletedProcess:
    compiler = next((found for name in COMPILERS[language]
                     if (found := shutil.which(name))), None)
    if compiler is None:
        pytest.skip(f"no {language} compiler")
    src = tmp_path / f"uses_contracts{SUFFIXES[language]}"
    src.write_text(SOURCE, encoding="utf-8")
    exe = tmp_path / "uses_contracts"
    built = subprocess.run(
        [compiler, *flags, "-I", str(contracts_include_dir()), str(src), "-o", str(exe)],
        capture_output=True, text=True,
    )
    assert built.returncode == 0, built.stderr
    return subprocess.run([str(exe)], capture_output=True, text=True)


@pytest.mark.parametrize("language", ["c", "c++"])
def test_runtime_checks_compile_and_fire(tmp_path, language):
    ran = _run(tmp_path, language, "-DVERIPP_RUNTIME_CHECKS")
    assert ran.returncode != 0, "the violated precondition did not stop the program"


@pytest.mark.parametrize("language", ["c", "c++"])
def test_without_runtime_checks_the_contracts_vanish(tmp_path, language):
    assert _run(tmp_path, language).returncode == 0
