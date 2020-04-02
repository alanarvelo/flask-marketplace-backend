from alembic import op
from sqlalchemy import Table, MetaData
from seed_data import seed_shows

# revision identifiers, used by Alembic.
revision = '3333'
down_revision = '2222'
branch_labels = None
depends_on = None

def upgrade():
    ## seeding shows data
    # get metadata from current connection
    meta = MetaData(bind=op.get_bind())
    # pass in tuple with tables we want to reflect, otherwise whole database will get reflected
    meta.reflect(only=('shows',))
    # define table representation
    Show = Table('shows', meta)
    # insert records
    op.bulk_insert(Show, seed_shows)

def downgrade():
    op.execute("DELETE FROM shows")

