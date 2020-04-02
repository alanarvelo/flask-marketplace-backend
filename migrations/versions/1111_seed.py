from alembic import op
from sqlalchemy import Table, MetaData
from seed_data import seed_venues, seed_artists

# revision identifiers, used by Alembic.
revision = '1111'
down_revision = '0000'
branch_labels = None
depends_on = None

def upgrade():
    # get metadata from current connection
    meta = MetaData(bind=op.get_bind())

    # pass in tuple with tables we want to reflect, otherwise whole database will get reflected
    meta.reflect(only=('venues', 'artists'))

    # define table representation
    Venue = Table('venues', meta)
    Artist = Table('artists', meta)

    # insert records
    op.bulk_insert(Venue, seed_venues)
    op.bulk_insert(Artist, seed_artists)

def downgrade():
    op.execute("DELETE FROM venues")
    op.execute("DELETE FROM artists")

