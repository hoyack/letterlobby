"""Create global_return_addresses table

Revision ID: f15bcc3e4ba4
Revises: 238971668613
Create Date: 2024-12-16 04:01:36.241849+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f15bcc3e4ba4'
down_revision: Union[str, None] = '238971668613'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###
