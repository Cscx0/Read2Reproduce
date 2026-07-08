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
