# Importar todos os modelos para garantir que os relacionamentos sejam registrados
from app.models.company import Company
from app.models.scrape_log import ScrapeLog
from app.models.aum_snapshot import AUMSnapshot
from app.models.usage import Usage

# Adicionar relacionamentos
from sqlalchemy.orm import relationship

# Relacionamentos para Company
Company.scrape_logs = relationship("ScrapeLog", back_populates="company")
Company.aum_snapshots = relationship("AUMSnapshot", back_populates="company")

# Relacionamentos já definidos nos modelos individuais
# ScrapeLog.company já está definido
# AUMSnapshot.company já está definido

__all__ = ["Company", "ScrapeLog", "AUMSnapshot", "Usage"]