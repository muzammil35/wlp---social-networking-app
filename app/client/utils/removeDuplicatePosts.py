def removeDuplicatePosts(posts):
    """
    Helper function to remove duplicate posts, based on their origin url
    """

    filteredPosts = []

    for post in posts:
        if post['origin'] not in [p['origin'] for p in filteredPosts]:
            filteredPosts.append(post)

    return filteredPosts
