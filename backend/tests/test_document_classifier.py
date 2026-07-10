import unittest

from app.services.document_classifier import classify_document
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


class DocumentClassifierTest(unittest.TestCase):
    def test_detects_physics_research_paper(self) -> None:
        text = """
        Quantum transport in superconducting lattice systems
        Abstract
        We measure electron scattering in a superconducting lattice and compare the observed
        spectrum with a Hamiltonian model. The experiment records magnetic field response,
        phonon coupling, and thermodynamic signatures across several temperatures.
        Introduction
        Prior work on condensed matter systems [1] suggests that spin interactions modify
        the wavefunction near the phase boundary.
        Methods
        The sample is cooled in a cryostat, calibrated with reference spectra, and measured
        by spectroscopy under varying magnetic field strengths.
        Results
        We report the uncertainty of fitted parameters and compare the observations with
        theoretical predictions.
        References
        [1] A. Smith et al. Physical Review Letters, 2023.
        """ * 2

        result = classify_document(parsed(text))

        self.assertTrue(result.is_academic_paper)
        self.assertEqual(result.domain, "physics")
        self.assertIn(result.document_type, {"research_paper", "academic_like_document"})

    def test_computational_chemistry_is_not_misclassified_as_computer_science(self) -> None:
        text = """
        ANI-1: an extensible neural network potential with DFT accuracy at force field computational cost
        Abstract
        We introduce a neural network potential for organic molecules trained on density functional theory data.
        The work studies molecular conformations, atomistic potential energy surfaces, force fields, chemical
        accuracy, and quantum chemistry benchmarks. Introduction Methods Results Discussion References.
        Experiments compare molecular energies against DFT and ab initio calculations for chemical compounds.
        [1] A. Smith et al., Journal of Chemical Physics, 2024.
        """ * 3

        result = classify_document(parsed(text, title="ANI-1 neural network potential"))

        self.assertTrue(result.is_academic_paper)
        self.assertEqual(result.domain, "chemistry")

    def test_computational_method_does_not_override_subject_domain(self) -> None:
        examples = [
            (
                "economics",
                """
                How inductive bias in machine learning aligns with optimality in economic dynamics
                Abstract
                We study economic dynamics, welfare, market equilibrium and optimality using machine learning tools.
                Introduction Methods Results Discussion References. The analysis concerns policy and economic models.
                [1] A. Smith et al., 2024.
                """,
            ),
            (
                "engineering",
                """
                Digital twinning of self-sensing structures using the statistical finite element method
                Abstract
                This engineering paper studies structural sensors, finite element models, digital twins and
                self-sensing structures. A neural surrogate is used only as a computational tool.
                Introduction Methods Results Discussion References.
                [1] A. Smith et al., 2024.
                """,
            ),
            (
                "humanities",
                """
                A digital historian and digital humanities methodology for discovering the past
                Abstract
                This historical study discusses archival evidence, historians, textual analysis and digital humanities.
                Machine learning is mentioned as one tool for metadata exploration.
                Introduction Methods Results Discussion References.
                [1] A. Smith et al., 2024.
                """,
            ),
            (
                "social_science",
                """
                Computational reproducibility in computational social science
                Abstract
                We study social science reproducibility, survey data, participants and coding practices.
                The paper uses computational methods but the research domain is social science.
                Introduction Methods Results Discussion References.
                [1] A. Smith et al., 2024.
                """,
            ),
        ]

        for expected_domain, text in examples:
            with self.subTest(expected_domain=expected_domain):
                result = classify_document(parsed(text))
                self.assertEqual(result.domain, expected_domain)

    def test_detects_non_academic_joke_text(self) -> None:
        text = ("这是一个恶搞 PDF，不是论文。哈哈哈 banana meme。没有摘要、方法、实验、参考文献，只是在整活。 " * 20)

        result = classify_document(parsed(text, title="Just a Joke"))

        self.assertFalse(result.is_academic_paper)
        self.assertEqual(result.domain, "non_academic")
        self.assertIn("非论文", "".join(result.warnings))

    def test_detects_unreadable_pdf_text(self) -> None:
        result = classify_document(parsed("   "))

        self.assertFalse(result.is_academic_paper)
        self.assertEqual(result.document_type, "empty_or_unreadable")


if __name__ == "__main__":
    unittest.main()
