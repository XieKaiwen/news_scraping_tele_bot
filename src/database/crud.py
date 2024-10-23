from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from .models import User, TopicPreference, UserQuery


# ---------------------- User CRUD ----------------------

# Create a new user
async def create_user(db: AsyncSession, tele_id: str, name: str) -> User:
    new_user = User(tele_id=tele_id, name=name)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

# Retrieve a user by id
async def get_user_by_id(db: AsyncSession, user_id: UUID) -> User:
    result = await db.execute(select(User).filter(User.id == user_id))
    return result.scalars().first()

# Retrieve a user by tele_id
async def get_user_by_tele_id(db: AsyncSession, tele_id: str) -> User:
    result = await db.execute(select(User).filter(User.tele_id == tele_id))
    return result.scalars().first()

# Update a user's name
async def update_user_name(db: AsyncSession, user_id: UUID, new_name: str) -> User:
    user = await get_user_by_id(db, user_id)
    if user:
        user.name = new_name
        await db.commit()
        await db.refresh(user)
    return user

# Delete a user
async def delete_user(db: AsyncSession, user_id: UUID) -> None:
    user = await get_user_by_id(db, user_id)
    if user:
        await db.delete(user)
        await db.commit()


# ------------------ TopicPreference CRUD ------------------

# Create a new topic preference
async def create_topic_preference(db: AsyncSession, user_id: UUID, topic_name: str, topic_hash: str, country_code: str) -> TopicPreference:
    new_topic = TopicPreference(user_id=user_id, topic_name=topic_name, topic_hash=topic_hash, country_code = country_code)
    db.add(new_topic)
    await db.commit()
    await db.refresh(new_topic)
    return new_topic

# Retrieve all topic preferences for a user
async def get_topic_preferences_by_user(db: AsyncSession, user_id: UUID) -> list[TopicPreference]:
    result = await db.execute(select(TopicPreference).filter(TopicPreference.user_id == user_id))
    return result.scalars().all()

# Delete a topic preference
async def delete_topic_preference(db: AsyncSession, topic_id: UUID) -> None:
    topic = await db.execute(select(TopicPreference).filter(TopicPreference.id == topic_id))
    topic = topic.scalars().first()
    if topic:
        await db.delete(topic)
        await db.commit()

async def is_topic_name_existing(db: AsyncSession, user_id: UUID, topic_name: str) -> bool:
    """
    Check if a specific topic name already exists for the given user.
    
    Args:
        db: The database session.
        user_id: The ID of the user to check topics for.
        topic_name: The name of the topic to check.
    
    Returns:
        bool: True if the topic name exists, False otherwise.
    """
    result = await db.execute(
        select(TopicPreference).filter(TopicPreference.user_id == user_id, TopicPreference.topic_name == topic_name)
    )
    topic_preference = result.scalars().first()
    return topic_preference is not None

# ------------------ UserQuery CRUD ------------------

# Create a new user query
async def create_user_query(db: AsyncSession, user_id: UUID, query: str) -> UserQuery:
    new_query = UserQuery(user_id=user_id, query=query)
    db.add(new_query)
    await db.commit()
    await db.refresh(new_query)
    return new_query

# Retrieve all queries for a user
async def get_user_queries_by_user(db: AsyncSession, user_id: UUID) -> list[UserQuery]:
    result = await db.execute(select(UserQuery).filter(UserQuery.user_id == user_id))
    return result.scalars().all()

# Delete a user query
async def delete_user_query(db: AsyncSession, query_id: UUID) -> None:
    query = await db.execute(select(UserQuery).filter(UserQuery.id == query_id))
    query = query.scalars().first()
    if query:
        await db.delete(query)
        await db.commit()
