from abc import ABCMeta

class PostInitMeta(ABCMeta):
    """Ensures method .register_after_init() is always called after constructor.
    """
    def __call__(self, *args, **kwargs):
        instance = super().__call__(*args, **kwargs)
        instance.post_init_hook()
        return instance