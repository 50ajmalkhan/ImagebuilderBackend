"""Initial migration

Revision ID: 001
Revises: 
Create Date: 2023-12-10 16:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create enum type
    op.execute("DROP TYPE IF EXISTS generationtype")
    op.execute("CREATE TYPE generationtype AS ENUM ('image', 'video')")

    # Create users table
    try:
        op.create_table(
            'users',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
            sa.Column('email', sa.String(255), nullable=False),
            sa.Column('full_name', sa.String(255), nullable=False),
            sa.Column('hashed_password', sa.String(255), nullable=False, comment='Bcrypt hashed password'),
            sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.CheckConstraint("length(hashed_password) > 0", name="users_hashed_password_check")
        )
        op.create_index('ix_users_email', 'users', ['email'], unique=True)
    except sa.exc.ProgrammingError as e:
        if 'already exists' not in str(e):
            raise e

    # Create generations table
    try:
        op.create_table(
            'generations',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
            sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
            sa.Column('prompt', sa.Text(), nullable=False),
            sa.Column('type', postgresql.ENUM('image', 'video', name='generationtype', create_type=False), nullable=False),
            sa.Column('url', sa.String(255), nullable=False),
            sa.Column('reference_image_url', sa.String(255), nullable=True),
            sa.Column('status', sa.String(50), nullable=False, server_default='success'),
            sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False)
        )
        op.create_index('ix_generations_user_id', 'generations', ['user_id'])
    except sa.exc.ProgrammingError as e:
        if 'already exists' not in str(e):
            raise e

    # Add trigger for updated_at
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)

    # Add triggers to both tables
    op.execute("""
        CREATE TRIGGER update_users_updated_at
            BEFORE UPDATE ON users
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
    """)

    op.execute("""
        CREATE TRIGGER update_generations_updated_at
            BEFORE UPDATE ON generations
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
    """)

def downgrade() -> None:
    # Drop triggers first
    op.execute("DROP TRIGGER IF EXISTS update_users_updated_at ON users")
    op.execute("DROP TRIGGER IF EXISTS update_generations_updated_at ON generations")
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column()")
    
    # Drop tables in reverse order
    op.drop_index('ix_generations_user_id')
    op.drop_table('generations')
    op.drop_index('ix_users_email')
    op.drop_table('users')
    op.execute("DROP TYPE IF EXISTS generationtype")