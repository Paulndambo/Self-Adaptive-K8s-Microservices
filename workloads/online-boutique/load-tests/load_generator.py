from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


SOCKSHOP_GENERATOR = Path(__file__).resolve().parents[1].parent / "sockshop" / "load-tests" / "load_generator.py"
spec = importlib.util.spec_from_file_location("sockshop_load_generator", SOCKSHOP_GENERATOR)
module = importlib.util.module_from_spec(spec)
assert spec is not None and spec.loader is not None
sys.modules["sockshop_load_generator"] = module
spec.loader.exec_module(module)

LoadStep = module.LoadStep
RequestResult = module.RequestResult
LoadTestSummary = module.LoadTestSummary
run_load_test = module.run_load_test
perform_request = module.perform_request
percentile = module.percentile
write_summary = module.write_summary
add_common_args = module.add_common_args

DEFAULT_PATHS = (
    "/",
    "/product",
    "/cart",
    "/checkout",
)
