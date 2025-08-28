from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session


def clear_all_tables(db_engine: Engine, model):
    with Session(db_engine) as db_session:
        tables = list(model.metadata.sorted_tables)
        tables.reverse()
        db_session.execute(text('SET FOREIGN_KEY_CHECKS = 0;'))
        for table in tables:
            db_session.execute(table.delete())
        db_session.execute(text('SET FOREIGN_KEY_CHECKS = 1;'))
        db_session.commit()
