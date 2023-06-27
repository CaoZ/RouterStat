from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.types import String

from config import Config

_db_url = 'mysql+mysqldb://{user}:{password}@{host}/{db}'.format_map(Config.DB)

engine = create_engine(_db_url, pool_recycle=3600)
Session = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    def __setattr__(self, key, value):
        # 当给 String 类型字段赋值时限制字符串的长度, 如 Column(String(20)) 中最长只能有 20 个字符.
        if isinstance(value, str):
            the_attribute = getattr(self.__class__, key, None)

            if isinstance(the_attribute, InstrumentedAttribute):
                # is a column
                if isinstance(the_attribute.property.columns[0].type, String):
                    max_length = the_attribute.property.columns[0].type.length
                    value = value[:max_length]

        super().__setattr__(key, value)

    @property
    def session(self) -> Session:
        """
        Get combined sqlalchemy session.
        """
        return Session.object_session(self)

    @classmethod
    def get(cls, object_id, session):
        """
        Get object by object id, if not find, return None.
        """
        the_object = session.query(cls).filter(
            cls.id == object_id
        ).first()

        return the_object

    @classmethod
    def get_property(cls, object_id, property_column, session):
        value = session.query(property_column).filter(
            cls.id == object_id
        ).scalar()

        return value

    @classmethod
    def exists(cls, session: Session, *filters):
        return session.query(
            session.query(cls).filter(*filters).exists()
        ).scalar()

    def to_dict(self, **kwargs) -> dict:
        """
        将一个 SQLAlchemy 的对象 (row, declarative_base) 转为 dict.
        如果 kwargs 有 columns, 则 columns 是所有需要的项; 若有 excluded, 则 excluded 是要排除的项. 二者不可并存.
        """
        d = {}

        columns = kwargs.get('columns')

        if columns:
            columns = [x.key for x in columns]

        else:
            # 不需要的项
            excluded = kwargs.get('excluded')
            columns = set(x.name for x in self.__table__.columns)

            if excluded:
                excluded = set(x.key for x in excluded)
                columns -= excluded

        for column in columns:
            value = getattr(self, column)
            d[column] = value

        return d

    @classmethod
    def print_create_table_sql(cls):
        """
        打印表的创建语句, 以便手动创建等用途
        """
        mock_engine = create_engine(_db_url, strategy='mock', executor=dump)

        print('#### Create table SQL for model {}: ####'.format(cls))
        cls.__table__.create(mock_engine)
        print('#' * 20)

    @classmethod
    def create_table_if_not_exist(cls):
        """
        如果需要的表不存在, 创建它
        """
        cls.__table__.create(engine, checkfirst=True)


def dump(sql, *args, **kwargs):
    print(sql.compile(dialect=engine.dialect))
