import pytest
from unittest.mock import patch, MagicMock
from src.models.schemas import AgentOutput

def test_translation_returns_agent_output(tmp_path, monkeypatch):
    monkeypatch.setattr("src.agents.translation_agent.MODELS_DIR", tmp_path)

    mock_tokenizer = MagicMock()
    mock_tokenizer.return_value = {"input_ids": MagicMock(), "attention_mask": MagicMock()}
    mock_tokenizer.decode = MagicMock(return_value="Bonjour le monde")
    mock_model = MagicMock()
    mock_model.generate = MagicMock(return_value=[[1, 2, 3]])

    fake_model_dir = tmp_path / "Helsinki-NLP_opus-mt-en-fr"
    fake_model_dir.mkdir()

    with patch("src.agents.translation_agent.MarianTokenizer.from_pretrained", return_value=mock_tokenizer), \
         patch("src.agents.translation_agent.MarianMTModel.from_pretrained", return_value=mock_model):
        from src.agents.translation_agent import run_translation_agent
        result = run_translation_agent("Hello world", source_lang="EN", target_lang="FR")

    assert isinstance(result, AgentOutput)
    assert result.agent_name == "TranslationAgent"
    assert len(result.content) > 0

def test_translation_raises_if_model_not_downloaded(tmp_path, monkeypatch):
    monkeypatch.setattr("src.agents.translation_agent.MODELS_DIR", tmp_path)
    from src.agents.translation_agent import run_translation_agent
    with pytest.raises(RuntimeError, match="not downloaded"):
        run_translation_agent("Hello", source_lang="EN", target_lang="JP")
