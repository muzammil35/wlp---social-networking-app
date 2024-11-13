from django.urls import reverse
from django.views import View
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
import requests
from ..forms.registerForm import RegisterForm
from django.contrib.auth import logout


class LogoutView(View):
    # Only used for logging out on swagger
    def get(self, request):
        return render(request, 'auth/logout.html')

    def post(self, request):
        # Clearing the session should also log the user out
        request.session.flush()

        return redirect('/login')


class RegisterView(View):
    def get(self, request):
        if request.user.is_authenticated:
            logout(request)
            return redirect('/profile')

        form = RegisterForm()

        return render(request, 'auth/register.html', {'form': form})

    def post(self, request):
        form = RegisterForm(request.POST)

        if form.is_valid():
            username = form.cleaned_data['username']
            displayName = form.cleaned_data['displayName']
            password = form.cleaned_data['password']
            github = form.cleaned_data['github']
            profileImage = form.cleaned_data['profileImage']

            response = requests.post(request.build_absolute_uri(
                reverse('api:author_list')), json={
                    "displayName": displayName,
                    "username": username,
                    "password": password,
                    "github": github if github else "",
                    "profile_image": profileImage if profileImage else ""
            },  headers={'referer': request.build_absolute_uri('/')})

            if response.status_code == 409:
                form.add_error(None, "Username already taken.")
            elif response.status_code == 201:
                user = authenticate(
                    request, username=username, password=password)
                if user is not None:
                    login(request, user)

                    return redirect('/profile')
        else:
            return render(request, 'auth/register.html', {'form': form})

        form.add_error(None, "Unable to register user. Please try again.")
        return render(request, 'auth/register.html', {'form': form})
