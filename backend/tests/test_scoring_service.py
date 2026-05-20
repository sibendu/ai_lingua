from app.services.scoring_service import ScoringService, tokenize


def test_tokenize_normalizes_accents_and_punctuation() -> None:
    assert tokenize("Ou est l'ecole ?") == ["ou", "est", "l'ecole"]


def test_scoring_excellent_match() -> None:
    result = ScoringService().score("Bonjour.", "bonjour")

    assert result.score >= 90
    assert result.label == "excellent"
    assert result.missing_words == []


def test_scoring_reports_missing_words() -> None:
    result = ScoringService().score("Je vais bien.", "je vais")

    assert result.score < 90
    assert "bien" in result.missing_words
