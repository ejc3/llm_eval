load("//starlark:llm_eval_macros.bzl", "llm_eval_eval", "llm_eval_suite")

python_binary(
    name = "llm_eval",
    srcs = glob(["src/py/llm_eval/**/*.py"]),
    main_module = "llm_eval.cli",
)

# Macro-generated smoke targets (mock mode)
llm_eval_eval(
    name = "job_monitor_mock",
    eval_md = "evals/job_monitor.md",
    tools_mode = "mock",
)
llm_eval_eval(
    name = "canary_mock",
    eval_md = "evals/canary_observe_readonly.md",
    tools_mode = "mock",
)

# Test targets
python_test(
    name = "unit_tests",
    srcs = glob(["tests/*.py"]),
)
sh_test(
    name = "unit_tests_sh",
    test = "scripts/run_unit_tests.sh",
    labels = ["llm_eval", "tests"],
)

# Suite: one run target per eval (mock)
llm_eval_suite(
    name = "all_evals_mock",
    evals_glob = ["evals/*.md"],
    tools_mode = "mock",
)
