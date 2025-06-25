from abc import ABCMeta

class PostInitMeta(ABCMeta):
    """Ensures method ._post_init_hook() is always called after the constructor.
    """
    def __call__(self, *args, **kwargs):
        instance = super().__call__(*args, **kwargs)
        instance._post_init_hook()
        #TODO: remove/improve this check at some point in the future
        if hasattr(instance, '_visited_portals'):
            assert len(instance._visited_portals) == 0
        return instance