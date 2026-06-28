from sqlalchemy import inspect

from app.models.dataset import Dataset
from app.models.job import Job, StatusJob
from app.models.user import Usuario


def test_modelo_usuario_tem_colunas_obrigatorias() -> None:
    cols = {c.key for c in inspect(Usuario).mapper.column_attrs}
    assert {"id", "email", "hash_senha", "criado_em", "ativo"}.issubset(cols)


def test_modelo_usuario_tem_relacionamento_jobs() -> None:
    rels = {r.key for r in inspect(Usuario).mapper.relationships}
    assert "jobs" in rels


def test_modelo_job_tem_colunas_fila() -> None:
    cols = {c.key for c in inspect(Job).mapper.column_attrs}
    assert {
        "id",
        "tipo",
        "payload",
        "status",
        "tentativas",
        "max_tentativas",
        "locked_until",
        "erro",
        "criado_em",
        "atualizado_em",
    }.issubset(cols)


def test_status_job_tem_todos_os_estados() -> None:
    assert set(StatusJob) == {
        StatusJob.PENDENTE,
        StatusJob.PROCESSANDO,
        StatusJob.CONCLUIDO,
        StatusJob.FALHOU,
        StatusJob.MORTO,
    }


def test_modelo_dataset_tem_colunas_obrigatorias() -> None:
    cols = {c.key for c in inspect(Dataset).mapper.column_attrs}
    assert {"id", "job_id", "nome", "resumo", "criado_em"}.issubset(cols)


def test_modelo_job_tem_relacionamentos_corretos() -> None:
    rels = {r.key for r in inspect(Job).mapper.relationships}
    assert {"usuario", "dataset"}.issubset(rels)
