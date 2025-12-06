from app.services.sentiment_service import SentimentAnalyzer


def test_positive_with_intensifier_and_keywords():
    text = "Muy buen servicio y atención excelente!"

    result = SentimentAnalyzer.analyze(text)

    assert result["polarity_label"] == "positivo"
    assert result["intensity"] >= 60
    assert result["satisfaction"] >= 80
    assert "buen" in result["keywords"]["positives"]
    assert "excelente" in result["keywords"]["positives"]


def test_negation_changes_polarity():
    text = "No es bueno, estoy enojado"

    result = SentimentAnalyzer.analyze(text)

    assert result["polarity"] < 0
    assert result["polarity_label"] == "negativo"
    assert "bueno" in result["keywords"]["negatives"] or "enojado" in result["keywords"]["negatives"]


def test_neutral_when_no_keywords():
    text = "El producto existe"

    result = SentimentAnalyzer.analyze(text)

    assert result["polarity_label"] == "neutral"
    assert 40 <= result["satisfaction"] <= 60
    assert result["keywords"] == {"positives": [], "negatives": []}
