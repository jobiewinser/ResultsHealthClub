def superusers_hijack(*, hijacker=None, hijacked=None):
    """
    Superusers and staff members may hijack other users.

    A superuser may hijack any other user.
    A staff member may hijack any user, except another staff member or superuser.
    """
    if hijacker.is_superuser:
        return True
    return False

    # return hijacker.groups.filter(name = "staff").exists() and not (hijacked.groups.filter(name = "staff").exists() or hijacked.is_superuser)