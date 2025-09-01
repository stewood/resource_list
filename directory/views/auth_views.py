"""
Authentication views for the directory app.
"""

from django.contrib.auth import login
from django.contrib.auth.views import LoginView
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy


class CustomLoginView(LoginView):
    """Custom login view that redirects to the main page after login."""
    
    template_name = 'registration/login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        """Redirect to the main page after successful login."""
        return reverse_lazy('directory:public_home')
