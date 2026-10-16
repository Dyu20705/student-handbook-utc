from student_handbook_rag.chain import GroundedAnswer, create_llm
from student_handbook_rag.config import LLM_MODEL, MAX_OUTPUT_TOKENS


def test_generation_settings_preserve_qualified_baseline():
    llm = create_llm()
    assert llm.model == LLM_MODEL
    assert llm.temperature == 0
    assert llm.num_ctx == 8192
    assert llm.num_predict == MAX_OUTPUT_TOKENS
    assert llm.reasoning is False
    assert llm.format == GroundedAnswer.model_json_schema()
