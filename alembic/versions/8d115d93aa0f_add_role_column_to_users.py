"""Add role column to users

Revision ID: 8d115d93aa0f
Revises: d6bc1e8c3b24
Create Date: 2024-12-15 14:15:18.919443+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8d115d93aa0f'
down_revision: Union[str, None] = 'd6bc1e8c3b24'
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