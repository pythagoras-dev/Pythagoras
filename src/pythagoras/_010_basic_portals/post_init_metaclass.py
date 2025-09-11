from abc import ABCMeta

class PostInitMeta(ABCMeta):
    """Ensures method ._post_init_hook() is always called after the constructor.
    
    This metaclass automatically calls the `_post_init_hook()` method on instances
    after their construction is complete. This ensures that any post-initialization
    logic is consistently executed for all instances of classes using this metaclass.
    """
    
    def __call__(self, *args, **kwargs):
        """Create and initialize an instance, then call its post-init hook.

        This method overrides the default instance creation process to ensure
        that `_post_init_hook()` is called after the regular constructor.
        It also includes validation logic for portal-aware objects.

        Args:
            *args: Positional arguments to pass to the class constructor.
            **kwargs: Keyword arguments to pass to the class constructor.

        Returns:
            The fully initialized instance with post-init hook executed.

        Raises:
            AssertionError: If portal-aware object validation fails.
        """
        instance = super().__call__(*args, **kwargs)
        instance._post_init_hook()
        #TODO: remove/improve this check at some point in the future
        if hasattr(instance, '_visited_portals'):
            assert hasattr(instance, '_linked_portal_at_init')
            assert len(instance._visited_portals) - int(instance._linked_portal_at_init is not None) == 0
        return instance