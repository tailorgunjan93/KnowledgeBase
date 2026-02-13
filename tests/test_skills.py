"""Tests for Skills Repository."""
import pytest
from data.repositories.settings_repository import SkillRepository
from domain.models import Skill

def test_create_skill(clean_db):
    """Test creating a new skill."""
    repo = SkillRepository()
    user_id = 1 # Assuming seeded or handled by valid FK if strict (sqlite FKs are on)
    # Ensure user exists for FK constraint if active (conftest clean_db deletes all)
    # We need to create a user first
    from data.repositories.user_repository import UserRepository
    from domain.models import User
    
    u_repo = UserRepository()
    u = User(username="skilluser", email="s@s.com", password_hash="hash")
    user_id = u_repo.create(u)

    skill = Skill(
        user_id=user_id,
        name="Test Skill",
        description="A test skill",
        prompt_template="Be a tester."
    )
    
    skill_id = repo.create(skill)
    assert skill_id is not None
    
    # Verify
    retrieved = repo.get_user_skills(user_id)
    assert len(retrieved) == 1
    assert retrieved[0].name == "Test Skill"

def test_delete_skill(clean_db):
    """Test deleting a skill."""
    repo = SkillRepository()
    # Create user
    from data.repositories.user_repository import UserRepository
    from domain.models import User
    u_repo = UserRepository()
    u = User(username="deluser", email="d@d.com", password_hash="hash")
    user_id = u_repo.create(u)
    
    skill = Skill(user_id=user_id, name="To Delete", description="desc", prompt_template="tmpl")
    sid = repo.create(skill)
    
    repo.delete(sid)
    
    retrieved = repo.get_user_skills(user_id)
    assert len(retrieved) == 0
