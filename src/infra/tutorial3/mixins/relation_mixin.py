from sqlalchemy import MetaData
from sqlalchemy.ext.declarative import declarative_base

from src.infra.tutorial3.mixins.base_query import BaseQuery


Base = declarative_base()
naming_convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(column_0_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}
Base.metadata = MetaData(naming_convention=naming_convention)


class RelationMixin(Base, BaseQuery):
    __abstract__ = True

    """
    User.with_({
        'posts': {
            'comments': {
                'user': JOINED
            }
        }
    }).all()
    
    User.with_({
        User.posts: {
            Post.comments: {
                Comment.user: JOINED
            }
        }
    }).all()
    
    
    from sqlalchemy_mixins import JOINED, SUBQUERY
    Post.with_({
        'user': JOINED, # joinedload user
        'comments': (SUBQUERY, {  # load comments in separate query
            'user': JOINED  # but, in this separate query, join user
        })
    }).all()
    
    
    Comment.with_joined('user', 'post', 'post.comments').first()
    User.with_subquery('posts', 'posts.comments').all()
    
    Comment.with_joined('user','post')
    Comment.with_({'user': JOINED})
    
    comments = Comment.where(post___public=True, post___user___name__like='Bi%').all()

"""
