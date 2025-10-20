def _run_cmd(eval_md, tools_mode, engine):
    return "buck2 run //:llm_eval -- run {} --tools {} --engine {}".format(eval_md, tools_mode, engine)

def llm_eval_eval(name, eval_md, tools_mode = "mock", engine = "chat"):
    native.sh_test(
        name = name,
        test = "bash",
        args = ["-lc", _run_cmd(eval_md, tools_mode, engine)],
        labels = ["llm_eval", tools_mode, engine],
    )

def llm_eval_suite(name, evals_glob, tools_mode = "mock", engine = "chat"):
    for p in native.glob(evals_glob):
        short = p.split("/")[-1].replace(".md", "")
        llm_eval_eval(
            name = "{}__{}".format(name, short),
            eval_md = p,
            tools_mode = tools_mode,
            engine = engine,
        )
