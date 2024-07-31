from typing import Any, List

import pytest
from langchain_core.documents import Document

from langchain_nvidia_ai_endpoints import ChatNVIDIA, NVIDIAEmbeddings, NVIDIARerank
from langchain_nvidia_ai_endpoints._statics import MODEL_TABLE, Model


def get_mode(config: pytest.Config) -> dict:
    nim_endpoint = config.getoption("--nim-endpoint")
    if nim_endpoint:
        return dict(base_url=nim_endpoint)
    return {}


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--chat-model-id",
        action="store",
        nargs="+",
        help="Run tests for a specific chat model or list of models",
    )
    parser.addoption(
        "--tool-model-id",
        action="store",
        nargs="+",
        help="Run tests for a specific chat models that support tool calling",
    )
    parser.addoption(
        "--qa-model-id",
        action="store",
        nargs="+",
        help="Run tests for a specific qa model or list of models",
    )
    parser.addoption(
        "--embedding-model-id",
        action="store",
        nargs="+",
        help="Run tests for a specific embedding model or list of models",
    )
    parser.addoption(
        "--rerank-model-id",
        action="store",
        nargs="+",
        help="Run tests for a specific rerank model or list of models",
    )
    parser.addoption(
        "--vlm-model-id",
        action="store",
        help="Run tests for a specific vlm model",
    )
    parser.addoption(
        "--all-models",
        action="store_true",
        help="Run tests across all models",
    )
    parser.addoption(
        "--nim-endpoint",
        type=str,
        help="Run tests using NIM mode",
    )


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    mode = get_mode(metafunc.config)

    def get_all_known_models() -> List[Model]:
        return list(MODEL_TABLE.values())

    if "chat_model" in metafunc.fixturenames:
        models = [ChatNVIDIA._default_model_name]
        if model_list := metafunc.config.getoption("chat_model_id"):
            models = model_list
        if metafunc.config.getoption("all_models"):
            models = [
                model.id
                for model in ChatNVIDIA(**mode).available_models
                if model.model_type == "chat"
            ]
        metafunc.parametrize("chat_model", models, ids=models)

    if "tool_model" in metafunc.fixturenames:
        models = ["meta/llama-3.1-8b-instruct"]
        if model_list := metafunc.config.getoption("tool_model_id"):
            models = model_list
        if metafunc.config.getoption("all_models"):
            models = [
                model.id
                for model in ChatNVIDIA(**mode).available_models
                if model.model_type == "chat" and model.supports_tools
            ]
        metafunc.parametrize("tool_model", models, ids=models)

    if "rerank_model" in metafunc.fixturenames:
        models = [NVIDIARerank._default_model_name]
        if model_list := metafunc.config.getoption("rerank_model_id"):
            models = model_list
        if metafunc.config.getoption("all_models"):
            models = [model.id for model in NVIDIARerank(**mode).available_models]
        metafunc.parametrize("rerank_model", models, ids=models)

    if "vlm_model" in metafunc.fixturenames:
        models = ["nvidia/neva-22b"]
        if model := metafunc.config.getoption("vlm_model_id"):
            models = [model]
        if metafunc.config.getoption("all_models"):
            models = [
                model.id
                for model in get_all_known_models()
                if model.model_type == "vlm"
            ]
        metafunc.parametrize("vlm_model", models, ids=models)

    if "qa_model" in metafunc.fixturenames:
        models = []
        if model_list := metafunc.config.getoption("qa_model_id"):
            models = model_list
        if metafunc.config.getoption("all_models"):
            models = [
                model.id
                for model in ChatNVIDIA(**mode).available_models
                if model.model_type == "qa"
            ]
        metafunc.parametrize("qa_model", models, ids=models)

    if "embedding_model" in metafunc.fixturenames:
        models = [NVIDIAEmbeddings._default_model_name]
        if metafunc.config.getoption("all_models"):
            models = [model.id for model in NVIDIAEmbeddings(**mode).available_models]
        if model_list := metafunc.config.getoption("embedding_model_id"):
            models = model_list
        if metafunc.config.getoption("all_models"):
            models = [model.id for model in NVIDIAEmbeddings(**mode).available_models]
        metafunc.parametrize("embedding_model", models, ids=models)


@pytest.fixture
def mode(request: pytest.FixtureRequest) -> dict:
    return get_mode(request.config)


@pytest.fixture(
    params=[
        ChatNVIDIA,
        NVIDIAEmbeddings,
        NVIDIARerank,
    ]
)
def public_class(request: pytest.FixtureRequest) -> type:
    return request.param


@pytest.fixture
def contact_service() -> Any:
    def _contact_service(instance: Any) -> None:
        if isinstance(instance, ChatNVIDIA):
            instance.invoke("Hello")
        elif isinstance(instance, NVIDIAEmbeddings):
            instance.embed_documents(["Hello"])
        elif isinstance(instance, NVIDIARerank):
            instance.compress_documents(
                documents=[Document(page_content="World")], query="Hello"
            )

    return _contact_service
