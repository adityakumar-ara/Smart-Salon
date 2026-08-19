from django.shortcuts import render


def csrf_failure(request, reason=""):
    """Render a friendly page whenever Django rejects a CSRF-protected request."""
    return render(request, "403_csrf.html", status=403)
