class ToDictMixin:
    def to_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}
