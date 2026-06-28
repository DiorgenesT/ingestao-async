# Importar todos os modelos aqui garante que estejam registrados no metadata
# antes que o Alembic ou o SQLAlchemy resolvam os relacionamentos.
from app.models.base import Base
from app.models.dataset import Dataset
from app.models.job import Job, StatusJob
from app.models.user import Usuario

__all__ = ["Base", "Dataset", "Job", "StatusJob", "Usuario"]
