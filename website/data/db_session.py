import sqlalchemy as sa
import sqlalchemy.orm as orm
from sqlalchemy.orm import Session


SqlAlchemyBase = orm.declarative_base()

__factory = None


def global_init(db_file: str):
    global __factory

    if __factory:
        return

    if not db_file or not db_file.strip():
        raise Exception("Необходимо указать файл базы данных.")

    conn_str = f'{db_file}'
    print(f"Подключение к базе данных по адресу {conn_str}")

    engine = sa.create_engine(conn_str, echo=False, pool_pre_ping=True)
    __factory = orm.sessionmaker(bind=engine)

    import website.data.__all_models

    # Alembic сам додумает
    SqlAlchemyBase.metadata.create_all(engine)  # убрать при деплое в сеть!!!


def create_session() -> Session:
    global __factory
    if __factory is None:
        raise Exception("База данных не инициализирована. Вызовите global_init()")
    return __factory()