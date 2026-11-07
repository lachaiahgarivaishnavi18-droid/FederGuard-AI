"""Initial coordinator schema. Raw transactions live outside this database."""
from alembic import op
from backend.app.core import Base
revision='0001'
down_revision=None
branch_labels=None
depends_on=None
def upgrade(): Base.metadata.create_all(bind=op.get_bind())
def downgrade(): Base.metadata.drop_all(bind=op.get_bind())
