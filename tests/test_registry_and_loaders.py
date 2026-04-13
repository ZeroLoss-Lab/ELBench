import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from elbench.config import load_project_config
from elbench.loaders import LoaderFactory
from elbench.registry import FileRegistry


class RegistryAndLoaderSmokeTest(unittest.TestCase):
    def test_registry_resolves_all_current_files(self) -> None:
        config = load_project_config(Path("configs"))
        registry = FileRegistry(config)
        resolved = registry.resolve()
        self.assertEqual(len(resolved), 8)

    def test_loaders_produce_samples(self) -> None:
        config = load_project_config(Path("configs"))
        registry = FileRegistry(config)
        resolved = registry.resolve()
        for item in resolved:
            loader = LoaderFactory.create(item.entry.loader_name)
            sample = next(iter(loader.iter_samples(item)))
            self.assertTrue(sample.prompt)
            self.assertEqual(sample.source_file, item.entry.canonical_name)

    def test_highlevel_omni_dimension_is_parsed_from_field(self) -> None:
        config = load_project_config(Path("configs"))
        registry = FileRegistry(config)
        resolved = registry.resolve(modules={"高阶育人"}, subsets={"omni"})
        loader = LoaderFactory.create(resolved[0].entry.loader_name)
        sample = next(iter(loader.iter_samples(resolved[0])))
        self.assertTrue(sample.dimension)

    def test_mmlu_pro_sampled_uses_zero_shot_prompt(self) -> None:
        config = load_project_config(Path("configs"))
        registry = FileRegistry(config)
        resolved = registry.resolve(source_files={"mmlu_pro_sampled.jsonl"})
        self.assertEqual(len(resolved), 1)
        loader = LoaderFactory.create(resolved[0].entry.loader_name)
        sample = next(iter(loader.iter_samples(resolved[0])))

        self.assertEqual(sample.module, "通用模型")
        self.assertEqual(sample.task, "mmlu_pro")
        self.assertEqual(sample.dimension, "law")
        self.assertNotIn("What is the judge ad hoc?", sample.prompt)
        self.assertIn("A woman was standing in the aisle of a subway car", sample.prompt)
        self.assertIn("A) Fraud, because he took the purse without the woman's consent.", sample.prompt)
        self.assertIn("J) Robbery, because he physically took the purse from the woman's presence.", sample.prompt)
        self.assertIn("ANSWER: [LETTER]", sample.prompt)
        self.assertEqual((sample.reference or {}).get("target"), "D")


if __name__ == "__main__":
    unittest.main()
