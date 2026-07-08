import unittest
from unittest.mock import patch

from app.schemas import AnalysisResult
from app.services.llm_client import mock_analysis
from app.services.document_classifier import classify_document
from app.services.paper_analyzer import _build_prompt, analyze_paper
from app.services.pdf_parser import ParsedPaper


def parsed(text: str, title: str = "Test Document") -> ParsedPaper:
    return ParsedPaper(
        title=title,
        abstract="",
        sections=[],
        pages=[{"page": 1, "text": text}],
        full_text=text,
        page_count=1,
    )


class PaperAnalyzerTest(unittest.TestCase):
    def test_non_paper_returns_diagnostic_analysis_without_llm(self) -> None:
        document = parsed("这是一个恶搞 PDF，不是论文。哈哈哈 banana meme。没有实验也没有参考文献。 " * 30)

        with patch("app.services.paper_analyzer.analyze_with_llm") as analyze_with_llm:
            result = analyze_paper(document, [], "paper_only")

        analyze_with_llm.assert_not_called()
        self.assertIsInstance(result, AnalysisResult)
        self.assertFalse(result.metadata.is_academic_paper)
        self.assertEqual(result.metadata.domain, "non_academic")
        self.assertIn("不是可直接复现分析的研究论文", result.structured_summary.background)
        self.assertGreaterEqual(len(result.reproduction_checklist), 3)

    def test_prompt_includes_domain_adaptation_rules(self) -> None:
        text = """
        Quantum transport in superconducting lattice systems
        Abstract
        We measure electron scattering in a superconducting lattice and compare the spectrum
        with a Hamiltonian model. Introduction Methods Results Discussion References.
        The experiment records magnetic field response, phonon coupling, thermodynamic
        signatures, spectroscopy, spin interactions, and uncertainty estimates.
        [1] A. Smith et al., 2024.
        """ * 3
        document = parsed(text, title="Quantum transport")
        classification = classify_document(document)
        prompt = _build_prompt(document, [], "paper_only", [], {}, classification)

        self.assertEqual(classification.domain, "physics")
        self.assertIn('"domain": "physics"', prompt)
        self.assertIn("不要默认这是一篇计算机科学", prompt)
        self.assertIn("物理问题、理论假设、关键方程", prompt)

    def test_user_selected_domain_overrides_auto_classification(self) -> None:
        text = """
        Quantum transport in superconducting lattice systems
        Abstract
        We measure electron scattering in a superconducting lattice and compare the spectrum
        with a Hamiltonian model. Introduction Methods Results Discussion References.
        The experiment records magnetic field response, spectroscopy, spin interactions,
        uncertainty estimates, thermodynamic signatures, and phonon coupling.
        [1] A. Smith et al., 2024.
        """ * 3
        document = parsed(text, title="Quantum transport")

        with patch("app.services.paper_analyzer.analyze_with_llm") as analyze_with_llm:
            analyze_with_llm.side_effect = lambda prompt, schema_name: mock_analysis(schema_name=schema_name, prompt=prompt)
            result = analyze_paper(document, [], "paper_only", analysis_domain="mathematics")

        self.assertEqual(result.metadata.domain, "mathematics")
        self.assertIn("用户手动选择分析方向", "".join(result.metadata.signals))

    def test_non_cs_domain_ignores_code_repository_context(self) -> None:
        text = """
        Quantum transport in superconducting lattice systems
        Abstract
        We measure electron scattering in a superconducting lattice and compare the spectrum
        with a Hamiltonian model. Code is available at https://github.com/example/physics-code.
        Introduction Methods Results Discussion References.
        The experiment records magnetic field response, spectroscopy, spin interactions,
        uncertainty estimates, thermodynamic signatures, and phonon coupling.
        [1] A. Smith et al., 2024.
        """ * 3
        document = parsed(text, title="Quantum transport")
        resources = [{"type": "github", "url": "https://github.com/example/physics-code", "confidence": 0.96}]

        with patch("app.services.paper_analyzer.analyze_with_llm") as analyze_with_llm:
            analyze_with_llm.side_effect = lambda prompt, schema_name: mock_analysis(schema_name=schema_name, prompt=prompt)
            result = analyze_paper(
                document,
                resources,
                "with_detected_resources",
                repo_context={"available": True, "repo_url": "https://github.com/example/physics-code"},
                analysis_domain="physics",
            )

        self.assertEqual(result.metadata.domain, "physics")
        self.assertFalse(result.repo_guide.available)
        self.assertIn("不是计算机科学", result.repo_guide.message or "")


if __name__ == "__main__":
    unittest.main()
