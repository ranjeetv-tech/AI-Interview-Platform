from app.database.session import Base, engine
from app.models import *

def init_db():
    Base.metadata.create_all(bind=engine)
