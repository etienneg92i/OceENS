"""Lecture de la file `summaries` : progression par sondage et estimation (spec #144)."""

import pytest
from sqlmodel import Session, SQLModel, create_engine

from oceens.models import Summary
from oceens.services.summary_queue import queue_estimate, survey_progress


@pytest.fixture
def session():
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def add_summaries(session, survey_id, statuses):
    for status in statuses:
        session.add(Summary(survey_id=survey_id, http_status=status))
    session.commit()


def test_ten_surveys_of_45_pending_jobs_take_3_h_00(session):
    for survey_id in range(1, 11):
        add_summaries(session, survey_id, [0] * 45)

    estimate = queue_estimate(session)

    assert estimate.seconds == 10_800
    assert estimate.label == "3 h 00"


def test_one_survey_of_45_pending_jobs_takes_18_min(session):
    add_summaries(session, 1, [0] * 45)

    estimate = queue_estimate(session)

    assert estimate.seconds == 1_080
    assert estimate.label == "18 min"


def test_progress_of_a_survey_with_mixed_rows(session):
    add_summaries(session, 1, [0, 0, 200, 200, 200, 504, None])

    progress = survey_progress(session, [1])[1]

    assert progress.total == 7
    assert progress.done == 3
    assert progress.pending == 2
    assert progress.failed == 2
    assert progress.total == progress.done + progress.failed + progress.pending
    assert not progress.finished


def test_a_survey_without_pending_rows_is_finished(session):
    add_summaries(session, 1, [200, 200, 200, 504, None])

    progress = survey_progress(session, [1])[1]

    assert progress.pending == 0
    assert progress.total == progress.done + progress.failed + progress.pending
    assert progress.finished


def test_a_survey_without_rows_is_not_finished(session):
    progress = survey_progress(session, [1])[1]

    assert (progress.total, progress.done, progress.failed, progress.pending) == (0, 0, 0, 0)
    assert not progress.finished
