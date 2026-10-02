"""Lecture de la file `summaries` : progression par sondage et estimation.

La table `summaries` sert de file entre l'application et
`oceens.summaries_generator_daemon`. `http_status` y porte à la fois l'état de
file et le résultat ; ce module est le seul lecteur à en connaître le codage :

- `0` : en attente ;
- `200` : synthèse générée ;
- toute autre valeur, NULL compris : échec.

Le module ne fait que lire. Il reçoit la session de l'appelant, ne la valide
jamais et ne lit aucune horloge : l'estimation se déduit du seul nombre de
travaux en attente. Une erreur de base remonte telle quelle à l'appelant.
"""

import math
from dataclasses import dataclass

from sqlmodel import case, func, select

from oceens.models import Summary

# Durée mesurée d'une synthèse, en secondes (Design Document v1, EPF-MDE/OceENS#115).
SECONDS_PER_JOB = 24

STATUS_PENDING = 0
STATUS_DONE = 200


@dataclass(frozen=True)
class SurveyProgress:
    """Avancement des synthèses d'un sondage. `total == done + failed + pending`."""

    total: int = 0
    done: int = 0
    failed: int = 0
    pending: int = 0

    @property
    def finished(self) -> bool:
        """Terminé : au moins une synthèse demandée, plus aucune en attente."""
        return self.total > 0 and self.pending == 0


@dataclass(frozen=True)
class QueueEstimate:
    """Temps estimé pour vider toute la file, tous sondages confondus."""

    seconds: int

    @property
    def label(self) -> str:
        """« N min » sous une heure, « H h MM » au-delà ; minutes arrondies au-dessus."""
        minutes = math.ceil(self.seconds / 60)
        if self.seconds < 3600:
            return f"{minutes} min"
        hours, minutes = divmod(minutes, 60)
        return f"{hours} h {minutes:02d}"


def survey_progress(session, survey_ids) -> dict[int, SurveyProgress]:
    """Avancement de chacun des sondages demandés.

    Chaque identifiant demandé a une entrée : un sondage sans synthèse vaut
    zéro partout et n'est pas terminé.
    """
    survey_ids = list(survey_ids)
    progress = {survey_id: SurveyProgress() for survey_id in survey_ids}
    if not survey_ids:
        return progress

    rows = session.exec(
        select(
            Summary.survey_id,
            func.count(Summary.summary_id),
            func.sum(case((Summary.http_status == STATUS_DONE, 1), else_=0)),
            func.sum(case((Summary.http_status == STATUS_PENDING, 1), else_=0)),
        )
        .where(Summary.survey_id.in_(survey_ids))
        .group_by(Summary.survey_id)
    ).all()

    for survey_id, total, done, pending in rows:
        progress[survey_id] = SurveyProgress(
            total=total,
            done=done,
            # Tout ce qui n'est ni fait ni en attente est un échec, NULL compris.
            failed=total - done - pending,
            pending=pending,
        )
    return progress


def queue_estimate(session) -> QueueEstimate:
    """Estimation pour tous les travaux en attente, de tous les sondages."""
    pending = session.exec(
        select(func.count(Summary.summary_id)).where(
            Summary.http_status == STATUS_PENDING
        )
    ).one()
    return QueueEstimate(seconds=pending * SECONDS_PER_JOB)
