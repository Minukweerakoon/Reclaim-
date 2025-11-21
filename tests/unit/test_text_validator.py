import pytest
from unittest.mock import MagicMock, patch
from src.text.validator import TextValidator

# Mock external dependencies
@pytest.fixture
def mock_spacy_load():
    with patch('src.text.validator.spacy.load') as mock:
        mock_nlp = MagicMock()
        mock_nlp.return_value.sents = [MagicMock(text="sentence1"), MagicMock(text="sentence2")]
        mock_nlp.return_value.ents = [MagicMock(text="entity1", label_="LOC")]
        mock.return_value = mock_nlp
        yield mock

@pytest.fixture
def mock_sentence_transformer():
    with patch('src.text.validator.SentenceTransformer') as mock:
        mock_instance = MagicMock()
        mock_instance.encode.return_value = [[0.1, 0.2], [0.3, 0.4]] # Dummy embeddings
        mock.return_value = mock_instance
        yield mock

@pytest.fixture
def mock_transformers():
    with patch('src.text.validator.AutoTokenizer.from_pretrained') as mock_tokenizer,
         patch('src.text.validator.AutoModel.from_pretrained') as mock_model:
        mock_tokenizer.return_value = MagicMock()
        mock_model.return_value = MagicMock()
        yield mock_tokenizer, mock_model

@pytest.fixture
def text_validator(mock_spacy_load, mock_sentence_transformer, mock_transformers):
    validator = TextValidator(enable_logging=False)
    return validator

class TestTextValidator:

    def test_init(self, mock_spacy_load, mock_sentence_transformer, mock_transformers):
        validator = TextValidator(enable_logging=False)
        mock_spacy_load.assert_called()
        mock_sentence_transformer.assert_called_once()
        mock_transformers[0].assert_called_once() # AutoTokenizer
        mock_transformers[1].assert_called_once() # AutoModel

    def test_check_completeness_complete(self, text_validator):
        text = "I lost my red phone in the library."
        result = text_validator.check_completeness(text, 'en')
        assert result['valid'] is True
        assert result['score'] == 1.0 # 0.4 (item) + 0.3 (color) + 0.3 (location)
        assert "phone" in result['entities']['item_type']
        assert "red" in result['entities']['color']
        assert "library" in result['entities']['location']
        assert not result['missing_info']
        assert "Description contains all required elements" in result['feedback']

    def test_check_completeness_incomplete(self, text_validator):
        text = "I lost something."
        result = text_validator.check_completeness(text, 'en')
        assert result['valid'] is False
        assert result['score'] == 0.0
        assert "item type" in result['missing_info']
        assert "color" in result['missing_info']
        assert "location" in result['missing_info']
        assert "Description is incomplete" in result['feedback']

    def test_check_semantic_coherence_coherent(self, text_validator, mock_spacy_load, mock_sentence_transformer):
        text = "I lost my phone. It was red."
        # Mock sentence transformer to return high similarity
        mock_sentence_transformer.return_value.encode.return_value = [[0.5, 0.5], [0.4, 0.6]]
        # Mock BERT model outputs for aux_signal
        text_validator.bert_model.return_value.attentions = [torch.rand(1, 1, 5, 5)]

        result = text_validator.check_semantic_coherence(text, 'en')
        assert result['valid'] is True
        assert result['score'] >= text_validator.coherence_threshold
        assert "Description is semantically coherent" in result['feedback']

    def test_check_semantic_coherence_incoherent(self, text_validator, mock_spacy_load, mock_sentence_transformer):
        text = "I lost my phone. The sky is blue."
        # Mock sentence transformer to return low similarity
        mock_sentence_transformer.return_value.encode.return_value = [[0.1, 0.9], [0.9, 0.1]]
        # Mock BERT model outputs for aux_signal
        text_validator.bert_model.return_value.attentions = [torch.rand(1, 1, 5, 5)]

        result = text_validator.check_semantic_coherence(text, 'en')
        assert result['valid'] is False
        assert result['score'] < text_validator.coherence_threshold
        assert "Description lacks semantic coherence" in result['feedback']

    def test_extract_entities(self, text_validator):
        text = "I lost my red iPhone in the library."
        result = text_validator.extract_entities(text, 'en')
        assert len(result['entities']) > 0
        assert "iPhone" in result['item_mentions']
        assert "red" in result['color_mentions']
        assert "library" in result['location_mentions']

    def test_validate_text_overall_valid(self, text_validator):
        text = "I lost my red phone in the library. It was a new model."
        # Mock sub-methods to return valid results
        text_validator.check_completeness = MagicMock(return_value={'valid': True, 'score': 1.0, 'entities': {}, 'missing_info': [], 'feedback': 'Complete'})
        text_validator.check_semantic_coherence = MagicMock(return_value={'valid': True, 'score': 0.8, 'feedback': 'Coherent'})
        text_validator.extract_entities = MagicMock(return_value={'entities': [], 'item_mentions': ['phone'], 'color_mentions': ['red'], 'location_mentions': ['library']})

        result = text_validator.validate_text(text, 'en')
        assert result['valid'] is True
        assert result['overall_score'] >= 0.7
        assert result['text'] == text
        assert 'timestamp' in result
        assert result['completeness']['valid'] is True
        assert result['coherence']['valid'] is True

    def test_validate_text_overall_invalid(self, text_validator):
        text = "Lost something."
        # Mock sub-methods to return invalid results
        text_validator.check_completeness = MagicMock(return_value={'valid': False, 'score': 0.0, 'entities': {}, 'missing_info': ['item type'], 'feedback': 'Incomplete'})
        text_validator.check_semantic_coherence = MagicMock(return_value={'valid': False, 'score': 0.3, 'feedback': 'Incoherent'})
        text_validator.extract_entities = MagicMock(return_value={'entities': [], 'item_mentions': [], 'color_mentions': [], 'location_mentions': []})

        result = text_validator.validate_text(text, 'en')
        assert result['valid'] is False
        assert result['overall_score'] < 0.7
        assert result['text'] == text
        assert 'timestamp' in result
        assert result['completeness']['valid'] is False
        assert result['coherence']['valid'] is False
