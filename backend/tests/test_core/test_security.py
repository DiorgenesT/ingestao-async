import pytest

from app.core.security import (
    criar_access_token,
    criar_refresh_token,
    decodificar_token,
    gerar_hash_senha,
    verificar_senha,
)


def test_hash_senha_e_diferente_da_senha_original() -> None:
    hash_ = gerar_hash_senha("minhasenha123")
    assert hash_ != "minhasenha123"


def test_verificar_senha_correta_retorna_true() -> None:
    hash_ = gerar_hash_senha("minhasenha123")
    assert verificar_senha("minhasenha123", hash_) is True


def test_verificar_senha_errada_retorna_false() -> None:
    hash_ = gerar_hash_senha("minhasenha123")
    assert verificar_senha("errada", hash_) is False


def test_criar_e_decodificar_access_token() -> None:
    token = criar_access_token(subject="usuario-id-123")
    payload = decodificar_token(token)
    assert payload["sub"] == "usuario-id-123"
    assert payload["tipo"] == "access"


def test_criar_e_decodificar_refresh_token() -> None:
    token = criar_refresh_token(subject="usuario-id-456")
    payload = decodificar_token(token)
    assert payload["sub"] == "usuario-id-456"
    assert payload["tipo"] == "refresh"


def test_token_invalido_levanta_excecao() -> None:
    with pytest.raises(ValueError, match="Token invalido"):
        decodificar_token("token.invalido.aqui")


def test_tokens_access_e_refresh_sao_distintos() -> None:
    access = criar_access_token(subject="id-789")
    refresh = criar_refresh_token(subject="id-789")
    assert access != refresh
