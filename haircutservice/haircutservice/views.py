from django.shortcuts import render


def csrf_failure(request, reason=""):
    """Render a friendly page whenever Django rejects a CSRF-protected request."""
    return render(request, "403_csrf.html", status=403)


def information_page(request, title):
    """Render a simple branded information page."""
    return render(request, "information_page.html", {"title": title})


def help_page(request):
    """Show customers and shopkeepers how to use SnipAlert."""
    return render(request, "help_page.html")


def legal_page(request, document):
    """Render the applicable SnipAlert legal notice."""
    return render(request, "legal_page.html", {"document": document})
