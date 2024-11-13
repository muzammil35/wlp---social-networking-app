def sortPosts(posts):
    """
    Helper function to sort posts by published date
    """
    posts = sorted(posts, key=lambda x: x['published'], reverse=True)

    return posts
