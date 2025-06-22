from abc import ABCMeta

class PostInitMeta(ABCMeta):
    """Ensures method ._post_init_hook() is always called after the constructor.
    """
    def __call__(self, *args, **kwargs):
        instance = super().__call__(*args, **kwargs)
        instance._post_init_hook()
        return instance